import re
from pathlib import Path

import yaml


class Note:
    def __init__(self, file_path: Path) -> None:
        self.file_path = Path(file_path)
        self.filename = self.file_path.stem
        self.full_path = file_path.absolute()
        self.metadata = {}
        self.content = ""
        self.links = []
        self.entities = []
        self.relationships = []
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
            f"links={self.links}, "
            f"entities={self.entities}, "
            f"relationships={self.relationships})"
        )

    def _parse_note(self) -> None:
        with open(self.file_path, "r", encoding="utf-8") as file:
            content = file.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    try:
                        frontmatter = yaml.safe_load(content[3:end])
                        self.metadata = frontmatter or {}
                        self._extract_ontological_data()
                    except yaml.YAMLError:
                        self.metadata = {}
                    self.content = content[end + 3 :].strip()
                else:
                    self.content = content
            else:
                self.content = content
            self.links = self._extract_links()

    def _extract_ontological_data(self):
        self.entities = self.metadata.get("entities", [])
        self.relationships = self.metadata.get("relationships", [])

        # Remove entities and relationships from metadata to avoid duplication
        self.metadata.pop("entities", None)
        self.metadata.pop("relationships", None)

    def _extract_links(self) -> list[dict]:
        link_pattern = r"\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]"
        matches = re.findall(link_pattern, self.content)
        return [
            {
                "filename": match[0],
                "heading": match[1] if match[1] else None,
                "display_text": match[2] if match[2] else match[0],
            }
            for match in matches
        ]
