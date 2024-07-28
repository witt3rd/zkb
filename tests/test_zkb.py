from pathlib import Path

import pytest
from zkb import ZKB, Note


def test_zkb_initialization(zkb_instance):
    assert isinstance(zkb_instance, ZKB)
    assert Path(zkb_instance.data_path).exists()
    assert Path(zkb_instance.notes_path).exists()
    assert Path(zkb_instance.db_dir_path).exists()
    assert Path(zkb_instance.db_file_path).exists()


def test_create_note(zkb_instance):
    note = zkb_instance.create_note("Test Note", "This is a test note.")
    assert isinstance(note, Note)
    assert note.title == "Test Note"
    assert "This is a test note." in note.content
    assert Path(zkb_instance.notes_path / "Test_Note.md").exists()


def test_create_duplicate_note(zkb_instance):
    zkb_instance.create_note("Duplicate", "Original content")
    with pytest.raises(FileExistsError):
        zkb_instance.create_note("Duplicate", "New content")


def test_read_note(zkb_instance):
    zkb_instance.create_note("Read Test", "Content to be read")
    note = zkb_instance.read_note("Read_Test")
    assert isinstance(note, Note)
    assert note.title == "Read Test"
    assert "Content to be read" in note.content


def test_read_nonexistent_note(zkb_instance):
    with pytest.raises(FileNotFoundError):
        zkb_instance.read_note("Nonexistent")


def test_update_note(zkb_instance):
    zkb_instance.create_note("Update Test", "Original content")
    updated_note = zkb_instance.update_note("Update_Test", "Updated content")
    assert "Updated content" in updated_note.content
    assert "Original content" not in updated_note.content


def test_update_nonexistent_note(zkb_instance):
    with pytest.raises(FileNotFoundError):
        zkb_instance.update_note("Nonexistent", "New content")


def test_delete_note(zkb_instance):
    zkb_instance.create_note("Delete Test", "Content to be deleted")
    assert Path(zkb_instance.notes_path / "Delete_Test.md").exists()
    zkb_instance.delete_note("Delete_Test")
    assert not Path(zkb_instance.notes_path / "Delete_Test.md").exists()


def test_delete_nonexistent_note(zkb_instance):
    with pytest.raises(FileNotFoundError):
        zkb_instance.delete_note("Nonexistent")


def test_search_notes(populated_zkb):
    results = populated_zkb.search_notes("ZKB")
    assert len(results) == 3
    assert all("Note" in result["filename"] for result in results)


def test_get_backlinks(populated_zkb):
    backlinks = populated_zkb.get_backlinks("Note1")
    assert len(backlinks) == 1
    assert backlinks[0]["filename"] == "Note3"


def test_get_outgoing_links(populated_zkb):
    outgoing_links = populated_zkb.get_outgoing_links("Note1")
    assert len(outgoing_links) == 1
    assert outgoing_links[0]["filename"] == "Note2"


def test_scan_notes(populated_zkb):
    populated_zkb.scan_notes()
    # Check if all notes are in the database
    all_notes = populated_zkb.db.get_all_notes()
    assert len(all_notes) == 5  # 4 notes + 1 sample note


def test_get_orphaned_notes(populated_zkb):
    orphaned_notes = populated_zkb.get_orphaned_notes()
    assert len(orphaned_notes) == 2
    assert "Orphan" and "Sample" in orphaned_notes


def test_get_broken_links(populated_zkb):
    # Add a note with a broken link
    populated_zkb.create_note("Broken", "This note has a [[NonexistentNote]]")
    broken_links = populated_zkb.get_broken_links()
    assert len(broken_links) == 4
    assert any(
        link["from_note"] == "Broken" and link["to_note"] == "NonexistentNote"
        for link in broken_links
    )


def test_sanitize_filename():
    assert ZKB._sanitize_filename("Test Note") == "Test_Note"
    assert ZKB._sanitize_filename("Complex: Title!") == "Complex_Title"
    assert ZKB._sanitize_filename("   Spaces   ") == "Spaces"


def test_note_with_frontmatter(populated_zkb):
    sample_note = populated_zkb.read_note("Sample")
    print(sample_note.__repr__())
    assert sample_note.title == "Sample Note"
    assert "test" in sample_note.metadata["tags"]
    assert "sample" in sample_note.metadata["tags"]


def test_note_links(populated_zkb):
    sample_note = populated_zkb.read_note("Sample")
    assert len(sample_note.links) == 3
    assert {"target": "link", "alias": "link"} in sample_note.links
    assert {"target": "has-tag", "alias": "test"} in sample_note.links
    assert {"target": "has-tag", "alias": "sample"} in sample_note.links
