import pytest


def test_create_note(zkb_instance, sample_note_content):
    note = zkb_instance.create_note("test_note", sample_note_content)
    assert note.filename == "test_note"
    assert (
        note.content.strip()
        == "This is a sample note content.\nIt contains a [[link]] to another note."
    )
    assert note.metadata["title"] == "Sample Note"
    assert note.metadata["tags"] == ["test", "sample"]


def test_read_note(zkb_instance, sample_note):
    note = zkb_instance.read_note("sample_note")
    assert note.filename == "sample_note"
    assert "This is a sample note content." in note.content
    assert "---" not in note.content  # Ensure YAML frontmatter is not in content


def test_update_note(zkb_instance, sample_note):
    updated_content = "Updated content"
    updated_note = zkb_instance.update_note("sample_note", updated_content)
    assert updated_note.content.strip() == updated_content


def test_delete_note(zkb_instance, sample_note):
    zkb_instance.delete_note("sample_note")
    with pytest.raises(FileNotFoundError):
        zkb_instance.read_note("sample_note")


def test_search_notes(zkb_instance, sample_note):
    results = zkb_instance.search_notes("sample")
    assert len(results) == 1
    assert results[0].filename == "sample_note"


def test_create_existing_note(zkb_instance, sample_note):
    with pytest.raises(FileExistsError):
        zkb_instance.create_note("sample_note", "New content")


def test_read_nonexistent_note(zkb_instance):
    with pytest.raises(FileNotFoundError):
        zkb_instance.read_note("nonexistent_note")


def test_update_nonexistent_note(zkb_instance):
    with pytest.raises(FileNotFoundError):
        zkb_instance.update_note("nonexistent_note", "Updated content")


def test_delete_nonexistent_note(zkb_instance):
    with pytest.raises(FileNotFoundError):
        zkb_instance.delete_note("nonexistent_note")


def test_note_content_without_frontmatter(zkb_instance, sample_note):
    note = zkb_instance.read_note("sample_note")
    assert "---" not in note.content
    assert note.content.strip().startswith("This is a sample note content.")


def test_update_note_preserves_metadata(zkb_instance, sample_note):
    updated_content = "Updated content\nWith multiple lines"
    updated_note = zkb_instance.update_note("sample_note", updated_content)
    assert updated_note.content.strip() == updated_content
    assert updated_note.metadata["title"] == "Sample Note"
    assert updated_note.metadata["tags"] == ["test", "sample"]
