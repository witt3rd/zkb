import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

        original_note = Note(full_path)

        full_content = self._prepare_note_content(content, metadata)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(full_content)
        updated_note = Note(full_path)
        updated_note.metadata = {**original_note.metadata, **updated_note.metadata}

        self._update_note_in_db(updated_note)
        self.qa_kb.collection.delete(where={"note_filename": filename})
        self.generate_and_index_qa_pairs(updated_note)

        return updated_note

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
        if not metadata:
            return content
        yaml_metadata = "---\n"
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

    def add_entity(
        self,
        entity_type: str,
        entity_name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Add a new entity to the ontology.

        Parameters
        ----------
        entity_type : str
            The type of the entity
        entity_name : str
            The name of the entity
        attributes : Optional[Dict[str, Any]], optional
            Additional attributes for the entity, by default None

        Returns
        -------
        int
            The ID of the newly added entity
        """
        entity_id = self.db.add_entity(entity_type, entity_name)
        if attributes:
            for key, value in attributes.items():
                self.db.add_relationship(
                    entity_id, self.db.add_entity("Attribute", str(value)), key
                )
        return entity_id

    def add_relationship(
        self, from_entity: str, to_entity: str, relationship_type: str
    ) -> int:
        """
        Add a new relationship between entities in the ontology.

        Parameters
        ----------
        from_entity : str
            The name of the entity the relationship starts from
        to_entity : str
            The name of the entity the relationship points to
        relationship_type : str
            The type of the relationship

        Returns
        -------
        int
            The ID of the newly added relationship
        """
        from_id = self.db.get_entity_id(from_entity)
        to_id = self.db.get_entity_id(to_entity)
        return self.db.add_relationship(from_id, to_id, relationship_type)

    def query_entities(
        self, entity_type: Optional[str] = None, name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query entities in the ontology.

        Parameters
        ----------
        entity_type : Optional[str], optional
            The type of entities to query, by default None
        name : Optional[str], optional
            The name of the entity to query, by default None

        Returns
        -------
        List[Dict[str, Any]]
            A list of matching entities with their attributes
        """
        entities = self.db.get_entities(entity_type, name)
        return [self._get_entity_with_attributes(entity) for entity in entities]

    def query_relationships(
        self,
        from_type: Optional[str] = None,
        from_name: Optional[str] = None,
        relationship_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query relationships in the ontology.

        Parameters
        ----------
        from_type : Optional[str], optional
            The type of the source entity, by default None
        from_name : Optional[str], optional
            The name of the source entity, by default None
        relationship_type : Optional[str], optional
            The type of relationship to query, by default None

        Returns
        -------
        List[Dict[str, Any]]
            A list of matching relationships
        """
        return self.db.get_relationships(from_type, from_name, relationship_type)

    def _get_entity_with_attributes(
        self, entity: Tuple[int, str, str]
    ) -> Dict[str, Any]:
        """
        Helper method to get an entity with its attributes.

        Parameters
        ----------
        entity : Tuple[int, str, str]
            A tuple containing (id, type, name) of the entity

        Returns
        -------
        Dict[str, Any]
            A dictionary representing the entity with its attributes
        """
        entity_id, entity_type, entity_name = entity
        attributes = self.db.get_entity_attributes(entity_id)
        return {
            "id": entity_id,
            "type": entity_type,
            "name": entity_name,
            "attributes": {attr[0]: attr[1] for attr in attributes},
        }

    def unified_query(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a unified query across both unstructured notes and structured ontology.

        Parameters
        ----------
        query : str
            The query string
        n_results : int, optional
            Number of results to return, by default 5

        Returns
        -------
        List[Dict[str, Any]]
            A list of results combining both unstructured and structured data
        """
        # Query unstructured notes
        qa_results = self.query_qa(query, n_results=n_results)

        # Query ontology (simplified example)
        entity_results = self.query_entities(name=query)
        relationship_results = self.query_relationships(from_name=query)

        # Combine results (this is a simplified example and might need more sophisticated merging)
        combined_results = qa_results + entity_results + relationship_results

        # Sort and limit results (this is a very basic approach and might need refinement)
        return sorted(
            combined_results, key=lambda x: x.get("relevance", 0), reverse=True
        )[:n_results]
