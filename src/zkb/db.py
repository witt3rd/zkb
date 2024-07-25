import sqlite3
from typing import Any


class Database:
    def __init__(self, db_file: str) -> None:
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self._create_tables()

    def __str__(self) -> str:
        return f"Database(db_file='{self.db_file}')"

    def __repr__(self) -> str:
        return f"Database(db_file='{self.db_file}')"

    def _create_tables(self) -> None:
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    filename TEXT UNIQUE,
                    full_path TEXT UNIQUE,
                    title TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    from_note TEXT,
                    to_note TEXT,
                    display_text TEXT,
                    FOREIGN KEY(from_note) REFERENCES notes(filename),
                    FOREIGN KEY(to_note) REFERENCES notes(filename)
                )
            """)

    def add_or_update_note_links(
        self,
        filename: str,
        full_path: str,
        title: str,
        links: list[tuple[str, str]],
    ) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO notes (filename, full_path, title)
                VALUES (?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET full_path = ?, title = ?
            """,
                (filename, full_path, title, full_path, title),
            )
            self.conn.execute("DELETE FROM links WHERE from_note = ?", (filename,))
            for link, display_text in links:
                self.conn.execute(
                    "INSERT INTO links (from_note, to_note, display_text) VALUES (?, ?, ?)",
                    (filename, link, display_text),
                )

    def get_all_notes(self):
        with self.conn:
            return self.conn.execute("SELECT * FROM notes").fetchall()

    def get_note_by_filename(self, filename) -> Any:
        with self.conn:
            return self.conn.execute(
                "SELECT * FROM notes WHERE filename = ?", (filename,)
            ).fetchone()

    def get_orphaned_notes(self) -> list[Any]:
        with self.conn:
            return self.conn.execute("""
                SELECT filename FROM notes
                WHERE filename NOT IN (
                    SELECT DISTINCT to_note FROM links
                )
            """).fetchall()

    def get_broken_links(self) -> list[Any]:
        with self.conn:
            return self.conn.execute("""
                SELECT from_note, to_note FROM links
                WHERE to_note NOT IN (SELECT filename FROM notes)
            """).fetchall()

    def get_backlinks(self, filename) -> list[Any]:
        with self.conn:
            return self.conn.execute(
                "SELECT from_note FROM links WHERE to_note = ?", (filename,)
            ).fetchall()

    def delete_note(self, filename: str) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM notes WHERE filename = ?", (filename,))
            self.conn.execute(
                "DELETE FROM links WHERE from_note = ? OR to_note = ?",
                (filename, filename),
            )
