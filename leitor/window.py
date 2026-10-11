import json
import logging
from pathlib import Path
import shutil
import time
import uuid

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSplitter, QListWidget, QListWidgetItem, QSpinBox, QDoubleSpinBox,
    QProgressBar, QSlider, QCheckBox, QFileDialog, QMessageBox, QInputDialog,
    QComboBox, QLineEdit, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QDialog, QFormLayout, QSizePolicy)

from .domain import buffered_seconds, next_missing, remap_progress
from . import VERSION
from .speech import AUDIO_REVISION
from .storage import Store, clean_sessions
from .viewer import PDFView
from .workers import ProcessChannel, pdf_worker, voice_worker

TARGET = 30.0
MAX_AHEAD = 90.0
MAX_BYTES = 500 * 1024 * 1024
WORKER_TIMEOUT = 300.0  # Cinco minutos sem retorno/progresso.


class MainWindow(QMainWindow):
    def __init__(self, data_root):
        super().__init__()
        self.root = Path(data_root)
        self.store = Store(self.root)
        self.audio_root = self.root / "audio"
        clean_sessions(self.audio_root)
        self.book = None
        self.pdf = self.tts = None
        self.tts_ready = False
        self.pending_audio = None
        self.pdf_activity = self.tts_activity = time.monotonic()
        self.page_segments = {}
        self.saved_snapshot = None
        self.metrics = []
        self.cache = {}
        self.garbage = set()
        self.retired_folders = set()
        self.folder = None
        self.token = 0
        self.index = 0
        self.page = 0
        self.offset = 0
        self.completed = False
        self.desired = False
        self.phase = "idle"
        self.loaded_index = None
        self.expected_source = ""
        self.seek_started = 0
        self.render_id = 0
        self.render_pending = None
        self.render_busy = False
        self.shown_page = None
        self.importing = False
        self.closed = False
        self.loading_guard = False
        self.audio = QAudioOutput(self)
        self.audio.setVolume(float(self.store.get("volume", "80")) / 100)
        self.devices = QMediaDevices(self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio)
        if hasattr(self.player, "setPitchCompensation"):
            self.player.setPitchCompensation(True)
        self.build_ui()
        self.devices.audioOutputsChanged.connect(self.refresh_outputs)
        self.refresh_outputs()
        self.player.mediaStatusChanged.connect(self.media_status)
        self.player.errorOccurred.connect(self.audio_error)
        self.player.positionChanged.connect(self.position_changed)
        self.player.seekableChanged.connect(lambda _: self.start_loaded())
        self.player.playbackStateChanged.connect(self.play_state)
        self.poller = QTimer(self)
        self.poller.timeout.connect(self.tick)
        self.poller.start(100)
        self.saver = QTimer(self)
        self.saver.timeout.connect(self.save_progress)
        self.saver.start(5000)
        self.refresh_recent()

    def build_ui(self):
        self.setWindowTitle(f"PDF Voz • Leitor {VERSION}")
        self.resize(1160, 800)
        self.setMinimumSize(850, 600)
        from .theme import STYLE
        self.setStyleSheet(STYLE)
        outer = QWidget()
        self.setCentralWidget(outer)
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        top = QHBoxLayout()
        self.sidebar_button = QPushButton("Painel lateral")
        self.sidebar_button.setCheckable(True)
        self.sidebar_button.setChecked(True)
        self.sidebar_button.setToolTip("Mostrar ou recolher Trechos, Sumário e Recentes (Ctrl+B)")
        self.sidebar_button.toggled.connect(self.toggle_sidebar)
        top.addWidget(self.sidebar_button)
        open_button = QPushButton("Abrir PDF")
        open_button.clicked.connect(lambda: self.open_dialog())
        self.title_label = QLabel("Escolha um livro para começar")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(40)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.title_label.setObjectName("bookTitle")
        top.addWidget(open_button)
        top.addWidget(self.title_label, 1)
        self.settings_button = QPushButton("Configurações")
        self.settings_button.clicked.connect(self.open_preferences)
        top.addWidget(self.settings_button)
        layout.addLayout(top)
        split = self.split = QSplitter()
        split.setChildrenCollapsible(False)
        tabs = self.sidebar = QTabWidget()
        self.lines = QListWidget()
        self.lines.setWordWrap(True)
        self.lines.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.lines.itemClicked.connect(lambda item: self.navigate(item.data(Qt.ItemDataRole.UserRole), True))
        self.chapters = QTreeWidget()
        self.chapters.setHeaderHidden(True)
        self.chapters.itemClicked.connect(self.chapter_clicked)
        self.recent = QListWidget()
        self.recent.itemDoubleClicked.connect(lambda item: self.open_book(item.data(Qt.ItemDataRole.UserRole)))
        tabs.addTab(self.lines, "Trechos")
        tabs.addTab(self.chapters, "Sumário")
        tabs.addTab(self.recent, "Recentes")
        tabs.setMinimumWidth(230)
        split.addWidget(tabs)
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        navigation = QHBoxLayout()
        previous = QPushButton("‹ Página")
        previous.clicked.connect(lambda: self.show_page(self.page - 1))
        following = QPushButton("Página ›")
        following.clicked.connect(lambda: self.show_page(self.page + 1))
        self.page_box = QSpinBox()
        self.page_box.setRange(1, 1)
        self.page_box.editingFinished.connect(lambda: self.show_page(self.page_box.value() - 1))
        self.page_total = QLabel("/ 0")
        self.zoom = QDoubleSpinBox()
        self.zoom.setRange(.5, 2.5)
        self.zoom.setSingleStep(.1)
        self.zoom.setValue(1.0)
        self.zoom.setSuffix(" ×")
        self.zoom.valueChanged.connect(self.zoom_changed)
        self.follow = QCheckBox("Acompanhar leitura")
        self.follow.setChecked(True)
        for widget in (previous, self.page_box, self.page_total, following, QLabel("Zoom"), self.zoom, self.follow):
            navigation.addWidget(widget)
        navigation.addStretch()
        layout.addLayout(navigation)
        self.viewer = PDFView()
        self.viewer.chosen.connect(lambda index: self.navigate(index, True))
        center_layout.addWidget(self.viewer, 1)
        split.addWidget(center)
        split.setSizes([270, 860])
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        self.sidebar_sizes = [270, 860]
        layout.addWidget(split, 1)
        controls = QHBoxLayout()
        back = QPushButton("‹ Trecho")
        back.clicked.connect(lambda: self.navigate(self.index - 1, self.desired))
        self.play_button = QPushButton("Reproduzir")
        self.play_button.setObjectName("primary")
        self.play_button.setMinimumWidth(118)
        self.play_button.clicked.connect(self.toggle_play)
        ahead = QPushButton("Trecho ›")
        ahead.clicked.connect(lambda: self.navigate(self.index + 1, self.desired))
        self.rate = QDoubleSpinBox()
        self.rate.setRange(.75, 2.0)
        self.rate.setSingleStep(.25)
        self.rate.setValue(1)
        self.rate.setSuffix(" ×")
        self.rate.valueChanged.connect(self.change_rate)
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(round(self.audio.volume() * 100))
        self.volume.setMaximumWidth(100)
        self.volume_label = QLabel(f"{self.volume.value()}%")
        self.volume.valueChanged.connect(self.change_volume)
        for widget in (back, self.play_button, ahead, QLabel("Velocidade"), self.rate,
                       QLabel("Volume"), self.volume, self.volume_label):
            controls.addWidget(widget)
        controls.addStretch()
        clear = QPushButton("Limpar áudios")
        clear.clicked.connect(self.clear_audio)

        layout.addLayout(controls)
        self.preferences = QDialog(self)
        self.preferences.setWindowTitle("Configurações de leitura")
        self.preferences.setMinimumWidth(540)
        preferences_layout = QVBoxLayout(self.preferences)
        preferences_layout.setContentsMargins(18, 18, 18, 18)
        preferences_layout.setSpacing(14)
        description = QLabel("As alterações são aplicadas ao selecionar cada opção.")
        description.setWordWrap(True)
        preferences_layout.addWidget(description)
        form = QFormLayout()
        form.setSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        preferences_layout.addLayout(form)
        sound_row = QHBoxLayout()
        self.output_choice = QComboBox()
        self.output_choice.setMinimumWidth(180)
        self.output_choice.setMaximumWidth(420)
        self.output_choice.currentIndexChanged.connect(self.change_output)
        refresh = QPushButton("Atualizar saídas")
        refresh.clicked.connect(self.refresh_outputs)
        settings = QPushButton("Som do Windows")
        settings.clicked.connect(self.open_sound_settings)
        form.addRow("Saída de áudio", self.output_choice)
        sound_row.addWidget(refresh)
        sound_row.addWidget(settings)
        preferences_layout.addLayout(sound_row)
        self.voice_choice = QComboBox()
        for label, code in (("Dora · português", "pf_dora"), ("Alex · português", "pm_alex"),
                            ("Santa · português", "pm_santa")):
            self.voice_choice.addItem(label, code)
        self.voice_choice.setCurrentIndex(max(0, self.voice_choice.findData(self.store.get("voice", "pf_dora"))))
        self.voice_choice.currentIndexChanged.connect(self.change_voice)
        self.reserve = QComboBox()
        for seconds in (15, 30, 60):
            self.reserve.addItem(f"{seconds} s", seconds)
        self.reserve.setCurrentIndex(max(0, self.reserve.findData(int(self.store.get("reserve", "30")))))
        self.reserve.setToolTip("Reserva de fala pronta, não tempo de espera. Menor reserva pode causar mais pausas.")
        self.reserve.currentIndexChanged.connect(self.change_reserve)
        self.narration_mode = QComboBox()
        for label, code in (("Automático", "auto"), ("Prosa", "prose"), ("Código", "code")):
            self.narration_mode.addItem(label, code)
        self.narration_mode.setToolTip("Tratamento da fala deste livro. Automático usa o tipo extraído do PDF.")
        self.narration_mode.currentIndexChanged.connect(self.change_narration_mode)
        self.start_now = QPushButton("Ouvir o que já está pronto")
        self.start_now.setEnabled(False)
        self.start_now.clicked.connect(self.play_ready)
        form.addRow("Voz", self.voice_choice)
        form.addRow("Reserva inicial", self.reserve)
        form.addRow("Tratamento da leitura", self.narration_mode)
        preferences_layout.addWidget(clear)
        done = QPushButton("Fechar configurações")
        done.clicked.connect(self.preferences.close)
        preferences_layout.addWidget(done)
        status_row = QHBoxLayout()
        self.status = QLabel("Pronto. A voz é preparada localmente; não é necessário enviar seu livro.")
        self.status.setWordWrap(True)
        self.status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.status.setObjectName("status")
        self.buffer_label = QLabel("Nenhum áudio preparado")
        self.buffer_label.setObjectName("status")
        self.buffer = QProgressBar()
        self.buffer.setTextVisible(False)
        self.buffer.setFixedHeight(5)
        self.buffer.setAccessibleName("Reserva de áudio")
        self.buffer.setRange(0, 60)
        self.buffer.setValue(0)
        status_row.addWidget(self.status, 1)
        status_row.addWidget(self.buffer_label)
        status_row.addWidget(self.start_now)
        layout.addLayout(status_row)
        layout.addWidget(self.buffer)
        menu = self.menuBar().addMenu("Arquivo")
        action = QAction("Abrir PDF…", self)
        action.setShortcut(QKeySequence.StandardKey.Open)
        action.triggered.connect(self.open_dialog)
        menu.addAction(action)
        close_action = QAction("Fechar livro", self)
        close_action.triggered.connect(self.close_book)
        menu.addAction(close_action)
        menu.addSeparator()
        logs = QAction("Abrir pasta de dados e diagnóstico", self)
        logs.triggered.connect(self.open_data)
        menu.addAction(logs)
        forget = QAction("Remover livro atual do histórico", self)
        forget.triggered.connect(self.forget_book)
        menu.addAction(forget)
        diagnostic = QAction("Gerar diagnóstico atual", self)
        diagnostic.triggered.connect(self.write_diagnostic)
        menu.addAction(diagnostic)
        models = QAction("Selecionar pasta dos modelos…", self)
        models.triggered.connect(self.select_models)
        menu.addAction(models)
        view_menu = self.menuBar().addMenu("Exibir")
        self.sidebar_action = QAction("Painel lateral", self)
        self.sidebar_action.setCheckable(True)
        self.sidebar_action.setChecked(True)
        self.sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        self.sidebar_action.toggled.connect(self.sidebar_button.setChecked)
        self.sidebar_button.toggled.connect(self.sidebar_action.setChecked)
        view_menu.addAction(self.sidebar_action)
        config_action = QAction("Configurações…", self)
        config_action.triggered.connect(self.open_preferences)
        view_menu.addAction(config_action)
        self.sidebar_button.setChecked(self.store.get("sidebar_visible", "1") == "1")
        QShortcut(QKeySequence("Space"), self, activated=self.toggle_play)
        QShortcut(QKeySequence("PgDown"), self, activated=lambda: self.show_page(self.page + 1))
        QShortcut(QKeySequence("PgUp"), self, activated=lambda: self.show_page(self.page - 1))

    def toggle_sidebar(self, visible):
        if not visible:
            self.sidebar_sizes = self.split.sizes()
        self.sidebar.setVisible(visible)
        if visible:
            self.split.setSizes(self.sidebar_sizes)
        self.store.set("sidebar_visible", "1" if visible else "0")

    def open_preferences(self):
        self.preferences.show()
        self.preferences.raise_()
        self.preferences.activateWindow()

    def audio_revision(self):
        return AUDIO_REVISION + ':' + (self.narration_mode.currentData() or 'auto')

    def change_narration_mode(self, _):
        if self.book:
            self.store.set('narration_mode:' + self.book['hash'], self.narration_mode.currentData())
            self.change_voice(0)
            self.status.setText('Tratamento da fala alterado. O trecho atual será preparado novamente.')

    def forget_book(self):
        if not self.book:
            return
        key = self.book['hash']
        self.close_book()
        self.store.forget(key)
        self.refresh_recent()
        self.status.setText('Livro removido do histórico. O PDF original foi mantido.')

    def write_diagnostic(self):
        from .diagnostics import diagnostics
        folder = self.root / 'logs'
        folder.mkdir(exist_ok=True)
        report = diagnostics()
        report['ultimos_trechos'] = self.metrics[-20:]
        report['voz'] = self.voice_choice.currentData()
        report['tratamento'] = self.narration_mode.currentData()
        report['velocidade'] = self.rate.value()
        path = folder / 'diagnostico_atual.json'
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        self.status.setText('Diagnóstico salvo em: ' + str(path))

    def change_volume(self, value):
        self.audio.setVolume(value / 100)
        self.volume_label.setText(f"{value}%")
        self.store.set("volume", value)

    def refresh_outputs(self):
        wanted = self.store.get("audio_output")
        outputs = QMediaDevices.audioOutputs()
        default = QMediaDevices.defaultAudioOutput()
        self.output_choice.blockSignals(True)
        self.output_choice.clear()
        self.output_choice.addItem("Padrão do sistema: " + (default.description() or "nenhum dispositivo"), "")
        for device in outputs:
            self.output_choice.addItem(device.description(), bytes(device.id()).hex())
        chosen = self.output_choice.findData(wanted)
        if wanted and chosen < 0:
            self.output_choice.addItem("Saída desconectada · usando padrão", wanted)
            chosen = self.output_choice.count() - 1
        self.output_choice.setCurrentIndex(max(0, chosen))
        self.output_choice.blockSignals(False)
        self.apply_output()

    def apply_output(self):
        wanted = self.output_choice.currentData()
        device = next((d for d in QMediaDevices.audioOutputs() if bytes(d.id()).hex() == wanted),
                      QMediaDevices.defaultAudioOutput())
        if self.audio.device().id() != device.id():
            self.audio.setDevice(device)
        self.output_choice.setToolTip("Saída em uso: " + (device.description() or "nenhuma"))

    def change_output(self, _):
        self.store.set("audio_output", self.output_choice.currentData() or "")
        self.apply_output()

    def open_sound_settings(self):
        import sys
        from PySide6.QtGui import QDesktopServices
        if sys.platform == "win32":
            QDesktopServices.openUrl(QUrl("ms-settings:sound"))
        else:
            QMessageBox.information(self, "Som", "Abra as configurações de som do seu sistema.")

    def change_reserve(self, _):
        self.store.set("reserve", self.reserve.currentData())
        self.drive()

    def play_ready(self):
        if self.desired and self.phase == "buffering" and self.index in self.cache:
            self.load_current()

    def change_voice(self, _):
        self.store.set("voice", self.voice_choice.currentData())
        if not self.book:
            return
        resume = self.desired
        self.desired = False
        self.unload_player()
        self.token += 1
        # Keep the loaded model; a pending old job will be discarded by its token.
        for item in self.cache.values():
            self.garbage.add(item["path"])
        self.cache.clear()
        self.collect_garbage()
        self.offset = 0
        self.phase = "paused"
        self.save_progress()
        self.status.setText("Voz alterada. O trecho atual será preparado desde o início.")
        self.play_button.setText("Reproduzir")
        if resume:
            self.toggle_play()

    def open_data(self):
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.root)))

    def refresh_recent(self):
        self.recent.clear()
        for path, title in self.store.history():
            item = QListWidgetItem(title)
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.recent.addItem(item)

    def open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir livro", "", "PDF (*.pdf)")
        if path:
            self.open_book(path)

    def open_book(self, path, password=""):
        self.close_book()
        if not Path(path).is_file():
            QMessageBox.warning(self, "Arquivo não encontrado", "Selecione novamente o PDF na pasta em que ele está salvo.")
            return
        self.opening_path = str(path)
        self.importing = True
        self.status.setText("Preparando livro…")
        self.pdf_activity = time.monotonic()
        self.pdf = ProcessChannel(pdf_worker)
        self.pdf.send({"kind": "open", "path": str(path), "password": password})

    def book_ready(self, book):
        self.importing = False
        self.narration_mode.blockSignals(True)
        self.narration_mode.setCurrentIndex(max(0, self.narration_mode.findData(
            self.store.get('narration_mode:' + book['hash'], 'auto'))))
        self.narration_mode.blockSignals(False)
        self.saved_snapshot = None
        saved = remap_progress(self.store.load(book["hash"]), self.store.book_payload(book["hash"]), book)
        if saved and self.store.get("audio_revision:" + book["hash"]) != self.audio_revision():
            saved = dict(saved, offset=0)
        self.book = book
        self.page_segments = {}
        for segment in book['segments']:
            for page in {region['page'] for region in segment['regions']}:
                self.page_segments.setdefault(page, []).append(segment)
        self.store.put_book(book)
        self.refresh_recent()
        self.folder = self.audio_root / ("session_" + uuid.uuid4().hex)
        self.folder.mkdir(parents=True)
        self.page_box.setMaximum(max(1, len(book["pages"])))
        self.page_total.setText(f"/ {len(book['pages'])}")
        self.title_label.setText(book["title"])
        self.chapters.clear()
        stack = []
        for chapter in book["toc"]:
            while stack and stack[-1][0] >= chapter["level"]:
                stack.pop()
            item = QTreeWidgetItem([chapter["title"]])
            item.setData(0, Qt.ItemDataRole.UserRole, chapter["page"])
            if stack:
                stack[-1][1].addChild(item)
            else:
                self.chapters.addTopLevelItem(item)
            stack.append((chapter["level"], item))
        self.index = min(saved["index"], len(book["segments"]) - 1) if saved and book["segments"] else 0
        self.offset = max(0, saved["offset"]) if saved and saved["voice"] == self.voice_choice.currentData() else 0
        self.completed = bool(saved["completed"]) if saved else False
        self.rate.setValue(saved["rate"] if saved else 1)
        self.zoom.setValue(saved["zoom"] if saved else 1)
        target = saved["page"] if saved else (book["segments"][0]["page"] if book["segments"] else 0)
        self.show_page(min(target, max(0, len(book["pages"]) - 1)))
        self.refresh_selection()
        self.phase = "paused"
        if not book["segments"]:
            self.status.setText("Este PDF não tem texto extraível. OCR não está disponível nesta versão.")
        elif saved:
            self.status.setText("Ponto salvo recuperado. Clique em Reproduzir para preparar o áudio.")
        else:
            self.status.setText("Livro pronto. Clique em uma frase ou em Reproduzir.")
        self.save_progress()

    def chapter_clicked(self, item, column):
        page = item.data(0, Qt.ItemDataRole.UserRole)
        self.show_page(page)
        if self.book:
            index = next((s["id"] for s in self.book["segments"] if s["page"] >= page), None)
            if index is not None:
                self.navigate(index, False)

    def show_page(self, page):
        if not self.book or not 0 <= page < len(self.book["pages"]):
            return
        self.page = page
        self.page_box.setValue(page + 1)
        self.render_id += 1
        self.render_pending = {"kind": "render", "page": page, "request": self.render_id,
                               "scale": max(1.3, min(3.0, self.zoom.value() * 1.4))}
        self.viewer.clear_page()
        self.shown_page = None
        self.lines.clear()
        for segment in self.page_segments.get(page, []):
            if any(r["page"] == page for r in segment["regions"]):
                text = segment["text"]
                item = QListWidgetItem(text[:140] + ("…" if len(text) > 140 else ""))
                item.setToolTip(text)
                item.setData(Qt.ItemDataRole.UserRole, segment["id"])
                self.lines.addItem(item)
        self.refresh_selection()
        self.request_render()

    def request_render(self):
        if self.pdf and self.render_pending and not self.render_busy:
            self.pdf_activity = time.monotonic()
            self.pdf.send(self.render_pending)
            self.render_pending = None
            self.render_busy = True

    def page_ready(self, message):
        self.render_busy = False
        if self.book and message["request"] == self.render_id:
            regions = [(s["id"], r["display_box"]) for s in self.page_segments.get(message["page"], [])
                       for r in s["regions"] if r["page"] == message["page"]]
            self.viewer.show_page(message["png"], message["scale"], regions)
            self.viewer.set_zoom(self.zoom.value())
            self.shown_page = message["page"]
            self.highlight()
        self.request_render()

    def zoom_changed(self, value):
        self.viewer.set_zoom(value)
        if self.book:
            self.show_page(self.page)

    def refresh_selection(self):
        if not self.book or not self.book["segments"]:
            return
        for i in range(self.lines.count()):
            item = self.lines.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == self.index:
                self.lines.setCurrentItem(item)
                break
        self.highlight()

    def highlight(self):
        self.viewer.highlight(self.index, self.phase == "playing", self.follow.isChecked())

    def select_models(self):
        path = QFileDialog.getExistingDirectory(self, "Selecione a pasta models do teste anterior")
        if path:
            if not self.valid_models(path):
                QMessageBox.warning(self, "Modelos não encontrados", "A pasta precisa conter kokoro-v1.0.onnx e voices-v1.0.bin.")
                return None
            self.store.set("models", path)
            return path
        return None

    @staticmethod
    def valid_models(path):
        return all((Path(path) / name).is_file() for name in ("kokoro-v1.0.onnx", "voices-v1.0.bin"))

    def ensure_voice(self):
        if self.tts:
            return True
        candidates = [self.store.get("models"), str(Path(__file__).resolve().parents[1] / "models")]
        path = next((p for p in candidates if p and self.valid_models(p)), None)
        if not path:
            QMessageBox.information(self, "Reaproveitar os modelos", "Escolha a pasta models usada no teste anterior. Não é necessário baixá-la novamente.")
            path = self.select_models()
        if not path:
            return False
        self.tts_ready = False
        self.tts_activity = time.monotonic()
        self.tts = ProcessChannel(voice_worker, path)
        return True

    def toggle_play(self):
        if not self.book or not self.book["segments"]:
            return

        if self.desired:
            self.desired = False
            self.player.pause()

            if self.phase != "loading":
                self.phase = "paused"

            self.save_progress()
            self.play_button.setText("Continuar")
            self.status.setText(
                "Pausado. Preparando áudio em segundo plano "
                "até o limite da reserva."
            )
            self.highlight()
            self.drive()
            return

        if self.completed:
            self.navigate(0, False)

        if not self.ensure_voice():
            return

        self.desired = True
        self.play_button.setText("Pausar")

        if (
            self.loaded_index == self.index
            and self.player.source().isValid()
        ):
            if self.phase == "loading":
                self.start_loaded()
            else:
                self.player.play()
                self.phase = "playing"
        else:
            self.phase = "buffering"

        self.drive()
        

    def unload_player(self):
        self.loading_guard = True
        self.loaded_index = None
        self.expected_source = ""
        self.player.stop()
        self.player.setSource(QUrl())
        self.loading_guard = False

    def navigate(self, index, autoplay=True):
        if not self.book or not 0 <= index < len(self.book["segments"]):
            return
        self.save_progress()
        self.desired = False
        self.unload_player()
        self.token += 1
        self.index = index
        self.offset = 0
        self.completed = False
        self.phase = "paused"
        self.prune(jump=True)
        if self.follow.isChecked():
            target = self.book["segments"][index]["page"]
            if target != self.page:
                self.show_page(target)
        self.refresh_selection()
        self.save_progress()
        self.play_button.setText("Reproduzir")
        if autoplay and self.ensure_voice():
            self.desired = True
            self.play_button.setText("Pausar")
            if index in self.cache:
                self.load_current()
            else:
                self.phase = "buffering"
            self.drive()

    def drive(self):
        if (
            not self.book
            or not self.tts
            or not self.tts_ready
            or self.completed
            or self.phase == "error"
        ):
            return

        seconds, end_ready = buffered_seconds(
            self.cache,
            self.index,
            len(self.book["segments"]),
            self.offset,
            self.rate.value(),
        )

        # Só inicia a reprodução quando o usuário deseja ouvir.
        if (
            self.desired
            and self.phase == "buffering"
            and self.index in self.cache
            and (
                seconds >= self.reserve.currentData()
                or end_ready
            )
        ):
            self.load_current()

        # A geração pode continuar mesmo com a reprodução pausada.
        if self.pending_audio is None and seconds < MAX_AHEAD:
            index = next_missing(
                self.cache,
                self.index,
                len(self.book["segments"]),
            )

            if index is not None:
                path = (
                    self.folder
                    / f"{self.token}_{index}_{uuid.uuid4().hex[:6]}.wav"
                )

                job = {
                    "index": index,
                    "text": self.book["segments"][index]["text"],
                    "path": str(path),
                    "token": self.token,
                    "voice": self.voice_choice.currentData(),
                    "kind": (self.book['segments'][index].get('kind', 'prose')
                             if self.narration_mode.currentData() == 'auto'
                             else self.narration_mode.currentData()),
                }

                self.pending_audio = job
                self.tts_activity = time.monotonic()
                self.tts.send(job)


    def load_current(self):
        if self.index not in self.cache:
            self.phase = "buffering"
            return
        self.phase = "loading"
        self.loaded_index = self.index
        self.seek_started = time.monotonic()
        self.expected_source = str(Path(self.cache[self.index]["path"]).resolve())
        self.player.setSource(QUrl.fromLocalFile(self.expected_source))
        self.player.setPlaybackRate(self.rate.value())
        if self.follow.isChecked():
            target = self.book["segments"][self.index]["page"]
            if target != self.page:
                self.show_page(target)
        self.refresh_selection()

    def start_loaded(self):
        if self.loading_guard or self.phase != "loading" or self.loaded_index != self.index:
            return
        if self.player.mediaStatus() not in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            return
        if self.offset > 0 and not self.player.isSeekable():
            if time.monotonic() - self.seek_started < 3:
                return
            self.offset = 0
            logging.warning("Áudio sem seek: retomada pelo início do trecho")
        if self.offset:
            duration = self.player.duration()
            self.player.setPosition(min(self.offset, max(0, duration - 100)) if duration else self.offset)
        self.phase = "playing" if self.desired else "paused"
        if self.desired:
            self.player.play()
        self.highlight()

    def media_status(self, status):
        if self.loading_guard or not self.book:
            return
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            self.start_loaded()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia and self.phase == "playing" and self.loaded_index == self.index:
            if self.index + 1 >= len(self.book["segments"]):
                self.completed = True
                self.desired = False
                self.offset = 0
                self.phase = "paused"
                self.unload_player()
                self.status.setText("Leitura concluída. Reproduzir começa novamente do início.")
                self.play_button.setText("Recomeçar")
                self.save_progress()
                self.highlight()
                return
            self.offset = 0
            self.index += 1
            self.unload_player()
            self.prune()
            self.refresh_selection()
            self.save_progress()
            if self.index in self.cache:
                self.load_current()
            else:
                self.phase = "buffering"
            self.drive()

    def play_state(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState and self.desired:
            self.phase = "playing"
            self.highlight()

    def position_changed(self, position):
        if not self.loading_guard and self.phase in ("playing", "paused") and self.loaded_index == self.index:
            self.offset = position

    def change_rate(self, rate):
        self.player.setPlaybackRate(rate)
        self.save_progress()

    def audio_error(self, error, message):
        if self.loading_guard or not self.book:
            return
        current = self.cache.pop(self.index, None)
        self.unload_player()
        if current:
            self.garbage.add(current["path"])
        self.fail("Não foi possível reproduzir o áudio. " + message)

    def fail(self, message, detail=""):
        logging.error("%s\n%s", message, detail)
        self.desired = False
        self.player.pause()
        self.phase = "error"
        self.play_button.setText("Tentar novamente")
        self.status.setText(message)
        self.highlight()

    def prune(self, jump=False):
        for index in list(self.cache):
            if index < self.index - 2 or (jump and index > self.index + 2):
                self.garbage.add(self.cache.pop(index)["path"])
        self.collect_garbage()

    def collect_garbage(self):
        for folder in list(self.retired_folders):
            shutil.rmtree(folder, ignore_errors=True)
            if not Path(folder).exists():
                self.retired_folders.remove(folder)
        for path in list(self.garbage):
            if path == self.expected_source:
                continue
            try:
                Path(path).unlink(missing_ok=True)
                self.garbage.remove(path)
            except OSError:
                pass  # Windows pode liberar o arquivo somente depois do evento de troca.

    def tick(self):
        if self.closed:
            return
        if self.pdf:
            for message in list(self.pdf.poll()):
                self.pdf_activity = time.monotonic()
                if message["kind"] == "book":
                    self.book_ready(message["book"])
                elif message["kind"] == "page":
                    self.page_ready(message)
                elif message["kind"] == "progress":
                    self.status.setText(f"Preparando livro… página {message['page']} de {message['total']}")
                elif message["kind"] == "error":
                    self.render_busy = False
                    self.importing = False
                    if "protegido" in message["error"].lower() and message["operation"] == "open":
                        password, ok = QInputDialog.getText(self, "Senha do PDF", "Senha (não será salva):", QLineEdit.EchoMode.Password)
                        if ok:
                            self.open_book(self.opening_path, password)
                        else:
                            self.close_book()
                        return
                    self.fail(message["error"], message["detail"])
            if self.pdf and (not self.pdf.process.is_alive() or (
                    (self.importing or self.render_busy) and time.monotonic() - self.pdf_activity > WORKER_TIMEOUT)):
                self.pdf.stop()
                self.pdf = None
                self.importing = self.render_busy = False
                self.render_pending = None
                self.fail('O processo PDF parou ou excedeu cinco minutos sem resposta. Use Abrir PDF novamente.')
        if self.tts:
            for message in list(self.tts.poll()):
                self.tts_activity = time.monotonic()
                if message["kind"] == "ready":
                    self.tts_ready = True
                elif message["kind"] == "audio":
                    self.pending_audio = None
                    if message["token"] == self.token and self.book:
                        self.cache[message["index"]] = message
                        self.metrics.append({'generation': message['generation'], 'duration': message['duration'],
                                             'rtf': message['generation'] / max(.001, message['duration'])})
                        self.metrics = self.metrics[-20:]
                        logging.info("audio index=%s duration=%.2f generation=%.2f", message["index"], message["duration"], message["generation"])
                        if sum(p.stat().st_size for p in self.folder.glob("*.wav")) > MAX_BYTES:
                            self.fail("Limite de áudio temporário atingido. Use Limpar áudios para continuar.")
                    else:
                        self.garbage.add(message["path"])
                elif message["kind"] == "error":
                    old = self.pending_audio
                    self.pending_audio = None
                    if old:
                        self.garbage.add(old["path"])
                    if message.get("fatal"):
                        self.tts.stop()
                        self.tts = None
                        self.tts_ready = False
                    if message.get("fatal") or message.get("token") == self.token:
                        self.fail("Falha na voz: " + message["error"], message["detail"])
            if self.tts and (not self.tts.process.is_alive() or (
                    (not self.tts_ready or self.pending_audio is not None)
                    and time.monotonic() - self.tts_activity > WORKER_TIMEOUT)):
                self.tts.stop()
                self.tts = None
                if self.pending_audio:
                    path = Path(self.pending_audio['path'])
                    self.garbage.update((str(path), str(path.with_suffix('.part.wav'))))
                self.pending_audio = None
                self.tts_ready = False
                self.fail("O mecanismo de voz parou ou excedeu cinco minutos sem progresso. Clique em Tentar novamente.")
        self.collect_garbage()
        self.start_loaded()
        self.drive()
        self.update_status()

    def update_status(self):
        if not self.book or not self.book["segments"]:
            return
        seconds, end = buffered_seconds(self.cache, self.index, len(self.book["segments"]), self.offset, self.rate.value())
        target = self.reserve.currentData()
        self.buffer.setRange(0, target)
        self.buffer.setValue(min(target, int(seconds)))
        self.start_now.setEnabled(self.desired and self.phase == "buffering" and self.index in self.cache)
        self.buffer_label.setText(f"{seconds:.0f} s de áudio prontos · reserva: {target} s")
        self.buffer.setAccessibleDescription(self.buffer_label.text())
        if self.metrics:
            total_audio = sum(m['duration'] for m in self.metrics)
            rtf = sum(m['generation'] for m in self.metrics) / max(.001, total_audio)
            self.buffer.setToolTip(f'RTF recente: {rtf:.2f}. Para sustentar {self.rate.value():.2f}×, precisa ficar abaixo de {1/self.rate.value():.2f}, com margem.')
        if not self.desired and self.phase == 'paused' and not self.completed and self.tts:
            self.status.setText('Pausado. Preparando áudio em segundo plano.' if self.pending_audio
                                else 'Pausado. Reserva pronta; geração aguardando.')
        if self.desired:
            if not self.tts_ready:
                text = "Preparando mecanismo de voz…"
            elif self.phase == "buffering":
                text = f"Preparando áudio… {min(seconds, target):.0f}/{target} s prontos. A leitura começará automaticamente."
            elif self.phase == "loading":
                text = "Abrindo áudio…"
            else:
                text = f"Lendo trecho {self.index + 1} de {len(self.book['segments'])} · {self.voice_choice.currentText()} · {self.rate.value():.2f}×"
            self.status.setText(text)

    def save_progress(self):
        if self.book and self.book["segments"]:
            snapshot = (self.book['hash'], self.index, self.offset, self.rate.value(), self.page,
                        self.zoom.value(), self.completed, self.voice_choice.currentData(), self.audio_revision())
            if snapshot != self.saved_snapshot:
                self.store.save(*snapshot[:-1], revision=snapshot[-1])
                self.saved_snapshot = snapshot

    def stop_voice(self):
        if self.tts:
            self.tts.stop()
        self.tts = None
        self.tts_ready = False
        self.pending_audio = None

    def remove_audio(self):
        self.cache.clear()
        self.garbage.clear()
        if self.folder:
            shutil.rmtree(self.folder, ignore_errors=True)
            if self.folder.exists():
                self.retired_folders.add(str(self.folder))
        clean_sessions(self.audio_root)

    def clear_audio(self):
        self.save_progress()
        self.desired = False
        self.unload_player()
        self.token += 1
        self.stop_voice()
        self.remove_audio()
        if self.book:
            self.folder = self.audio_root / ("session_" + uuid.uuid4().hex)
            self.folder.mkdir(parents=True)
        self.phase = "paused"
        self.play_button.setText("Reproduzir")
        self.status.setText("Áudios temporários removidos. O ponto de leitura foi mantido.")
        self.highlight()

    def close_book(self):
        self.save_progress()
        self.desired = False
        self.token += 1
        self.unload_player()
        self.stop_voice()
        if self.pdf:
            self.pdf.stop()
        self.pdf = None
        self.book = None
        self.page_segments = {}
        self.saved_snapshot = None
        self.importing = False
        self.render_busy = False
        self.render_pending = None
        self.remove_audio()
        self.folder = None
        self.phase = "idle"
        self.offset = 0
        self.completed = False
        self.viewer.clear_page()
        self.lines.clear()
        self.chapters.clear()
        self.title_label.setText("Nenhum livro aberto")
        self.page_box.setRange(1, 1)
        self.page_total.setText("/ 0")
        self.status.setText("Livro fechado. O ponto de leitura foi salvo e os áudios temporários foram removidos.")
        self.buffer.setValue(0)
        self.buffer_label.setText("Nenhum áudio preparado")
        self.start_now.setEnabled(False)
        self.play_button.setText("Reproduzir")

    def closeEvent(self, event):
        self.poller.stop()
        self.saver.stop()
        self.close_book()
        self.closed = True
        self.store.close()
        event.accept()
