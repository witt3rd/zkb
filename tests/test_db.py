import os

import pytest
from zkb import Database


@pytest.fixture
def db():
    db_file = "test_database.db"
    db = Database(db_file)
    yield db
    db.conn.close()
    os.remove(db_file)


def test_database_initialization(db):
    assert str(db) == "Database(db_file='test_database.db')"
    assert repr(db) == "Database(db_file='test_database.db')"


def test_add_or_update_note_links(db):
    db.add_or_update_note_links(
        "note1.md", "/path/to/note1.md", "Note 1", [("note2.md", "Link to Note 2")]
    )
    note = db.get_note_by_filename("note1.md")
    assert note[1] == "note1.md"
    assert note[2] == "/path/to/note1.md"
    assert note[3] == "Note 1"

    links = db.conn.execute(
        "SELECT * FROM links WHERE from_note = 'note1.md'"
    ).fetchall()
    assert len(links) == 1
    assert links[0][1] == "note2.md"
    assert links[0][2] == "Link to Note 2"


def test_add_entity(db):
    entity_id = db.add_entity("Person", "John Doe")
    assert entity_id > 0
    entities = db.get_entities(entity_type="Person", name="John Doe")
    assert len(entities) == 1
    assert entities[0][1] == "Person"
    assert entities[0][2] == "John Doe"


def test_add_relationship(db):
    entity1_id = db.add_entity("Person", "John Doe")
    entity2_id = db.add_entity("Company", "Acme Inc")
    relationship_id = db.add_relationship(entity1_id, entity2_id, "works_for")
    assert relationship_id > 0

    relationships = db.get_relationships(
        from_type="Person", from_name="John Doe", relationship_type="works_for"
    )
    assert len(relationships) == 1
    assert relationships[0]["from_name"] == "John Doe"
    assert relationships[0]["to_name"] == "Acme Inc"
    assert relationships[0]["relationship_type"] == "works_for"


def test_associate_note_entity(db):
    db.add_or_update_note_links("note1.md", "/path/to/note1.md", "Note 1", [])
    note_id = db.get_note_by_filename("note1.md")[0]
    entity_id = db.add_entity("Person", "John Doe")
    db.associate_note_entity(note_id, entity_id)

    entities = db.get_entities_for_note(note_id)
    assert len(entities) == 1
    assert entities[0][1] == "Person"
    assert entities[0][2] == "John Doe"


def test_get_all_notes(db):
    db.add_or_update_note_links("note1.md", "/path/to/note1.md", "Note 1", [])
    db.add_or_update_note_links("note2.md", "/path/to/note2.md", "Note 2", [])
    notes = db.get_all_notes()
    assert len(notes) == 2
    assert {note[1] for note in notes} == {"note1.md", "note2.md"}


def test_get_orphaned_notes(db):
    db.add_or_update_note_links("note1.md", "/path/to/note1.md", "Note 1", [])
    db.add_or_update_note_links(
        "note2.md", "/path/to/note2.md", "Note 2", [("note1.md", "Link to Note 1")]
    )
    orphaned = db.get_orphaned_notes()
    assert len(orphaned) == 1
    assert orphaned[0][0] == "note2.md"


def test_get_broken_links(db):
    db.add_or_update_note_links(
        "note1.md", "/path/to/note1.md", "Note 1", [("note2.md", "Link to Note 2")]
    )
    broken = db.get_broken_links()
    assert len(broken) == 1
    assert broken[0][0] == "note1.md"
    assert broken[0][1] == "note2.md"


def test_get_backlinks(db):
    db.add_or_update_note_links(
        "note1.md", "/path/to/note1.md", "Note 1", [("note2.md", "Link to Note 2")]
    )
    db.add_or_update_note_links("note2.md", "/path/to/note2.md", "Note 2", [])
    backlinks = db.get_backlinks("note2.md")
    assert len(backlinks) == 1
    assert backlinks[0][0] == "note1.md"


def test_delete_note(db):
    db.add_or_update_note_links(
        "note1.md", "/path/to/note1.md", "Note 1", [("note2.md", "Link to Note 2")]
    )
    db.delete_note("note1.md")
    assert db.get_note_by_filename("note1.md") is None
    assert (
        len(
            db.conn.execute(
                "SELECT * FROM links WHERE from_note = 'note1.md'"
            ).fetchall()
        )
        == 0
    )


def test_get_entity_id(db):
    db.add_entity("Person", "John Doe")
    entity_id = db.get_entity_id("John Doe")
    assert entity_id > 0

    with pytest.raises(ValueError):
        db.get_entity_id("Nonexistent Entity")


def test_get_entity_attributes(db):
    person_id = db.add_entity("Person", "John Doe")
    age_id = db.add_entity("Attribute", "Age")
    db.add_relationship(person_id, age_id, "has_age")

    attributes = db.get_entity_attributes(person_id)
    assert len(attributes) == 1
    assert attributes[0][0] == "has_age"
    assert attributes[0][1] == "Age"


def test_get_entities(db):
    db.add_entity("Person", "John Doe")
    db.add_entity("Person", "Jane Doe")
    db.add_entity("Company", "Acme Inc")

    all_entities = db.get_entities()
    assert len(all_entities) == 3

    person_entities = db.get_entities(entity_type="Person")
    assert len(person_entities) == 2

    john_entity = db.get_entities(name="John Doe")
    assert len(john_entity) == 1
    assert john_entity[0][2] == "John Doe"


def test_get_relationships(db):
    john_id = db.add_entity("Person", "John Doe")
    jane_id = db.add_entity("Person", "Jane Doe")
    acme_id = db.add_entity("Company", "Acme Inc")

    db.add_relationship(john_id, acme_id, "works_for")
    db.add_relationship(jane_id, acme_id, "works_for")
    db.add_relationship(john_id, jane_id, "married_to")

    all_relationships = db.get_relationships()
    assert len(all_relationships) == 3

    work_relationships = db.get_relationships(relationship_type="works_for")
    assert len(work_relationships) == 2

    john_relationships = db.get_relationships(from_name="John Doe")
    assert len(john_relationships) == 2
