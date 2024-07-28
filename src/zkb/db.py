import sqlite3
from typing import Any, Dict, List, Optional, Tuple


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
            # Notes table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY,
                    filename TEXT UNIQUE,
                    full_path TEXT UNIQUE,
                    title TEXT
                )
            """)

            # Links table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    from_note TEXT,
                    to_note TEXT,
                    display_text TEXT,
                    is_broken BOOLEAN DEFAULT 0,
                    FOREIGN KEY(from_note) REFERENCES notes(filename),
                    FOREIGN KEY(to_note) REFERENCES notes(filename)
                )
            """)

            # Entities table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY,
                    type TEXT,
                    name TEXT,
                    UNIQUE(type, name)
                )
            """)

            # Relationships table (implements reified attributes)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY,
                    from_entity_id INTEGER,
                    to_entity_id INTEGER,
                    type TEXT,
                    FOREIGN KEY(from_entity_id) REFERENCES entities(id),
                    FOREIGN KEY(to_entity_id) REFERENCES entities(id)
                )
            """)

            # Note-Entity association table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS note_entities (
                    note_id INTEGER,
                    entity_id INTEGER,
                    FOREIGN KEY(note_id) REFERENCES notes(id),
                    FOREIGN KEY(entity_id) REFERENCES entities(id),
                    UNIQUE(note_id, entity_id)
                )
            """)

    def add_or_update_note_links(
        self,
        filename: str,
        full_path: str,
        title: str,
        links: List[Tuple[str, str]],
    ) -> None:
        with self.conn:
            # Add or update the note
            self.conn.execute(
                """
                INSERT INTO notes (filename, full_path, title)
                VALUES (?, ?, ?)
                ON CONFLICT(filename) DO UPDATE SET full_path = ?, title = ?
                """,
                (filename, full_path, title, full_path, title),
            )

            # Get existing links for this note
            existing_links = self.conn.execute(
                "SELECT to_note, is_broken FROM links WHERE from_note = ?", (filename,)
            ).fetchall()
            existing_links_dict = {link[0]: link[1] for link in existing_links}

            # Update links
            for link, display_text in links:
                if link in existing_links_dict:
                    # Update existing link
                    self.conn.execute(
                        """
                        UPDATE links
                        SET display_text = ?, is_broken = ?
                        WHERE from_note = ? AND to_note = ?
                        """,
                        (display_text, 0, filename, link),
                    )
                else:
                    # Add new link
                    is_broken = (
                        self.conn.execute(
                            "SELECT 1 FROM notes WHERE filename = ?", (link,)
                        ).fetchone()
                        is None
                    )
                    self.conn.execute(
                        """
                        INSERT INTO links (from_note, to_note, display_text, is_broken)
                        VALUES (?, ?, ?, ?)
                        """,
                        (filename, link, display_text, int(is_broken)),
                    )

            # Remove links that no longer exist
            current_links = set(link for link, _ in links)
            for old_link in existing_links_dict:
                if old_link not in current_links:
                    self.conn.execute(
                        "DELETE FROM links WHERE from_note = ? AND to_note = ?",
                        (filename, old_link),
                    )

            # Update broken status for links pointing to this note
            self.conn.execute(
                "UPDATE links SET is_broken = 0 WHERE to_note = ?", (filename,)
            )

    def add_entity(self, entity_type: str, entity_name: str) -> int:
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO entities (type, name)
                VALUES (?, ?)
                ON CONFLICT(type, name) DO UPDATE SET type = type
                RETURNING id
                """,
                (entity_type, entity_name),
            )
            return cursor.fetchone()[0]

    def add_relationship(
        self, from_entity_id: int, to_entity_id: int, relationship_type: str
    ) -> int:
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO relationships (from_entity_id, to_entity_id, type)
                VALUES (?, ?, ?)
                RETURNING id
                """,
                (from_entity_id, to_entity_id, relationship_type),
            )
            return cursor.fetchone()[0]

    def associate_note_entity(self, note_id: int, entity_id: int) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO note_entities (note_id, entity_id)
                VALUES (?, ?)
                """,
                (note_id, entity_id),
            )

    def get_all_notes(self) -> List[Tuple]:
        with self.conn:
            return self.conn.execute("SELECT * FROM notes").fetchall()

    def get_note_by_filename(self, filename: str) -> Any:
        with self.conn:
            return self.conn.execute(
                "SELECT * FROM notes WHERE filename = ?", (filename,)
            ).fetchone()

    def get_orphaned_notes(self) -> List[Any]:
        with self.conn:
            return self.conn.execute("""
                SELECT filename FROM notes
                WHERE filename NOT IN (
                    SELECT DISTINCT to_note FROM links
                )
            """).fetchall()

    def get_broken_links(self) -> List[Any]:
        with self.conn:
            return self.conn.execute("""
                SELECT from_note, to_note FROM links
                WHERE is_broken = 1
            """).fetchall()

    def get_backlinks(self, filename: str) -> List[Any]:
        with self.conn:
            return self.conn.execute(
                "SELECT from_note FROM links WHERE to_note = ?", (filename,)
            ).fetchall()

    def get_entities_for_note(self, note_id: int) -> List[Tuple]:
        with self.conn:
            return self.conn.execute(
                """
                SELECT e.id, e.type, e.name
                FROM entities e
                JOIN note_entities ne ON e.id = ne.entity_id
                WHERE ne.note_id = ?
            """,
                (note_id,),
            ).fetchall()

    def get_relationships_for_entity(self, entity_id: int) -> List[Tuple]:
        with self.conn:
            return self.conn.execute(
                """
                SELECT r.id, r.type, e.id, e.type, e.name
                FROM relationships r
                JOIN entities e ON r.to_entity_id = e.id
                WHERE r.from_entity_id = ?
            """,
                (entity_id,),
            ).fetchall()

    def delete_note(self, filename: str) -> None:
        with self.conn:
            note_id = self.conn.execute(
                "SELECT id FROM notes WHERE filename = ?", (filename,)
            ).fetchone()
            if note_id:
                note_id = note_id[0]
                self.conn.execute(
                    "DELETE FROM note_entities WHERE note_id = ?", (note_id,)
                )

            # Delete the note from the notes table
            self.conn.execute("DELETE FROM notes WHERE filename = ?", (filename,))

            # Mark incoming links as broken
            self.conn.execute(
                "UPDATE links SET is_broken = 1 WHERE to_note = ?", (filename,)
            )

            # Delete outgoing links from the deleted note
            self.conn.execute("DELETE FROM links WHERE from_note = ?", (filename,))

    def get_entity_id(self, entity_name: str) -> int:
        with self.conn:
            result = self.conn.execute(
                "SELECT id FROM entities WHERE name = ?", (entity_name,)
            ).fetchone()
            if result:
                return result[0]
            raise ValueError(f"Entity '{entity_name}' not found")

    def get_entities(
        self, entity_type: Optional[str] = None, name: Optional[str] = None
    ) -> List[Tuple[int, str, str]]:
        query = "SELECT id, type, name FROM entities WHERE 1=1"
        params = []
        if entity_type:
            query += " AND type = ?"
            params.append(entity_type)
        if name:
            query += " AND name = ?"
            params.append(name)
        with self.conn:
            return self.conn.execute(query, params).fetchall()

    def get_relationships(
        self,
        from_type: Optional[str] = None,
        from_name: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT r.id, e1.type as from_type, e1.name as from_name,
                   r.type as relationship_type, e2.type as to_type, e2.name as to_name
            FROM relationships r
            JOIN entities e1 ON r.from_entity_id = e1.id
            JOIN entities e2 ON r.to_entity_id = e2.id
            WHERE 1=1
        """
        params = []
        if from_type:
            query += " AND e1.type = ?"
            params.append(from_type)
        if from_name:
            query += " AND e1.name = ?"
            params.append(from_name)
        if relationship_type:
            query += " AND r.type = ?"
            params.append(relationship_type)
        with self.conn:
            results = self.conn.execute(query, params).fetchall()
        return [
            dict(
                zip(
                    [
                        "id",
                        "from_type",
                        "from_name",
                        "relationship_type",
                        "to_type",
                        "to_name",
                    ],
                    r,
                )
            )
            for r in results
        ]

    def get_entity_attributes(self, entity_id: int) -> List[Tuple[str, str]]:
        query = """
            SELECT r.type, e.name
            FROM relationships r
            JOIN entities e ON r.to_entity_id = e.id
            WHERE r.from_entity_id = ? AND e.type = 'Attribute'
        """
        with self.conn:
            return self.conn.execute(query, (entity_id,)).fetchall()
