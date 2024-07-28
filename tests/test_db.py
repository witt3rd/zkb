# test_db.py


def test_database_initialization(db):
    assert str(db) == f"Database(db_file='{db.db_file}')"
    assert repr(db) == f"Database(db_file='{db.db_file}')"


def test_add_or_update_note(db):
    db.add_or_update_note("note1.md", "Note 1", "This is the content of Note 1")
    note = db.get_note("note1.md")
    assert note == ("note1.md", "Note 1", "This is the content of Note 1")


def test_add_or_update_link(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_note("note2.md", "Note 2", "Content 2")
    db.add_or_update_link("note1.md", "note2.md", "reference")

    links = db.get_links("note1.md")
    assert len(links) == 1
    assert links[0] == ("note2.md", "reference", "Note 2", False)


def test_get_note(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    note = db.get_note("note1.md")
    assert note == ("note1.md", "Note 1", "Content 1")

    non_existent = db.get_note("non_existent.md")
    assert non_existent is None


def test_get_links(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_note("note2.md", "Note 2", "Content 2")
    db.add_or_update_note("note3.md", "Note 3", "Content 3")

    db.add_or_update_link("note1.md", "note2.md", "reference")
    db.add_or_update_link("note3.md", "note1.md", "backlink")

    outgoing = db.get_links("note1.md", "outgoing")
    assert len(outgoing) == 1
    assert outgoing[0] == ("note2.md", "reference", "Note 2", False)

    incoming = db.get_links("note1.md", "incoming")
    assert len(incoming) == 1
    assert incoming[0] == ("note3.md", "backlink", "Note 3", False)


def test_search_notes(db):
    db.add_or_update_note("note1.md", "Apple Note", "This note is about apples")
    db.add_or_update_note("note2.md", "Banana Note", "This note is about bananas")

    results = db.search_notes("apple")
    assert len(results) == 1
    assert results[0] == ("note1.md", "Apple Note")


def test_delete_note(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_note("note2.md", "Note 2", "Content 2")
    db.add_or_update_link("note1.md", "note2.md", "reference")

    db.delete_note("note2.md")

    assert db.get_note("note2.md") is None
    links = db.get_links("note1.md")
    assert len(links) == 1
    assert links[0][3] == True  # is_broken should be True


def test_get_broken_links(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_link("note1.md", "non_existent.md", "broken")

    broken_links = db.get_broken_links()
    assert len(broken_links) == 1
    assert broken_links[0] == ("note1.md", "non_existent.md", "broken")


def test_update_broken_links(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_link("note1.md", "note2.md", "initially_broken")

    db.update_broken_links()
    broken_links = db.get_broken_links()
    assert len(broken_links) == 1

    db.add_or_update_note("note2.md", "Note 2", "Content 2")
    db.update_broken_links()
    broken_links = db.get_broken_links()
    assert len(broken_links) == 0


def test_get_all_notes(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_note("note2.md", "Note 2", "Content 2")

    all_notes = db.get_all_notes()
    assert len(all_notes) == 2
    assert set(note[0] for note in all_notes) == {"note1.md", "note2.md"}


def test_get_orphaned_notes(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_note("note2.md", "Note 2", "Content 2")
    db.add_or_update_link("note1.md", "note2.md", "reference")

    orphaned = db.get_orphaned_notes()
    assert len(orphaned) == 1
    assert orphaned[0] == "note1.md"


def test_get_link_types(db):
    db.add_or_update_note("note1.md", "Note 1", "Content 1")
    db.add_or_update_note("note2.md", "Note 2", "Content 2")
    db.add_or_update_link("note1.md", "note2.md", "reference")
    db.add_or_update_link("note2.md", "note1.md", "backlink")

    link_types = db.get_link_types()
    assert set(link_types) == {"reference", "backlink"}
