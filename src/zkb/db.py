import sqlite3
from dataclasses import dataclass
from typing import List, Literal, Optional


@dataclass
class NoteInfo:
    filename: str


@dataclass
class NoteContent:
    filename: str
    content: str


@dataclass
class LinkInfo:
    source: str
    target: str
    alias: str
    is_broken: bool


@dataclass
class BrokenLink:
    from_note: str
    to_note: str
    link_type: str


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
                    content TEXT
                )
            """)

            # Links table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY,
                    from_note TEXT,
                    to_note TEXT,
                    alias TEXT,
                    is_broken BOOLEAN DEFAULT 0,
                    FOREIGN KEY(from_note) REFERENCES notes(filename),
                    UNIQUE(from_note, to_note, alias)
                )
            """)

    def add_or_update_note(self, filename: str, content: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO notes (filename, content)
                VALUES (?, ?)
                ON CONFLICT(filename) DO UPDATE SET
                    content = excluded.content
            """,
                (filename, content),
            )
            # Update broken status of incoming links
            self.conn.execute(
                """
                UPDATE links SET is_broken = 0
                WHERE to_note = ?
            """,
                (filename,),
            )

    def add_or_update_link(self, from_note: str, to_note: str, alias: str) -> None:
        """Add or update a link between two notes."""
        print(f"Adding link: {from_note} -> {to_note} ({alias})")
        with self.conn:
            target_exists = (
                self.conn.execute(
                    "SELECT 1 FROM notes WHERE filename = ?", (to_note,)
                ).fetchone()
                is not None
            )

            self.conn.execute(
                """
                INSERT INTO links (from_note, to_note, alias, is_broken)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(from_note, to_note, alias) DO UPDATE SET
                    is_broken = excluded.is_broken
                """,
                (from_note, to_note, alias, not target_exists),
            )

    def get_all_notes(self) -> List[NoteInfo]:
        with self.conn:
            results = self.conn.execute("SELECT filename, title FROM notes").fetchall()
        return [NoteInfo(filename) for filename, title in results]

    def get_note(self, filename: str) -> Optional[NoteContent]:
        with self.conn:
            result = self.conn.execute(
                "SELECT filename, content FROM notes WHERE filename = ?",
                (filename,),
            ).fetchone()
        return NoteContent(*result) if result else None

    def get_links(
        self, filename: str, direction: Literal["outgoing", "incoming"] = "outgoing"
    ) -> List[LinkInfo]:
        with self.conn:
            if direction == "outgoing":
                query = """
                    SELECT from_note, to_note, alias, is_broken
                    FROM links
                    WHERE from_note = ?
                """
                params = (filename,)
            else:  # incoming
                query = """
                    SELECT from_note, to_note, links.alias, links.is_broken
                    FROM links
                    WHERE links.to_note = ? OR links.alias = ?
                """
                params = (filename, filename)
            results = self.conn.execute(query, params).fetchall()
        return [LinkInfo(*result) for result in results]

    def search_notes(self, query: str) -> List[NoteInfo]:
        with self.conn:
            results = self.conn.execute(
                """
                SELECT DISTINCT n.filename
                FROM notes n
                LEFT JOIN links l ON n.filename = l.to_note
                WHERE n.content LIKE ? OR l.alias LIKE ?
                """,
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        return [NoteInfo(filename) for filename in results]

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

    def get_broken_links(self) -> List[BrokenLink]:
        with self.conn:
            results = self.conn.execute("""
                SELECT from_note, to_note, alias
                FROM links
                WHERE is_broken = 1
            """).fetchall()
        return [BrokenLink(*result) for result in results]

    def get_orphaned_notes(self) -> List[str]:
        with self.conn:
            results = self.conn.execute("""
                SELECT filename
                FROM notes
                WHERE filename NOT IN (
                    SELECT DISTINCT to_note
                    FROM links
                )
                AND filename NOT IN (
                    SELECT DISTINCT alias
                    FROM links
                    WHERE alias IS NOT NULL
                )
            """).fetchall()
        return [result[0] for result in results]
