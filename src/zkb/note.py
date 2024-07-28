import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class Note:
    """
    Represents a single note in the Zettelkasten system.

    Attributes:
        file_path (Path): The path to the note file.
        filename (str): The filename of the note without extension.
        full_path (Path): The absolute path to the note file.
        metadata (Dict): Arbitrary metadata associated with the note.
        content (str): The main content of the note.
        links (List[Dict]): List of links found in the note.
    """

    def __init__(self, file_path: Path) -> None:
        """
        Initialize a Note object.

        Args:
            file_path (Path): The path to the note file.
        """
        self.file_path: Path = Path(file_path)
        self.filename: str = self.file_path.stem
        self.full_path: Path = file_path.absolute()
        self.metadata: Dict = {}
        self.content: str = ""
        self.links: List[Dict] = []
        self._parse_note()

    def __str__(self) -> str:
        return f"Note: {self.filename}"

    def __repr__(self) -> str:
        return (
            f"Note(file_path='{self.file_path}', "
            f"filename='{self.filename}', "
            f"full_path='{self.full_path}', "
            f"metadata={self.metadata}, "
            f"content='{self.content[:50]}...', "
            f"links={self.links})"
        )

    def _parse_note(self) -> None:
        """Parse the note file, extracting metadata, content, and links."""
        with open(self.file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Extract YAML frontmatter
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                try:
                    self.metadata = yaml.safe_load(content[3:end]) or {}
                except yaml.YAMLError:
                    self.metadata = {}
                self.content = content[end + 3 :].strip()
            else:
                self.content = content
        else:
            self.content = content

        self.links = self._extract_links()

    def _extract_links(self) -> List[Dict]:
        """
        Extract links from the note content.

        Returns:
            List[Dict]: A list of dictionaries containing link information.
        """
        link_pattern = r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]"
        matches = re.findall(link_pattern, self.content)
        return [
            {"target": match[0], "alias": match[1] if match[1] else match[0]}
            for match in matches
        ]

    @property
    def title(self) -> str:
        """
        Get the title of the note.

        Returns:
            str: The title of the note, defaulting to the filename if not specified in metadata.
        """
        return self.metadata.get("title", self.filename)

    def update_content(
        self, new_content: str, new_metadata: Optional[Dict] = None
    ) -> None:
        """
        Update the content and metadata of the note.

        Args:
            new_content (str): The new content for the note.
            new_metadata (Optional[Dict]): New metadata to merge with existing metadata.
        """
        if new_metadata:
            self.metadata.update(new_metadata)

        yaml_metadata = (
            "---\n" + yaml.dump(self.metadata) + "---\n\n" if self.metadata else ""
        )
        full_content = yaml_metadata + new_content

        with open(self.file_path, "w", encoding="utf-8") as file:
            file.write(full_content)

        self.content = new_content
        self.links = self._extract_links()

    def add_link(self, target: str, alias: Optional[str] = None) -> None:
        """
        Add a new link to the note content.

        Args:
            target (str): The target of the link.
            alias (Optional[str]): An optional alias for the link.
        """
        link_text = f"[[{target}]]" if alias is None else f"[[{target}|{alias}]]"
        self.content += f"\n{link_text}"
        self.links.append({"target": target, "alias": alias or target})
        self.update_content(self.content)

    def remove_link(self, target: str, alias: Optional[str] = None) -> None:
        """
        Remove a link from the note content.

        Args:
            target (str): The target of the link to remove.
            alias (Optional[str]): The alias of the link to remove, if any.
        """
        link_text = f"[[{target}]]" if alias is None else f"[[{target}|{alias}]]"
        self.content = self.content.replace(link_text, "")
        self.links = [
            link
            for link in self.links
            if link["target"] != target or link["alias"] != (alias or target)
        ]
        self.update_content(self.content)
