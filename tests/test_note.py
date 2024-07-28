import pytest
from zkb import Note


@pytest.fixture
def temp_note_file(tmp_path):
    """Create a temporary note file for testing."""
    content = """---
title: Test Note
tags: [test, pytest]
entities:
  - Person
  - Place
relationships:
  - type: located_in
    source: Person
    target: Place
---
This is a test note.
It contains a [[link]] and a [[complex link#heading|display text]].
"""
    file_path = tmp_path / "test_note.md"
    file_path.write_text(content)
    return file_path


def test_note_initialization(temp_note_file):
    note = Note(temp_note_file)
    assert note.file_path == temp_note_file
    assert note.filename == "test_note"
    assert note.full_path == temp_note_file.absolute()


def test_note_metadata(temp_note_file):
    note = Note(temp_note_file)
    assert note.metadata == {"title": "Test Note", "tags": ["test", "pytest"]}


def test_note_content(temp_note_file):
    note = Note(temp_note_file)
    assert (
        note.content.strip()
        == "This is a test note.\nIt contains a [[link]] and a [[complex link#heading|display text]]."
    )


def test_note_links(temp_note_file):
    note = Note(temp_note_file)
    expected_links = [
        {"filename": "link", "heading": None, "display_text": "link"},
        {
            "filename": "complex link",
            "heading": "heading",
            "display_text": "display text",
        },
    ]
    assert note.links == expected_links


def test_note_entities(temp_note_file):
    note = Note(temp_note_file)
    assert note.entities == ["Person", "Place"]


def test_note_relationships(temp_note_file):
    note = Note(temp_note_file)
    expected_relationship = {
        "type": "located_in",
        "source": "Person",
        "target": "Place",
    }
    assert note.relationships == [expected_relationship]


def test_note_str_representation(temp_note_file):
    note = Note(temp_note_file)
    assert str(note) == "Note: test_note"


def test_note_repr_representation(temp_note_file):
    note = Note(temp_note_file)
    repr_str = repr(note)

    # Check for the presence of key components in the repr string
    assert f"Note(file_path='{note.file_path}'" in repr_str
    assert "filename='test_note'" in repr_str
    assert f"full_path='{note.full_path}'" in repr_str
    assert "metadata={'title': 'Test Note', 'tags': ['test', 'pytest']}" in repr_str
    assert "content='This is a test note." in repr_str
    assert (
        "links=[{'filename': 'link', 'heading': None, 'display_text': 'link'}, {'filename': 'complex link', 'heading': 'heading', 'display_text': 'display text'}]"
        in repr_str
    )
    assert "entities=['Person', 'Place']" in repr_str
    assert (
        "relationships=[{'type': 'located_in', 'source': 'Person', 'target': 'Place'}]"
        in repr_str
    )


def test_note_without_frontmatter(tmp_path):
    content = "This is a note without frontmatter."
    file_path = tmp_path / "no_frontmatter.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {}
    assert note.content == content
    assert note.links == []
    assert note.entities == []
    assert note.relationships == []


def test_note_with_invalid_yaml(tmp_path):
    content = """---
invalid: yaml: content:
---
This is a note with invalid YAML in the frontmatter.
"""
    file_path = tmp_path / "invalid_yaml.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {}
    assert (
        note.content.strip() == "This is a note with invalid YAML in the frontmatter."
    )


def test_note_with_empty_frontmatter(tmp_path):
    content = """---
---
This is a note with empty frontmatter.
"""
    file_path = tmp_path / "empty_frontmatter.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {}
    assert note.content.strip() == "This is a note with empty frontmatter."


def test_note_with_only_metadata(tmp_path):
    content = """---
title: Metadata Only
tags: [test]
---"""
    file_path = tmp_path / "metadata_only.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {"title": "Metadata Only", "tags": ["test"]}
    assert note.content == ""


def test_note_with_unicode_content(tmp_path):
    content = """---
title: Unicode Test
---
This note contains unicode characters: ñ, é, 漢字
"""
    file_path = tmp_path / "unicode_test.md"
    file_path.write_text(content, encoding="utf-8")

    note = Note(file_path)
    assert "unicode characters: ñ, é, 漢字" in note.content
