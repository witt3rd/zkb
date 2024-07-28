from zkb import Note


def test_note_initialization(sample_note_file):
    note = Note(sample_note_file)
    assert note.file_path == sample_note_file
    assert note.filename == "sample_note"
    assert note.full_path == sample_note_file.absolute()


def test_note_metadata(sample_note):
    assert sample_note.metadata == {"title": "Sample Note", "tags": ["test", "sample"]}


def test_note_content(sample_note):
    expected_content = """# Sample Note

This is a sample note content.
It contains a [[link]] to another note.
[[has-tag|test]]
[[has-tag|sample]]"""
    assert sample_note.content.strip() == expected_content


def test_note_links(sample_note):
    expected_links = [
        {"target": "link", "alias": "link"},
        {"target": "has-tag", "alias": "test"},
        {"target": "has-tag", "alias": "sample"},
    ]
    assert sample_note.links == expected_links


def test_note_title(sample_note):
    assert sample_note.title == "Sample Note"


def test_note_str_representation(sample_note):
    assert str(sample_note) == "Note: sample_note"


def test_note_repr_representation(sample_note):
    repr_str = repr(sample_note)
    assert "Note(file_path=" in repr_str
    assert "filename='sample_note'" in repr_str
    assert "full_path=" in repr_str
    assert "metadata={'title': 'Sample Note', 'tags': ['test', 'sample']}" in repr_str
    assert "content='# Sample Note" in repr_str
    assert "links=[{'target': 'link', 'alias': 'link'}" in repr_str


def test_note_update_content(sample_note):
    new_content = "Updated content\n[[new-link]]"
    sample_note.update_content(new_content)
    assert sample_note.content == new_content
    assert sample_note.links == [{"target": "new-link", "alias": "new-link"}]


def test_note_add_link(sample_note):
    sample_note.add_link("new-target", "new-alias")
    assert {"target": "new-target", "alias": "new-alias"} in sample_note.links


def test_note_remove_link(sample_note):
    sample_note.remove_link("link")
    assert {"target": "link", "alias": "link"} not in sample_note.links


def test_note_without_frontmatter(temp_dir):
    content = "This is a note without frontmatter."
    file_path = temp_dir / "no_frontmatter.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {}
    assert note.content == content
    assert note.links == []


def test_note_with_invalid_yaml(temp_dir):
    content = """---
invalid: yaml: content:
---
This is a note with invalid YAML in the frontmatter.
"""
    file_path = temp_dir / "invalid_yaml.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {}
    assert (
        note.content.strip() == "This is a note with invalid YAML in the frontmatter."
    )


def test_note_with_empty_frontmatter(temp_dir):
    content = """---
---
This is a note with empty frontmatter.
"""
    file_path = temp_dir / "empty_frontmatter.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {}
    assert note.content.strip() == "This is a note with empty frontmatter."


def test_note_with_only_metadata(temp_dir):
    content = """---
title: Metadata Only
tags: [test]
---"""
    file_path = temp_dir / "metadata_only.md"
    file_path.write_text(content)

    note = Note(file_path)
    assert note.metadata == {"title": "Metadata Only", "tags": ["test"]}
    assert note.content == ""


def test_note_with_unicode_content(temp_dir):
    content = """---
title: Unicode Test
---
This note contains unicode characters: ñ, é, 漢字
"""
    file_path = temp_dir / "unicode_test.md"
    file_path.write_text(content, encoding="utf-8")

    note = Note(file_path)
    assert "unicode characters: ñ, é, 漢字" in note.content
