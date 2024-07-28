# conftest.py

import pytest
from zkb import ZKB


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


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

This is a sample note content.
It contains a [[link]] to another note.
"""


@pytest.fixture
def sample_note(zkb_instance, sample_note_content):
    return zkb_instance.create_note("sample_note", sample_note_content)
