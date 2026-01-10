#!/usr/bin/env python3
"""
Look up Scimago quartiles for journals in publications.bib
"""

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from collections import defaultdict

# Manual mapping of journals to their Scimago Q1 status (2023/2024 data)
# Based on Scimago Journal Rankings
SCIMAGO_QUARTILES = {
    # Q1 Journals
    "IEEE Transactions on Engineering Management": "Q1",
    "European Journal of Cancer": "Q1",
    "Journal of Clinical Oncology": "Q1",
    "Journal of Thoracic Oncology": "Q1",
    "Annals of Oncology": "Q1",
    "Business Strategy and the Environment": "Q1",
    "International Journal of Operations and Production Management": "Q1",
    "Annals of Operations Research": "Q1",
    "Management International Review": "Q1",
    "Journal of Business Research": "Q1",
    "International Journal of Production Research": "Q1",
    "European Journal of Operational Research": "Q1",
    "International Journal of Hospitality Management": "Q1",
    "Tourism Management": "Q1",
    "Annals of Tourism Research": "Q1",
    "Journal of Travel Research": "Q1",
    "Computers in Human Behavior": "Q1",
    "International Journal of Contemporary Hospitality Management": "Q1",
    "Journal of the American Society for Information Science and Technology": "Q1",
    "Journal of the American Society for Information Science and Technology (JASIST)": "Q1",
    "International Journal of Information Management": "Q1",
    "Information Sciences": "Q1",
    "International Journal of Electronic Commerce": "Q1",
    "ESMO Open": "Q1",
    "Clinical Genitourinary Cancer": "Q1",

    # Q2 Journals
    "Expert Systems": "Q2",
    "Expert Systems with Applications": "Q1",  # Actually Q1
    "Electronic Commerce Research and Applications": "Q1",  # Actually Q1
    "Journal of Documentation": "Q1",  # Actually Q1
    "Health Systems": "Q2",
    "Journal of Air Transport Management": "Q1",  # Actually Q1
    "Benchmarking: An International Journal": "Q2",
    "Library & Information Science Research": "Q2",
    "Online Information Review": "Q2",

    # Q3 Journals
    "The Electronic Library": "Q2",
    "ESMO Gastrointestinal Oncology": "Q2",
    "New Review of Information Networking": "Q3",
    "Program: Electronic library and Information Systems": "Q3",

    # Q4 or unranked
    "International Journal of Knowledge and Web Intelligence": "Q4",
    "International Journal of Metadata, Semantics and Ontologies": "Q4",
    "WSEAS Transactions on Information Science and Applications": "Q4",
    "Data in Brief": "Q3",
    "arXiv Preprint": None,
}


def load_bibtex(filename):
    """Load and parse BibTeX file."""
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(filename, 'r', encoding='utf-8') as f:
        bib_database = bibtexparser.load(f, parser=parser)

    return bib_database


def get_unique_journals(entries):
    """Extract unique journal names from entries."""
    journals = set()
    for entry in entries:
        if entry.get('ENTRYTYPE') == 'article':
            journal = entry.get('journal', '')
            if journal:
                journals.add(journal)
    return sorted(journals)


def count_quartiles(entries):
    """Count publications by Scimago quartile."""
    counts = defaultdict(int)
    q1_journals = []

    for entry in entries:
        if entry.get('ENTRYTYPE') == 'article':
            journal = entry.get('journal', '')
            quartile = SCIMAGO_QUARTILES.get(journal)
            if quartile:
                counts[quartile] += 1
                if quartile == "Q1":
                    q1_journals.append((journal, entry.get('year', '')))

    return counts, q1_journals


def add_scimago_to_bib(bib_database):
    """Add scimago field to entries in bib database."""
    for entry in bib_database.entries:
        if entry.get('ENTRYTYPE') == 'article':
            journal = entry.get('journal', '')
            quartile = SCIMAGO_QUARTILES.get(journal)
            if quartile:
                entry['scimago'] = quartile
    return bib_database


def main():
    bib_database = load_bibtex('publications.bib')

    # Get unique journals
    journals = get_unique_journals(bib_database.entries)
    print("Unique journals found:")
    for j in journals:
        q = SCIMAGO_QUARTILES.get(j, "NOT FOUND")
        print(f"  - {j}: {q}")

    print("\n" + "="*60 + "\n")

    # Count quartiles
    counts, q1_journals = count_quartiles(bib_database.entries)

    total_journal_articles = sum(1 for e in bib_database.entries if e.get('ENTRYTYPE') == 'article')
    total_ranked = sum(counts.values())

    print("Scimago Quartile Summary:")
    print(f"  Q1: {counts['Q1']} publications")
    print(f"  Q2: {counts['Q2']} publications")
    print(f"  Q3: {counts['Q3']} publications")
    print(f"  Q4: {counts['Q4']} publications")
    print(f"  Total ranked: {total_ranked}")
    print(f"  Total journal articles: {total_journal_articles}")

    if total_journal_articles > 0:
        q1_pct = (counts['Q1'] / total_journal_articles) * 100
        print(f"\n  Q1 percentage: {q1_pct:.1f}%")

    print("\nQ1 Publications:")
    for j, y in sorted(q1_journals, key=lambda x: x[1], reverse=True):
        print(f"  - {y}: {j}")

    # Add scimago field to bib
    bib_database = add_scimago_to_bib(bib_database)

    # Write updated bib file
    with open('publications.bib', 'w', encoding='utf-8') as f:
        bibtexparser.dump(bib_database, f)

    print("\nUpdated publications.bib with scimago fields")


if __name__ == '__main__':
    main()
