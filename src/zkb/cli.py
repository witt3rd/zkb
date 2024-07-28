import argparse
import json

from .zkb import ZKB


class CLI:
    def __init__(self, data_dir=None, db_dir=None):
        self.zkb = ZKB(data_dir=data_dir, db_dir=db_dir)

    def scan_notes(self):
        self.zkb.scan_notes()
        print("Notes scanned and database updated.")

    def find_orphaned_notes(self):
        orphans = self.zkb.find_orphaned_notes()
        print("Orphaned Notes:")
        for orphan in orphans:
            print(orphan)

    def find_broken_links(self):
        broken_links = self.zkb.find_broken_links()
        print("Broken Links:")
        for from_file, to_file in broken_links:
            print(f"{from_file} -> {to_file}")

    def find_backlinks(self, filename):
        backlinks = self.zkb.find_backlinks(filename)
        print(f"Backlinks to {filename}:")
        for backlink in backlinks:
            print(backlink)

    def add_entity(self, entity_type, entity_name, attributes):
        entity_id = self.zkb.add_entity(entity_type, entity_name, attributes)
        print(f"Added entity: {entity_type} - {entity_name} (ID: {entity_id})")

    def add_relationship(self, from_entity, to_entity, relationship_type):
        relationship_id = self.zkb.add_relationship(
            from_entity, to_entity, relationship_type
        )
        print(
            f"Added relationship: {from_entity} {relationship_type} {to_entity} (ID: {relationship_id})"
        )

    def query_entities(self, entity_type=None, name=None):
        entities = self.zkb.query_entities(entity_type=entity_type, name=name)
        print(json.dumps(entities, indent=2))

    def query_relationships(self, from_type=None, relationship_type=None):
        relationships = self.zkb.query_relationships(
            from_type=from_type, relationship_type=relationship_type
        )
        print(json.dumps(relationships, indent=2))

    def unified_query(self, query):
        results = self.zkb.unified_query(query)
        print(json.dumps(results, indent=2))

    def generate_and_index_qa_pairs(self, filename):
        note = self.zkb.read_note(filename)
        self.zkb.generate_and_index_qa_pairs(note)
        print(f"Generated and indexed QA pairs for {filename}")

    def query_qa(self, question):
        results = self.zkb.query_qa(question)
        print(json.dumps(results, indent=2))


def main():
    parser = argparse.ArgumentParser(description="ZKB CLI")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/",
        help="Directory containing markdown notes",
    )
    parser.add_argument(
        "--db-dir",
        type=str,
        default="db/",
        help="Directory for the database",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    subparsers.add_parser("scan", help="Scan notes and update the database")
    subparsers.add_parser("find-orphans", help="Find orphaned notes")
    subparsers.add_parser("find-broken-links", help="Find broken links")

    backlinks_parser = subparsers.add_parser(
        "find-backlinks", help="Find backlinks to a note"
    )
    backlinks_parser.add_argument(
        "filename", type=str, help="Filename of the note to find backlinks for"
    )

    add_entity_parser = subparsers.add_parser(
        "add-entity", help="Add a new entity to the ontology"
    )
    add_entity_parser.add_argument("entity_type", type=str, help="Type of the entity")
    add_entity_parser.add_argument("entity_name", type=str, help="Name of the entity")
    add_entity_parser.add_argument(
        "--attributes",
        type=json.loads,
        default={},
        help="JSON string of entity attributes",
    )

    add_relationship_parser = subparsers.add_parser(
        "add-relationship", help="Add a new relationship to the ontology"
    )
    add_relationship_parser.add_argument(
        "from_entity", type=str, help="Name of the source entity"
    )
    add_relationship_parser.add_argument(
        "to_entity", type=str, help="Name of the target entity"
    )
    add_relationship_parser.add_argument(
        "relationship_type", type=str, help="Type of the relationship"
    )

    query_entities_parser = subparsers.add_parser(
        "query-entities", help="Query entities in the ontology"
    )
    query_entities_parser.add_argument(
        "--entity_type", type=str, help="Type of entities to query"
    )
    query_entities_parser.add_argument(
        "--name", type=str, help="Name of the entity to query"
    )

    query_relationships_parser = subparsers.add_parser(
        "query-relationships", help="Query relationships in the ontology"
    )
    query_relationships_parser.add_argument(
        "--from_type", type=str, help="Type of the source entity"
    )
    query_relationships_parser.add_argument(
        "--relationship_type", type=str, help="Type of relationship to query"
    )

    unified_query_parser = subparsers.add_parser(
        "unified-query", help="Perform a unified query across notes and ontology"
    )
    unified_query_parser.add_argument("query", type=str, help="Query string")

    generate_qa_parser = subparsers.add_parser(
        "generate-qa", help="Generate and index QA pairs for a note"
    )
    generate_qa_parser.add_argument(
        "filename", type=str, help="Filename of the note to generate QA pairs for"
    )

    query_qa_parser = subparsers.add_parser("query-qa", help="Query the QA system")
    query_qa_parser.add_argument(
        "question", type=str, help="Question to ask the QA system"
    )

    args = parser.parse_args()

    cli = CLI(data_dir=args.data_dir, db_dir=args.db_dir)

    if args.command == "scan":
        cli.scan_notes()
    elif args.command == "find-orphans":
        cli.find_orphaned_notes()
    elif args.command == "find-broken-links":
        cli.find_broken_links()
    elif args.command == "find-backlinks":
        cli.find_backlinks(args.filename)
    elif args.command == "add-entity":
        cli.add_entity(args.entity_type, args.entity_name, args.attributes)
    elif args.command == "add-relationship":
        cli.add_relationship(args.from_entity, args.to_entity, args.relationship_type)
    elif args.command == "query-entities":
        cli.query_entities(args.entity_type, args.name)
    elif args.command == "query-relationships":
        cli.query_relationships(args.from_type, args.relationship_type)
    elif args.command == "unified-query":
        cli.unified_query(args.query)
    elif args.command == "generate-qa":
        cli.generate_and_index_qa_pairs(args.filename)
    elif args.command == "query-qa":
        cli.query_qa(args.question)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
