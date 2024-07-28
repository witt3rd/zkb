import pytest


@pytest.fixture
def linked_notes(zkb_instance):
    zkb_instance.create_note("note1", "Content with [[note2]] link")
    zkb_instance.create_note("note2", "Content with [[note3]] link")
    zkb_instance.create_note("note3", "Content without links")
    zkb_instance.create_note("orphan", "Orphaned note")
    zkb_instance.scan_notes()  # Ensure all notes are scanned and indexed
    return zkb_instance


def test_find_orphaned_notes(linked_notes):
    orphans = linked_notes.find_orphaned_notes()
    print(f"Orphaned notes: {orphans}")
    assert set(orphans) == {
        "note1",
        "orphan",
    }, f"Expected 'note1' and 'orphan' to be orphaned, but got: {orphans}"


def test_find_broken_links(linked_notes):
    broken_links = linked_notes.find_broken_links()
    print(f"Initial broken links: {broken_links}")
    assert len(broken_links) == 0
    linked_notes.delete_note("note3")
    broken_links = linked_notes.find_broken_links()
    print(f"Broken links after deleting note3: {broken_links}")
    assert (
        ("note2", "note3") in broken_links
    ), f"Expected ('note2', 'note3') in broken links, but got: {broken_links}"


def test_find_backlinks(linked_notes):
    backlinks = linked_notes.find_backlinks("note2")
    print(f"Backlinks for note2: {backlinks}")
    assert "note1" in backlinks
    backlinks = linked_notes.find_backlinks("note1")
    print(f"Backlinks for note1: {backlinks}")
    assert len(backlinks) == 0
