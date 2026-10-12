"""Comparação auditiva local; usa um único processo de voz e WAVs temporários."""
import json
import shutil
import time
import uuid
from pathlib import Path
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                              QComboBox, QPlainTextEdit, QPushButton)
from .narration import prepare_spoken_text
from .text_cleaning import clean_text
from .workers import ProcessChannel, voice_worker


class PronunciationDialog(QDialog):
    def __init__(self, parent, model_dir, folder, voice, device, volume):
        super().__init__(parent)
        self.setWindowTitle('Teste de pronúncia — comparação A/B')
        self.resize(700, 640)
        self.model_dir, self.folder = model_dir, Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.channel = None
        self.ready = self.busy = False
        self.queue, self.paths = [], {}
        self.last_activity = time.monotonic()
        layout = QVBoxLayout(self)
        label = QLabel('Compare a leitura original com a preparada. Você pode editar a proposta de fala.\n'
                       'As alterações deste teste não mudam o dicionário nem o PDF.')
        label.setWordWrap(True)
        layout.addWidget(label)
        self.samples = QComboBox()
        self.samples.addItem('Texto livre', None)
        data_path = Path(__file__).with_name('data') / 'testes_pronuncia.json'
        try:
            cases = json.loads(data_path.read_text('utf-8'))['cases']
        except (OSError, ValueError, KeyError):
            cases = []
        for case in cases:
            self.samples.addItem(f"{case['group']} — {case['text'][:65]}", case)
        layout.addWidget(self.samples)
        self.goal = QLabel('Use até 1.000 caracteres em cada campo.')
        self.goal.setWordWrap(True)
        layout.addWidget(self.goal)
        row = QHBoxLayout()
        self.voice = QComboBox()
        for title, code in [('Dora', 'pf_dora'), ('Alex', 'pm_alex'), ('Santa', 'pm_santa')]:
            self.voice.addItem(title, code)
        self.voice.setCurrentIndex(max(0, self.voice.findData(voice)))
        self.mode = QComboBox()
        for title, kind in [('Comum', 'common'), ('Texto em livro técnico', 'prose'), ('Código', 'code'), ('Título', 'heading')]:
            self.mode.addItem(title, kind)
        row.addWidget(QLabel('Voz'))
        row.addWidget(self.voice)
        row.addWidget(QLabel('Tratamento'))
        row.addWidget(self.mode)
        layout.addLayout(row)
        layout.addWidget(QLabel('A — texto original'))
        self.original = QPlainTextEdit()
        layout.addWidget(self.original)
        layout.addWidget(QLabel('B — texto preparado (editável para testar uma correção)'))
        self.prepared = QPlainTextEdit()
        layout.addWidget(self.prepared)
        row = QHBoxLayout()
        self.generate = QPushButton('Preparar comparação')
        self.play_a = QPushButton('Ouvir original')
        self.play_b = QPushButton('Ouvir preparado')
        self.stop_button = QPushButton('Parar áudio')
        for button in (self.generate, self.play_a, self.play_b, self.stop_button):
            row.addWidget(button)
        layout.addLayout(row)
        self.status = QLabel('A comparação será feita na velocidade 1×.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        close = QPushButton('Fechar teste')
        layout.addWidget(close)
        self.player = QMediaPlayer(self)
        self.output = QAudioOutput(self)
        self.output.setDevice(device)
        self.output.setVolume(volume)
        self.player.setAudioOutput(self.output)
        self.player.errorOccurred.connect(lambda *_: self.status.setText('Falha ao reproduzir: ' + self.player.errorString()))
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.poll)
        self.timer.start()
        self.generate.clicked.connect(self.start_comparison)
        self.play_a.clicked.connect(lambda: self.play('original'))
        self.play_b.clicked.connect(lambda: self.play('prepared'))
        self.stop_button.clicked.connect(self.player.stop)
        close.clicked.connect(self.reject)
        self.samples.currentIndexChanged.connect(self.select_sample)
        self.original.textChanged.connect(self.preview)
        self.mode.currentIndexChanged.connect(self.preview)
        self.prepared.textChanged.connect(self.invalidate)
        self.voice.currentIndexChanged.connect(self.invalidate)
        self.invalidate()
        self.samples.setCurrentIndex(1 if cases else 0)

    def select_sample(self, *_):
        case = self.samples.currentData()
        if case:
            self.mode.setCurrentIndex(max(0, self.mode.findData(case['kind'])))
            self.original.setPlainText(case['text'])
            self.goal.setText(case['goal'] + '\nReferência: ' + case['reference'])

    def invalidate(self, *_):
        self.player.stop()
        self.play_a.setEnabled(False)
        self.play_b.setEnabled(False)

    def preview(self, *_):
        text = self.original.toPlainText()
        self.prepared.setPlainText(prepare_spoken_text(text, self.mode.currentData()) if len(text) <= 1000 else '')
        self.invalidate()

    def set_busy(self, busy):
        self.busy = busy
        for widget in (self.samples, self.voice, self.mode, self.original, self.prepared, self.generate):
            widget.setEnabled(not busy)

    def start_comparison(self):
        a, b = clean_text(self.original.toPlainText()).strip(), clean_text(self.prepared.toPlainText()).strip()
        if not all(0 < len(t) <= 1000 and any(c.isalnum() for c in t) for t in (a, b)):
            self.status.setText('Preencha os dois campos com texto de até 1.000 caracteres.')
            return
        if not self.model_dir:
            self.status.setText('Modelos não encontrados. Selecione a pasta de modelos no leitor.')
            return
        self.invalidate()
        self.player.setSource(QUrl())
        for path in self.paths.values():
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        self.paths = {}
        self.queue = [('original', a), ('prepared', b)]
        self.set_busy(True)
        self.status.setText('Preparando a comparação na CPU…')
        try:
            if self.channel is None:
                self.ready = False
                self.channel = ProcessChannel(voice_worker, self.model_dir)
            self.last_activity = time.monotonic()
            if self.ready:
                self.send_next()
        except Exception as error:
            self.fail(str(error))

    def send_next(self):
        name, text = self.queue.pop(0)
        path = self.folder / (name + '_' + uuid.uuid4().hex + '.wav')
        self.paths[name] = path
        # Ambas as versões seguem o mesmo caminho acústico; B já foi preparada.
        self.channel.send({'token': 'pronunciation-test', 'index': name, 'text': text,
                           'path': str(path), 'voice': self.voice.currentData(),
                           'kind': 'prose', 'prepared': True})
        self.last_activity = time.monotonic()

    def poll(self):
        if not self.channel:
            return
        for message in list(self.channel.poll()):
            self.last_activity = time.monotonic()
            if message['kind'] == 'ready':
                self.ready = True
                if self.busy:
                    self.send_next()
            elif message['kind'] == 'audio':
                if self.queue:
                    self.send_next()
                else:
                    self.set_busy(False)
                    self.play_a.setEnabled(True)
                    self.play_b.setEnabled(True)
                    self.status.setText('Compare A e B. Uma proposta de escrita ainda precisa de avaliação auditiva.')
            elif message['kind'] == 'error':
                self.fail(message['error'])
                return
        if self.channel and (not self.channel.process.is_alive() or
                             (self.busy and time.monotonic() - self.last_activity > 300)):
            self.fail('O processo de voz parou ou excedeu cinco minutos sem resposta.')

    def fail(self, message):
        if self.channel:
            self.channel.stop()
        self.channel = None
        self.ready = False
        self.queue = []
        self.set_busy(False)
        self.invalidate()
        self.status.setText('Não foi possível comparar: ' + message)

    def play(self, name):
        if name in self.paths:
            self.player.setSource(QUrl.fromLocalFile(str(self.paths[name])))
            self.player.play()

    def done(self, result):
        self.timer.stop()
        self.player.stop()
        self.player.setSource(QUrl())
        if self.channel:
            self.channel.stop()
            self.channel = None
        shutil.rmtree(self.folder, ignore_errors=True)
        super().done(result)
