# ZKB: Zettelkasten-inspired Knowledge Base with EBR

A Zettelkasten-inspired knowledge base with Embeddings-Based Retrieval

[![PyPI version](https://badge.fury.io/py/zkb.svg)](https://badge.fury.io/py/zkb)
[![CI](https://github.com/witt3rd/zkb/actions/workflows/ci.yml/badge.svg)](https://github.com/witt3rd/zkb/actions/workflows/ci.yml)
[![Rye](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/rye/main/artwork/badge.json)](https://rye.astral.sh)
[![GitHub license](https://img.shields.io/github/license/witt3rd/zkb.svg)](https://github.com/witt3rd/zkbe/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/witt3rd/zkb.svg)](https://github.com/witt3rd/zkb/issues)
[![GitHub stars](https://img.shields.io/github/stars/witt3rd/zkb.svg)](https://github.com/witt3rd/zkb/stargazers)
[![Twitter](https://img.shields.io/twitter/url/https/twitter.com/dt_public.svg?style=social&label=Follow%20%40dt_public)](https://twitter.com/dt_public)

ZKB is a command-line tool for managing a Zettelkasten-inspired knowledge base of markdown notes. It helps you organize, link, and analyze your notes efficiently, while also providing powerful question-answering capabilities through Embeddings-Based Retrieval (EBR).

## Features

- Scan and index markdown notes
- Find orphaned notes (notes not linked to by any other note)
- Detect broken links between notes
- Find backlinks to a specific note
- Create, read, update, and delete notes
- Search notes based on content or metadata
- Generate and index question-answer pairs from notes
- Query the knowledge base using natural language questions (EBR)

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/witt3rd/zkb.git
   ```

2. Install dependencies:

   ```sh
   pip install .
   ```

## Usage

```sh
python -m zkb.cli [--data-dir DATA_DIR] [--db-path DB_PATH] {command} [args]
```

Available commands:

- `scan`: Scan notes and update the database
- `find-orphans`: Find orphaned notes
- `find-broken-links`: Find broken links
- `find-backlinks {filename}`: Find backlinks to a specific note

## Configuration

You can set the following environment variables or use a `.env` file:

- `DATA_DIR`: Directory containing markdown notes (default: "data/")
- `DB_DIR`: Directory for the SQLite database (default: "db/")

## Embeddings-Based Retrieval (EBR)

ZKB incorporates Embeddings-Based Retrieval (EBR) through the [qa-store](https://github.com/witt3rd/qa-store) library. This feature enables:

1. Automatic generation of question-answer pairs from your notes.
2. Indexing of these pairs using embeddings for efficient retrieval.
3. Natural language querying of your knowledge base.

EBR allows you to ask questions about your notes and receive relevant answers, even if the exact wording doesn't match. This powerful feature enhances the discoverability and utility of your knowledge base.

## Design

### How it works

1. ZKB scans markdown files in the specified directory.
2. It parses each note, extracting metadata, content, and links.
3. The extracted information is stored in an SQLite database.
4. Question-answer pairs are generated from the notes and indexed using embeddings.
5. Various operations can be performed on the indexed data, including EBR-based querying.

### Key Operations

1. **Scanning notes**: Parses markdown files, extracts metadata and links, and updates the database.
2. **Finding orphaned notes**: Identifies notes that are not linked to by any other note.
3. **Detecting broken links**: Finds links that point to non-existent notes.
4. **Finding backlinks**: Discovers which notes link to a specific note.
5. **Creating/Reading/Updating/Deleting notes**: Manages individual notes in the knowledge base.
6. **Searching notes**: Finds notes based on content or metadata.
7. **Generating and indexing QA pairs**: Creates question-answer pairs from notes and indexes them for retrieval.
8. **Querying the knowledge base**: Uses natural language questions to retrieve relevant information from the notes.

### Data Structures

1. **Note**: Represents a markdown note with properties like filename, full path, metadata, content, and links.
2. **Database**: SQLite database with two main tables:
   - `notes`: Stores information about each note (id, filename, full_path, title)
   - `links`: Stores links between notes (from_note, to_note, display_text)
3. **QA Knowledge Base**: Stores and indexes question-answer pairs generated from notes.

### Components

1. **ZKB**: Main class that orchestrates the operations.
2. **Database**: Handles database operations.
3. **Note**: Represents and parses individual markdown notes.
4. **CLI**: Provides the command-line interface.
5. **QuestionAnswerKB**: Manages the generation, indexing, and retrieval of QA pairs.

## TODO

We're constantly working to improve zkb. Here are some features and enhancements we're planning to implement:

- [ ] Implement a web-based user interface
- [ ] Add support for tags and categories
- [ ] Improve the natural language processing capabilities
- [ ] Implement a plugin system for extensibility
- [ ] Add visualization tools for exploring the knowledge graph

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

Donald Thompson - [@dt_public](https://twitter.com/dt_public) - <witt3rd@witt3rd.com>

Project Link: [https://github.com/witt3rd/zkb](https://github.com/witt3rd/zkb)
