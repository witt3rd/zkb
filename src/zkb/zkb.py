import os
from pathlib import Path

from dotenv import load_dotenv

from .db import Database
from .note import Note

#

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "data/")
DB_DIR = os.getenv("DB_DIR", "db/")
DB_PATH = os.path.join(DB_DIR, "zkb.db")

#


class ZKB:
    def __init__(
        self,
        data_dir: str | None = DATA_DIR,
        db_path: str | None = DB_PATH,
    ) -> None:
        self.data_dir = Path(str(data_dir))
        self.notes_dir = self.data_dir / "notes"
        if not self.notes_dir.exists():
            self.notes_dir.mkdir(parents=True)
        db_dir = Path(str(db_path)).parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True)
        self.db = Database(str(db_path))

    def scan_notes(self) -> None:
        for note_file in self.notes_dir.rglob("*.md"):
            note = Note(note_file)
            links = [
                (link["filename"], link.get("display_text", link["filename"]))
                for link in note.links
            ]
            self.db.add_or_update_note_links(
                note.filename,
                str(note.full_path),
                note.metadata.get("title", note.filename),
                links,
            )

    def find_orphaned_notes(self) -> list[str]:
        orphans = self.db.get_orphaned_notes()
        return [orphan[0] for orphan in orphans]

    def find_broken_links(self) -> list[tuple[str, str]]:
        broken_links = self.db.get_broken_links()
        return [(filename, link) for filename, link in broken_links]

    def find_backlinks(self, filename) -> list[str]:
        backlinks = self.db.get_backlinks(filename)
        return [backlink[0] for backlink in backlinks]
