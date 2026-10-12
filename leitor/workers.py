import os
import queue
import traceback


def pdf_worker(commands, results):
    import pymupdf as fitz
    from .pdf_service import extract_book, render_page
    doc = None
    while True:
        job = commands.get()
        if job is None:
            break
        try:
            if job["kind"] == "open":
                if doc:
                    doc.close()
                book = extract_book(job["path"], job.get("password", ""),
                    lambda page, total: results.put({"kind": "progress", "page": page, "total": total})
                    if page % 10 == 0 or page == total else None)
                doc = fitz.open(job["path"])
                if doc.needs_pass:
                    doc.authenticate(job.get("password", ""))
                results.put({"kind": "book", "book": book})
            elif job["kind"] == "render" and doc:
                results.put({"kind": "page", "request": job["request"], "page": job["page"],
                             **render_page(doc, job["page"], job["scale"])})
        except Exception as error:
            results.put({"kind": "error", "operation": job["kind"], "error": str(error), "detail": traceback.format_exc()})
    if doc:
        doc.close()


def voice_worker(commands, results, model_dir):
    os.environ["ORT_DISABLE_TELEMETRY"] = "1"
    from pathlib import Path
    from .voice import VoiceEngine
    try:
        engine = VoiceEngine(Path(model_dir) / "kokoro-v1.0.onnx", Path(model_dir) / "voices-v1.0.bin", threads=4)
        results.put({"kind": "ready"})
    except Exception as error:
        results.put({"kind": "error", "error": str(error), "detail": traceback.format_exc(), "fatal": True})
        return
    while True:
        job = commands.get()
        if job is None:
            break
        try:
            metric = engine.render([{'text': job['text'], 'kind': job.get('kind', 'prose'),
                                    'next_kind': job.get('next_kind'), 'prepared': job.get('prepared', False)}],
                job.get('voice', 'pf_dora'), job['path'],
                progress=lambda _: results.put({'kind': 'progress', 'token': job['token']}))
            results.put({"kind": "audio", "token": job["token"], "index": job["index"],
                         "path": job["path"], "duration": metric["audio_s"], "generation": metric["geracao_s"]})
        except Exception as error:
            results.put({"kind": "error", "token": job["token"], "error": str(error), "detail": traceback.format_exc()})


class ProcessChannel:
    def __init__(self, target, *args):
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        self.commands = ctx.Queue()
        self.results = ctx.Queue()
        self.process = ctx.Process(target=target, args=(self.commands, self.results, *args), daemon=True)
        self.process.start()

    def send(self, job):
        self.commands.put(job)

    def poll(self):
        for _ in range(100):
            try:
                yield self.results.get_nowait()
            except queue.Empty:
                break

    def stop(self):
        # Terminação encerra inferência nativa antes da limpeza dos WAVs.
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=2)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=1)
        for q in (self.commands, self.results):
            q.cancel_join_thread()
            q.close()
