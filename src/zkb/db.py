import sqlite3
from typing import List, Literal, Optional, Tuple


class Database:
    def __init__(self, db_file: str) -> None:
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self._create_tables()

    def __str__(self) -> str:
        return f"Database(db_file='{self.db_file}')"

    def __repr__(self) -> str:
        return self.__str__()

    def _create_tables(self) -> None:
        with self.conn:
            # Notes table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    filename TEXT UNIQUE,
                    title TEXT,
                    content TEXT
                )
            """)

            # Links table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY,
                    from_note TEXT,
                    to_note TEXT,
                    link_type TEXT,
                    is_broken BOOLEAN DEFAULT 0,
                    FOREIGN KEY(from_note) REFERENCES notes(filename),
                    UNIQUE(from_note, to_note, link_type)
                )
            """)

    def add_or_update_note(self, filename: str, title: str, content: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO notes (filename, title, content)
                VALUES (?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    title = excluded.title,
                    content = excluded.content
            """,
                (filename, title, content),
            )
            # Update broken status of incoming links
            self.conn.execute(
                """
                UPDATE links SET is_broken = 0
                WHERE to_note = ?
            """,
                (filename,),
            )

    def add_or_update_link(self, from_note: str, to_note: str, link_type: str) -> None:
        with self.conn:
            # Check if the target note exists
            target_exists = (
                self.conn.execute(
                    "SELECT 1 FROM notes WHERE filename = ?", (to_note,)
                ).fetchone()
                is not None
            )

            self.conn.execute(
                """
                INSERT INTO links (from_note, to_note, link_type, is_broken)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(from_note, to_note, link_type) DO UPDATE SET
                    is_broken = excluded.is_broken
                """,
                (from_note, to_note, link_type, not target_exists),
            )

    def get_all_notes(self) -> List[Tuple[str, str]]:
        with self.conn:
            return self.conn.execute("SELECT filename, title FROM notes").fetchall()

    def get_note(self, filename: str) -> Optional[Tuple[str, str, str]]:
        with self.conn:
            result = self.conn.execute(
                """
                SELECT filename, title, content
                FROM notes
                WHERE filename = ?
            """,
                (filename,),
            ).fetchone()
        return result if result else None

    def get_links(
        self,
        filename: str,
        direction: Literal["outgoing", "incoming"] = "outgoing",
    ) -> List[Tuple[str, str, str, bool]]:
        with self.conn:
            if direction == "outgoing":
                query = """
                    SELECT to_note, link_type, COALESCE(notes.title, links.to_note), links.is_broken
                    FROM links
                    LEFT JOIN notes ON links.to_note = notes.filename
                    WHERE from_note = ?
                """
            else:  # incoming
                query = """
                    SELECT from_note, link_type, notes.title, links.is_broken
                    FROM links
                    JOIN notes ON links.from_note = notes.filename
                    WHERE to_note = ?
                """
            return self.conn.execute(query, (filename,)).fetchall()

    def search_notes(self, query: str) -> List[Tuple[str, str]]:
        with self.conn:
            return self.conn.execute(
                """
                SELECT filename, title
                FROM notes
                WHERE title LIKE ? OR content LIKE ?
            """,
                (f"%{query}%", f"%{query}%"),
            ).fetchall()

    def delete_note(self, filename: str) -> None:
        with self.conn:
            # Remove the note
            self.conn.execute("DELETE FROM notes WHERE filename = ?", (filename,))

            # Remove outgoing links from the deleted note
            self.conn.execute("DELETE FROM links WHERE from_note = ?", (filename,))

            # Mark incoming links as broken
            self.conn.execute(
                """
                UPDATE links SET is_broken = 1
                WHERE to_note = ?
            """,
                (filename,),
            )

    def get_broken_links(self) -> List[Tuple[str, str, str]]:
        with self.conn:
            return self.conn.execute("""
                SELECT from_note, to_note, link_type
                FROM links
                WHERE is_broken = 1
            """).fetchall()

    def update_broken_links(self) -> None:
        with self.conn:
            # Mark links as broken if their target note doesn't exist
            self.conn.execute("""
                UPDATE links
                SET is_broken = 1
                WHERE to_note NOT IN (SELECT filename FROM notes)
            """)

            # Mark links as not broken if their target note exists
            self.conn.execute("""
                UPDATE links
                SET is_broken = 0
                WHERE to_note IN (SELECT filename FROM notes)
            """)

        with self.conn:
            return self.conn.execute("SELECT filename, title FROM notes").fetchall()

    def get_orphaned_notes(self) -> List[str]:
        with self.conn:
            return [
                row[0]
                for row in self.conn.execute("""
                SELECT filename FROM notes
                WHERE filename NOT IN (SELECT DISTINCT to_note FROM links)
            """).fetchall()
            ]

    def get_link_types(self) -> List[str]:
        with self.conn:
            return [
                row[0]
                for row in self.conn.execute("""
                SELECT DISTINCT link_type FROM links
            """).fetchall()
            ]
