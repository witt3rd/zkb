import yaml


def parse_frontmatter(content: str) -> tuple[dict, str]:
    metadata = {}
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            try:
                metadata = yaml.safe_load(content[3:end]) or {}
            except yaml.YAMLError:
                pass
            content = content[end + 3 :].strip()
    return metadata, content
