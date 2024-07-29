import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

from .db import BrokenLink, Database, LinkInfo, NoteInfo
from .note import Note

load_dotenv()

NOTES_DIR = os.getenv("NOTES_DIR", "notes/")
DB_DIR = os.getenv("DB_DIR", "db/")


class ZKB:
    def __init__(
        self,
        notes_dir: Optional[str] = None,
        db_dir: Optional[str] = None,
    ) -> None:
        """
        Initialize the ZKB (Zettelkasten Base) object.

        Parameters
        ----------
        notes_dir : Optional[str], optional
            Directory for storing notes, by default None (uses NOTES_DIR from environment)
        db_dir : Optional[str], optional
            Directory for storing the database, by default None (uses DB_DIR from environment)
        """
        self.notes_path = Path(notes_dir or NOTES_DIR)
        self.notes_path.mkdir(parents=True, exist_ok=True)

        self.db_dir_path = Path(db_dir or DB_DIR)
        self.db_dir_path.mkdir(parents=True, exist_ok=True)
        self.db_file_path = self.db_dir_path / "zkb.db"

        self.db = Database(str(self.db_file_path))

    def create_note(self, title: str, content: str) -> Note:
        """
        Create a new note.

        Parameters
        ----------
        title : str
            The title of the note (will be used as filename)
        content : str
            The content of the note

        Returns
        -------
        Note
            The created Note object

        Raises
        ------
        FileExistsError
            If a note with the same filename already exists
        """
        filename = self._sanitize_filename(title)
        full_path = self.notes_path / f"{filename}.md"
        if full_path.exists():
            raise FileExistsError(f"Note {filename} already exists")
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        note = Note(full_path)
        if "title" not in note.metadata:
            note.metadata["title"] = title
            note.update_content(note.content, note.metadata)
        self._update_note_in_db(note)
        return note

    def read_note(self, filename: str) -> Note:
        """
        Read a note from the file system.

        Parameters
        ----------
        filename : str
            The filename of the note to read (without extension)

        Returns
        -------
        Note
            The Note object

        Raises
        ------
        FileNotFoundError
            If the note does not exist
        """
        full_path = self.notes_path / f"{filename}.md"
        if not full_path.exists():
            raise FileNotFoundError(f"Note {filename} does not exist")
        return Note(full_path)

    def update_note(self, filename: str, new_content: str) -> Note:
        """
        Update an existing note.

        Parameters
        ----------
        filename : str
            The filename of the note to update (without extension)
        new_content : str
            The new content of the note

        Returns
        -------
        Note
            The updated Note object

        Raises
        ------
        FileNotFoundError
            If the note does not exist
        """
        full_path = self.notes_path / f"{filename}.md"
        if not full_path.exists():
            raise FileNotFoundError(f"Note {filename} does not exist")

        note = Note(full_path)
        note.update_content(new_content)
        self._update_note_in_db(note)
        return note

    def delete_note(self, filename: str) -> None:
        """
        Delete a note and remove it from the index.

        Parameters
        ----------
        filename : str
            The filename of the note to delete (without extension)

        Raises
        ------
        FileNotFoundError
            If the note does not exist
        """
        full_path = self.notes_path / f"{filename}.md"
        if not full_path.exists():
            raise FileNotFoundError(f"Note {filename} does not exist")

        os.remove(full_path)
        self.db.delete_note(filename)

    def search_notes(self, query: str) -> List[NoteInfo]:
        """
        Search for notes based on a query string.

        Parameters
        ----------
        query : str
            The search query

        Returns
        -------
        List[NoteInfo]
            A list of NoteInfo objects containing filename and title of matching notes
        """
        return self.db.search_notes(query)

    def get_incoming_links(self, filename: str) -> List[LinkInfo]:
        """
        Get all notes that link to the given note.

        Parameters
        ----------
        filename : str
            The filename of the note to find incoming for

        Returns
        -------
        List[LinkInfo]
            A list of LinkInfo objects containing information about notes linking to the given note
        """
        return self.db.get_links(filename, direction="incoming")

    def get_outgoing_links(self, filename: str) -> List[LinkInfo]:
        """
        Get all notes that the given note links to.

        Parameters
        ----------
        filename : str
            The filename of the note to find outgoing links for

        Returns
        -------
        List[LinkInfo]
            A list of LinkInfo objects containing information about notes linked from the given note
        """
        return self.db.get_links(filename, direction="outgoing")

    def scan_notes(self) -> int:
        """Scan all notes and update the database."""
        count = 0
        for note_file in self.notes_path.rglob("*.md"):
            note = Note(note_file)
            self._update_note_in_db(note)
            count += 1
        self.db.update_broken_links()
        return count

    def get_all_notes(self) -> List[NoteInfo]:
        """
        Get all notes in the database.

        Returns
        -------
        List[NoteInfo]
            A list of NoteInfo objects containing the filename and title of each note
        """
        return self.db.get_all_notes()

    def get_orphaned_notes(self) -> List[str]:
        """
        Find orphaned notes (notes with no incoming links).

        Returns
        -------
        List[str]
            A list of filenames of orphaned notes
        """
        return self.db.get_orphaned_notes()

    def get_broken_links(self) -> List[BrokenLink]:
        """
        Find broken links (links to non-existent notes).

        Returns
        -------
        List[BrokenLink]
            A list of BrokenLink objects containing information about broken links
        """
        return self.db.get_broken_links()

    def _update_note_in_db(self, note: Note) -> None:
        """Update note information in the database."""
        self.db.add_or_update_note(note.filename, note.title, note.content)
        for link in note.links:
            self.db.add_or_update_link(note.filename, link["target"], link["alias"])

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitize the filename to be used as a valid file name."""
        return (
            "".join(c for c in filename.strip() if c.isalnum() or c in (" ", "-", "_"))
            .rstrip()
            .replace(" ", "_")
        )
