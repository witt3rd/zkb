import pytest
from zkb import ZKB, Database, Note


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def db(temp_dir):
    db_file = temp_dir / "test_database.db"
    db = Database(str(db_file))
    yield db
    db.conn.close()


@pytest.fixture
def zkb_instance(temp_dir):
    data_dir = temp_dir / "data"
    db_dir = temp_dir / "db"
    return ZKB(data_dir=str(data_dir), db_dir=str(db_dir))


@pytest.fixture
def sample_note_content():
    return """---
title: Sample Note
tags: [test, sample]
---
# Sample Note

This is a sample note content.
It contains a [[link]] to another note.
[[has-tag|test]]
[[has-tag|sample]]
"""


@pytest.fixture
def sample_note_file(temp_dir, sample_note_content):
    file_path = temp_dir / "sample_note.md"
    file_path.write_text(sample_note_content)
    return file_path


@pytest.fixture
def sample_note(sample_note_file):
    return Note(sample_note_file)


@pytest.fixture
def populated_zkb(zkb_instance, sample_note_content):
    # Create a few sample notes
    zkb_instance.create_note("Note1", "Content of ZKB Note 1\n[[Note2]]")
    zkb_instance.create_note("Note2", "Content of ZKB Note 2\n[[Note3]]")
    zkb_instance.create_note("Note3", "Content of ZKB Note 3\n[[Note1]]")
    zkb_instance.create_note("Orphan", "This Znote has no links")

    # Add a note with the sample content
    zkb_instance.create_note("Sample", sample_note_content)

    return zkb_instance
