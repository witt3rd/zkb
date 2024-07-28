import json

import pytest


@pytest.fixture
def qa_note(zkb_instance):
    content = """
    # Python Programming

    Python is a high-level programming language.
    It is known for its simplicity and readability.

    ## Key Features
    1. Dynamic typing
    2. Interpreted language
    3. Object-oriented programming support
    """
    return zkb_instance.create_note("python_note", content)


def test_generate_and_index_qa_pairs(zkb_instance, qa_note):
    zkb_instance.generate_and_index_qa_pairs(qa_note)
    results = zkb_instance.query_qa("What is Python?")
    print(json.dumps(results, indent=2))
    assert len(results) > 0
    assert any(
        "high-level programming language" in result["answer"].lower()
        for result in results
    )


def test_query_qa(zkb_instance, qa_note):
    zkb_instance.generate_and_index_qa_pairs(qa_note)
    results = zkb_instance.query_qa("What are some features of Python?")
    print(json.dumps(results, indent=2))
    assert len(results) > 0
    assert any("dynamic typing" in result["answer"].lower() for result in results)


def test_qa_metadata(zkb_instance, qa_note):
    zkb_instance.generate_and_index_qa_pairs(qa_note)
    results = zkb_instance.query_qa("What is Python?")
    print(json.dumps(results, indent=2))
    assert results[0]["metadata"]["note_filename"] == "python_note"
