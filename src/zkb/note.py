import re
from pathlib import Path

import yaml


class Note:
    def __init__(
        self,
        file_path: Path,
    ) -> None:
        self.file_path = Path(file_path)
        self.filename = self.file_path.stem
        self.full_path = file_path.absolute()
        self.metadata = {}  # Initialize as an empty dictionary
        self.content = ""
        self.links = []
        self._parse_note()

    def __str__(self) -> str:
        """
        Returns a string representation of the Note object.
        """
        return f"Note: {self.filename}"

    def __repr__(self) -> str:
        """
        Returns a detailed string representation of the Note object.
        """
        return (
            f"Note(file_path='{self.file_path}', "
            f"filename='{self.filename}', "
            f"full_path='{self.full_path}', "
            f"metadata={self.metadata}, "
            f"content='{self.content[:50]}...', "  # First 50 characters of content
            f"links={self.links})"
        )

    def _parse_note(self) -> None:
        with open(self.file_path, "r", encoding="utf-8") as file:
            content = file.read()
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    try:
                        self.metadata = yaml.safe_load(content[3:end]) or {}
                    except yaml.YAMLError:
                        # If YAML parsing fails, set metadata to an empty dict
                        self.metadata = {}
                    self.content = content[end + 3 :].strip()
                else:
                    self.content = content
            else:
                self.content = content
            self.links = self._extract_links()

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
