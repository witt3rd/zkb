import shutil

import pytest
from zkb import ZKB


@pytest.fixture(scope="function")
def zkb(tmp_path) -> ZKB:
    # Create a temporary directory for test data
    test_data_path = tmp_path / "test_data"
    test_data_path.mkdir()

    # Copy test data to the temporary directory
    shutil.copytree("tests/data", test_data_path, dirs_exist_ok=True)

    # Creat a temporary database directory
    test_db_path = tmp_path / "test_db"

    # Create a ZKB instance with the temporary test data
    zkb_instance = ZKB(
        data_dir=str(test_data_path),
        db_dir=str(test_db_path),
    )
    zkb_instance.scan_notes()

    yield zkb_instance

    # Cleanup (optional, as tmp_path is automatically cleaned up by pytest)
    shutil.rmtree(test_data_path)


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


def test_create_note(zkb) -> None:
    filename = "new_test_note"
    content = "This is a test note."
    metadata = {"title": "Test Note", "tags": ["test", "new"]}

    new_note = zkb.create_note(filename, content, metadata)

    assert new_note.filename == filename
    assert new_note.content.strip() == content
    assert new_note.metadata == metadata

    # Check if the file was created
    assert (zkb.notes_path / f"{filename}.md").exists()

    # Check if the note was added to the database
    db_note = zkb.db.get_note_by_filename(filename)
    assert db_note is not None

    # Clean up
    zkb.delete_note(filename)


def test_read_note(zkb) -> None:
    filename = "example_note"
    note = zkb.read_note(filename)

    assert note.filename == filename
    assert "This is an example note" in note.content
    assert note.metadata.get("title") == "Example Note"


def test_update_note(zkb) -> None:
    filename = "example_note"
    new_content = "This is an updated example note."
    new_metadata = {"title": "Updated Example Note", "tags": ["example", "updated"]}

    updated_note = zkb.update_note(filename, new_content, new_metadata)

    assert updated_note.filename == filename
    assert updated_note.content.strip() == new_content
    assert updated_note.metadata == new_metadata

    # Check if the file was updated
    with open(zkb.notes_path / f"{filename}.md", "r", encoding="utf-8") as f:
        file_content = f.read()
    assert new_content in file_content

    # Check if the database was updated
    db_note = zkb.db.get_note_by_filename(filename)
    assert db_note is not None
    assert db_note[3] == new_metadata.get("title")  # Assuming title is at index 3

    # Revert changes
    zkb.update_note(filename, "This is an example note.", {"title": "Example Note"})


def test_delete_note(zkb) -> None:
    filename = "temp_note_for_deletion"
    content = "This note will be deleted."

    # Create a temporary note
    zkb.create_note(filename, content)

    # Delete the note
    zkb.delete_note(filename)

    # Check if the file was deleted
    assert not (zkb.notes_path / f"{filename}.md").exists()

    # Check if the note was removed from the database
    db_note = zkb.db.get_note_by_filename(filename)
    assert db_note is None


def test_search_notes(zkb) -> None:
    query = "example"
    results = zkb.search_notes(query)

    assert len(results) > 0
    assert all(
        query.lower() in note.content.lower()
        or query.lower() in note.metadata.get("title", "").lower()
        for note in results
    )


def test_create_note_with_links(zkb) -> None:
    filename = "note_with_links"
    content = "This note links to [[example_note]] and [[another_note]]."

    new_note = zkb.create_note(filename, content)

    assert len(new_note.links) == 2
    assert {
        "filename": "example_note",
        "display_text": "example_note",
        "heading": None,
    } in new_note.links
    assert {
        "filename": "another_note",
        "display_text": "another_note",
        "heading": None,
    } in new_note.links

    # Check if links were added to the database
    backlinks_example = zkb.find_backlinks("example_note")
    backlinks_another = zkb.find_backlinks("another_note")

    assert filename in backlinks_example
    assert filename in backlinks_another

    # Clean up
    zkb.delete_note(filename)


def test_generate_and_query_qa(zkb):
    # First, create a note with some content
    filename = "qa_test_note"
    content = "The capital of France is Paris. The capital of Italy is Rome."
    zkb.create_note(filename, content)

    # Generate QA pairs
    note = zkb.read_note(filename)
    zkb.generate_and_index_qa_pairs(note)

    # Query the QA knowledge base
    results = zkb.query_qa("What is the capital of France?")

    assert len(results) > 0
    assert any("Paris" in result["answer"] for result in results)

    # Clean up
    zkb.delete_note(filename)


def test_create_existing_note(zkb):
    filename = "existing_note"
    content = "This note already exists."
    zkb.create_note(filename, content)

    with pytest.raises(FileExistsError):
        zkb.create_note(filename, "This should fail.")

    # Clean up
    zkb.delete_note(filename)


def test_read_nonexistent_note(zkb):
    with pytest.raises(FileNotFoundError):
        zkb.read_note("nonexistent_note")


def test_update_nonexistent_note(zkb):
    with pytest.raises(FileNotFoundError):
        zkb.update_note("nonexistent_note", "This should fail.")


def test_delete_nonexistent_note(zkb):
    with pytest.raises(FileNotFoundError):
        zkb.delete_note("nonexistent_note")


def test_search_empty_query(zkb):
    results = zkb.search_notes("")
    assert len(results) == 0


def test_create_note_with_complex_links(zkb):
    filename = "complex_links_note"
    content = "Link with heading: [[example_note#section]]. Link with custom text: [[another_note|Custom Text]]."

    new_note = zkb.create_note(filename, content)

    assert len(new_note.links) == 2
    assert {
        "filename": "example_note",
        "display_text": "example_note",
        "heading": "section",
    } in new_note.links
    assert {
        "filename": "another_note",
        "display_text": "Custom Text",
        "heading": None,
    } in new_note.links

    # Clean up
    zkb.delete_note(filename)
