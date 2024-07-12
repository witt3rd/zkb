import pytest
from zkb import ZKB


@pytest.fixture
def zkb() -> ZKB:
    zkb_instance = ZKB(
        data_dir="tests/data",
        db_path="tests/db/zkb.db",
    )
    zkb_instance.scan_notes()
    return zkb_instance


def test_find_orphaned_notes(zkb) -> None:
    orphans = zkb.find_orphaned_notes()
    expected_orphans = ["example_note"]
    assert (
        orphans == expected_orphans
    ), f"Expected {expected_orphans}, but got {orphans}"


def test_find_broken_links(zkb) -> None:
    broken_links = zkb.find_broken_links()
    expected_broken_links = [("example_note", "yet_another_note")]
    assert (
        broken_links == expected_broken_links
    ), f"Expected {expected_broken_links}, but got {broken_links}"


def test_find_backlinks_example_note(zkb) -> None:
    title = "example_note"
    backlinks = zkb.find_backlinks(title)
    expected_backlinks = []
    assert (
        backlinks == expected_backlinks
    ), f"Expected {expected_backlinks}, but got {backlinks}"


def test_find_backlinks_another_note(zkb) -> None:
    title = "another_note"
    backlinks = zkb.find_backlinks(title)
    expected_backlinks = ["example_note"]
    assert (
        backlinks == expected_backlinks
    ), f"Expected {expected_backlinks}, but got {backlinks}"
