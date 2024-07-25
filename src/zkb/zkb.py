import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from qa_store import QuestionAnswerKB

from .db import Database
from .note import Note

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "data/")
DB_DIR = os.getenv("DB_DIR", "db/")


class ZKB:
    def __init__(
        self,
        data_dir: str = DATA_DIR,
        db_dir: str = DB_DIR,
    ) -> None:
        """
        Initialize the ZKB (Zettelkasten Base) object.

        Parameters
        ----------
        data_dir : str, optional
            Directory for storing notes, by default DATA_DIR
        db_dir : str, optional
            Directory for storing the database, by default DB_DIR
        """
        self.data_path = Path(str(data_dir))
        self.notes_path = self.data_path / "notes"
        self.notes_path.mkdir(parents=True, exist_ok=True)

        self.db_dir_path = Path(str(db_dir))
        self.db_dir_path.mkdir(parents=True, exist_ok=True)
        self.db_file_path = self.db_dir_path / "zkb.db"

        self.db = Database(str(self.db_file_path))
        self.qa_kb = QuestionAnswerKB(
            db_dir=db_dir,
            collection_name="zkb",
        )

    def generate_and_index_qa_pairs(
        self,
        note: Note,
        num_rewordings: int = 3,
    ):
        """
        Generate and index question-answer pairs for a given note.

        Parameters
        ----------
        note : Note
            The note to generate QA pairs from
        num_rewordings : int, optional
            Number of rewordings for each question, by default 3
        """
        qa_pairs = self.qa_kb.generate_qa_pairs(note.content)
        for pair in qa_pairs:
            metadata = {
                "note_filename": note.filename,
                "note_full_path": str(note.full_path),
            }
            self.qa_kb.add_qa(
                pair["q"],
                pair["a"],
                metadata=metadata,
                num_rewordings=num_rewordings,
            )

    def scan_notes(self) -> None:
        """Scan all notes and update the database and QA index."""
        for note_file in self.notes_path.rglob("*.md"):
            note = Note(note_file)
            self._update_note_in_db(note)
            self.generate_and_index_qa_pairs(note)

    def find_orphaned_notes(self) -> List[str]:
        """
        Find orphaned notes in the database.

        Returns
        -------
        List[str]
            List of orphaned note filenames
        """
        orphans = self.db.get_orphaned_notes()
        return [orphan[0] for orphan in orphans]

    def find_broken_links(self) -> List[tuple[str, str]]:
        """
        Find broken links in the notes.

        Returns
        -------
        List[tuple[str, str]]
            List of tuples containing (filename, broken_link)
        """
        return self.db.get_broken_links()

    def find_backlinks(self, filename: str) -> List[str]:
        """
        Find backlinks for a given note.

        Parameters
        ----------
        filename : str
            The filename of the note to find backlinks for

        Returns
        -------
        List[str]
            List of filenames that link to the given note
        """
        backlinks = self.db.get_backlinks(filename)
        return [backlink[0] for backlink in backlinks]

    def create_note(
        self,
        filename: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Note:
        """
        Create a new note and add it to the index.

        Parameters
        ----------
        filename : str
            The filename for the new note (without extension)
        content : str
            The content of the note
        metadata : Optional[Dict], optional
            Optional metadata for the note, by default None

        Returns
        -------
        Note
            The created Note object

        Raises
        ------
        FileExistsError
            If a note with the given filename already exists
        """
        full_path = self.notes_path / f"{filename}.md"
        if full_path.exists():
            raise FileExistsError(f"Note {filename} already exists")

        full_content = self._prepare_note_content(content, metadata)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        note = Note(full_path)
        self._update_note_in_db(note)
        self.generate_and_index_qa_pairs(note)

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

    def update_note(
        self,
        filename: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> Note:
        """
        Update an existing note and update it in the index.

        Parameters
        ----------
        filename : str
            The filename of the note to update (without extension)
        content : str
            The new content of the note
        metadata : Optional[Dict], optional
            Optional new metadata for the note, by default None

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

        full_content = self._prepare_note_content(content, metadata)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        note = Note(full_path)
        self._update_note_in_db(note)
        self.qa_kb.collection.delete(where={"note_filename": filename})
        self.generate_and_index_qa_pairs(note)

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
        self.qa_kb.collection.delete(where={"note_filename": filename})

    def search_notes(self, query: str) -> List[Note]:
        """
        Search for notes based on a query string.

        Parameters
        ----------
        query : str
            The search query

        Returns
        -------
        List[Note]
            A list of matching Note objects
        """
        if not query:
            return []
        matching_notes = []
        for note_file in self.notes_path.rglob("*.md"):
            note = Note(note_file)
            if (
                query.lower() in note.content.lower()
                or query.lower() in note.metadata.get("title", "").lower()
            ):
                matching_notes.append(note)
        return matching_notes

    def query_qa(
        self,
        question: str,
        n_results: int = 5,
        num_rewordings: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Query the QA knowledge base.

        Parameters
        ----------
        question : str
            The question to query
        n_results : int, optional
            Number of results to return, by default 5
        num_rewordings : int, optional
            Number of rewordings for the question, by default 3

        Returns
        -------
        List[Dict[str, Any]]
            List of matching QA pairs with metadata
        """
        return self.qa_kb.query(
            question, n_results=n_results, num_rewordings=num_rewordings
        )

    def _prepare_note_content(
        self, content: str, metadata: Optional[Dict] = None
    ) -> str:
        """Prepare note content with YAML frontmatter."""
        yaml_metadata = "---\n"
        if metadata:
            for key, value in metadata.items():
                yaml_metadata += f"{key}: {value}\n"
        yaml_metadata += "---\n\n"
        return yaml_metadata + content

    def _update_note_in_db(self, note: Note) -> None:
        """Update note information in the database."""
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
