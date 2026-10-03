import json
import sqlite3
import shutil
from pathlib import Path


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "leitura.sqlite3")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS books(hash TEXT PRIMARY KEY,path TEXT,title TEXT, payload TEXT);
        CREATE TABLE IF NOT EXISTS progress(hash TEXT PRIMARY KEY, segment INTEGER, offset INTEGER,
            rate REAL, page INTEGER, zoom REAL, completed INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
        ''')

        if "voice" not in {row[1] for row in self.db.execute("PRAGMA table_info(progress)")} :
            self.db.execute("ALTER TABLE progress ADD COLUMN voice TEXT DEFAULT 'pf_dora'")
            self.db.commit()

    def put_book(self, book):
        self.db.execute("INSERT OR REPLACE INTO books VALUES(?,?,?,?)",
                        (book["hash"], book["path"], book["title"], json.dumps(book, ensure_ascii=False)))
        self.set("last_path", book["path"])
        self.db.commit()

    def book_payload(self, key):
        row = self.db.execute("SELECT payload FROM books WHERE hash=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def history(self):
        return self.db.execute("SELECT path,title FROM books ORDER BY rowid DESC LIMIT 20").fetchall()

    def save(self, key, index, offset, rate, page, zoom, completed=False, voice="pf_dora", revision=None):
        self.db.execute("INSERT OR REPLACE INTO progress VALUES(?,?,?,?,?,?,?,?)",
                        (key, index, offset, rate, page, zoom, int(completed), voice))
        if revision is not None:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", ('audio_revision:' + key, revision))
        self.db.commit()

    def load(self, key):
        row = self.db.execute("SELECT segment,offset,rate,page,zoom,completed,voice FROM progress WHERE hash=?", (key,)).fetchone()
        return dict(zip(("index", "offset", "rate", "page", "zoom", "completed", "voice"), row)) if row else None

    def get(self, key, default=""):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else default

    def set(self, key, value):
        if self.get(key, None) == str(value):
            return
        self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, str(value)))
        self.db.commit()

    def forget(self, key):
        with self.db:
            self.db.execute('DELETE FROM books WHERE hash=?', (key,))
            self.db.execute('DELETE FROM progress WHERE hash=?', (key,))
            self.db.executemany('DELETE FROM settings WHERE key=?',
                               [('audio_revision:' + key,), ('narration_mode:' + key,)])

    def close(self):
        self.db.close()


def clean_sessions(root):
    """Chamar somente com o bloqueio de instância exclusiva adquirido."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for child in root.glob("session_*"):
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, ignore_errors=True)
