import argparse
from typing import Optional

from .zkb import ZKB


class CLI:
    def __init__(self, notes_dir: Optional[str] = None, db_dir: Optional[str] = None):
        self.zkb = ZKB(notes_dir=notes_dir, db_dir=db_dir)

    def create_note(self, title, content):
        try:
            note = self.zkb.create_note(title, content)
            print(f"Note created: {note.filename}")
        except FileExistsError:
            print(f"Error: Note '{title}' already exists")

    def read_note(self, filename):
        try:
            note = self.zkb.read_note(filename)
            print(f"Title: {note.title}")
            print(f"Content:\n{note.content}")
        except FileNotFoundError:
            print(f"Error: Note '{filename}' not found")

    def update_note(self, filename, new_content):
        try:
            note = self.zkb.update_note(filename, new_content)
            print(f"Note updated: {note.filename}")
        except FileNotFoundError:
            print(f"Error: Note '{filename}' not found")

    def delete_note(self, filename):
        try:
            self.zkb.delete_note(filename)
            print(f"Note deleted: {filename}")
        except FileNotFoundError:
            print(f"Error: Note '{filename}' not found")

    def search_notes(self, query):
        results = self.zkb.search_notes(query)
        if results:
            print("Search results:")
            for result in results:
                print(f"- {result['filename']}: {result['title']}")
                if result.get("link_type"):
                    print(f"  (Referenced as: {result['link_type']})")
        else:
            print("No r esults found")

    def get_incoming_links(self, filename):
        links = self.zkb.get_incoming_links(filename)
        if links:
            print(f"Incoming links for {filename}:")
            for link in links:
                if link.alias == filename:
                    print(f"o: {link.source} {link.target} {link.alias}")
                else:
                    print(f"p: {link.source} {link.target} {link.alias}")
        else:
            print(f"No incoming links found for {filename}")

    def get_outgoing_links(self, filename):
        links = self.zkb.get_outgoing_links(filename)
        if links:
            print(f"Outgoing links for {filename}:")
            for link in links:
                print(f"s: {link.source} {link.target} {link.alias}")
        else:
            print(f"No outgoing links found for {filename}")

    def scan_notes(self):
        count = self.zkb.scan_notes()
        print(f"{count} note{'s' if count > 1 else ''} scanned and database updated")

    def get_all_notes(self):
        notes = self.zkb.get_all_notes()
        if notes:
            print("All notes:")
            for note in notes:
                print(f"- {note['filename']}: {note['title']}")
        else:
            print("No notes found")

    def get_orphaned_notes(self):
        orphans = self.zkb.get_orphaned_notes()
        if orphans:
            print("Orphaned notes:")
            for orphan in orphans:
                print(f"- {orphan}")
        else:
            print("No orphaned notes found")

    def get_broken_links(self):
        broken_links = self.zkb.get_broken_links()
        if broken_links:
            print("Broken links:")
            for link in broken_links:
                print(f"- {link.from_note} -> {link.to_note} ({link.alias})")
        else:
            print("No broken links found")


def main():
    parser = argparse.ArgumentParser(description="ZKB CLI")
    parser.add_argument("--notes-dir", type=str, help="Directory for storing notes")
    parser.add_argument("--db-dir", type=str, help="Directory for storing the database")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Create note
    create_parser = subparsers.add_parser("create", help="Create a new note")
    create_parser.add_argument("title", help="Title of the note")
    create_parser.add_argument("content", help="Content of the note")

    # Read note
    read_parser = subparsers.add_parser("read", help="Read a note")
    read_parser.add_argument("filename", help="Filename of the note to read")

    # Update note
    update_parser = subparsers.add_parser("update", help="Update an existing note")
    update_parser.add_argument("filename", help="Filename of the note to update")
    update_parser.add_argument("new_content", help="New content for the note")

    # Delete note
    delete_parser = subparsers.add_parser("delete", help="Delete a note")
    delete_parser.add_argument("filename", help="Filename of the note to delete")

    # Search notes
    search_parser = subparsers.add_parser("search", help="Search for notes")
    search_parser.add_argument("query", help="Search query")

    # Get incoming links
    incoming_parser = subparsers.add_parser(
        "incoming", help="Get incoming links for a note"
    )
    incoming_parser.add_argument("filename", help="Filename of the note")

    # Get outgoing links
    outgoing_parser = subparsers.add_parser(
        "outgoing", help="Get outgoing links for a note"
    )
    outgoing_parser.add_argument("filename", help="Filename of the note")

    # Scan notes
    subparsers.add_parser("scan", help="Scan all notes and update the database")

    # Get orphaned notes
    subparsers.add_parser("orphans", help="Get orphaned notes")

    # Get broken links
    subparsers.add_parser("broken", help="Get broken links")

    # Get all notes
    subparsers.add_parser("all", help="Get all notes")

    args = parser.parse_args()

    cli = CLI(notes_dir=args.notes_dir, db_dir=args.db_dir)

    if args.command == "create":
        cli.create_note(args.title, args.content)
    elif args.command == "read":
        cli.read_note(args.filename)
    elif args.command == "update":
        cli.update_note(args.filename, args.new_content)
    elif args.command == "delete":
        cli.delete_note(args.filename)
    elif args.command == "search":
        cli.search_notes(args.query)
    elif args.command == "incoming":
        cli.get_incoming_links(args.filename)
    elif args.command == "outgoing":
        cli.get_outgoing_links(args.filename)
    elif args.command == "scan":
        cli.scan_notes()
    elif args.command == "all":
        cli.get_all_notes()
    elif args.command == "orphans":
        cli.get_orphaned_notes()
    elif args.command == "broken":
        cli.get_broken_links()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
