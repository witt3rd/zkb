import pytest


@pytest.fixture
def ontology_setup(zkb_instance):
    zkb_instance.add_entity("Person", "Alice", {"age": 30, "occupation": "Engineer"})
    zkb_instance.add_entity("Person", "Bob", {"age": 35, "occupation": "Designer"})
    zkb_instance.add_entity("Company", "TechCorp")
    zkb_instance.add_relationship("Alice", "TechCorp", "works_for")
    zkb_instance.add_relationship("Bob", "TechCorp", "works_for")
    return zkb_instance


def test_add_entity(zkb_instance):
    entity_id = zkb_instance.add_entity("Person", "Charlie", {"age": 25})
    assert entity_id > 0


def test_add_relationship(ontology_setup):
    relationship_id = ontology_setup.add_relationship("Alice", "Bob", "knows")
    assert relationship_id > 0


def test_query_entities(ontology_setup):
    persons = ontology_setup.query_entities(entity_type="Person")
    assert len(persons) == 2
    assert any(person["name"] == "Alice" for person in persons)
    assert any(person["name"] == "Bob" for person in persons)


def test_query_relationships(ontology_setup):
    relationships = ontology_setup.query_relationships(
        from_type="Person", relationship_type="works_for"
    )
    assert len(relationships) == 2


def test_query_entity_attributes(ontology_setup):
    alice = ontology_setup.query_entities(name="Alice")[0]
    assert alice["attributes"]["age"] == "30"
    assert alice["attributes"]["occupation"] == "Engineer"


def test_unified_query(ontology_setup):
    ontology_setup.create_note("alice_note", "Alice is a skilled engineer.")
    ontology_setup.scan_notes()
    results = ontology_setup.unified_query("Alice")
    assert len(results) > 0
    assert any("Alice" in str(result) for result in results)
