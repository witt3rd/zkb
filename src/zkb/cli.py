import argparse

from .zkb import ZKB


class CLI:
    def __init__(self, data_dir=None, db_path=None):
        self.zkb = ZKB(data_dir=data_dir, db_path=db_path)

    def scan_notes(self):
        self.zkb.scan_notes()

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


def main():
    parser = argparse.ArgumentParser(description="ZKB CLI")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/",
        help="Directory containing markdown notes",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default="db/zkb.db",
        help="Path to the SQLite database",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scan notes command
    subparsers.add_parser("scan", help="Scan notes and update the database")

    # Find orphaned notes command
    subparsers.add_parser("find-orphans", help="Find orphaned notes")

    # Find broken links command
    subparsers.add_parser("find-broken-links", help="Find broken links")

    # Find backlinks command
    backlinks_parser = subparsers.add_parser(
        "find-backlinks", help="Find backlinks to a note"
    )
    backlinks_parser.add_argument(
        "filename", type=str, help="Filename of the note to find backlinks for"
    )

    args = parser.parse_args()

    cli = CLI(data_dir=args.data_dir, db_path=args.db_path)

    if args.command == "scan":
        cli.scan_notes()
    elif args.command == "find-orphans":
        cli.find_orphaned_notes()
    elif args.command == "find-broken-links":
        cli.find_broken_links()
    elif args.command == "find-backlinks":
        cli.find_backlinks(args.filename)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
