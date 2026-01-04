#!/usr/bin/env python3
"""
Generate publications.md from publications.bib using APA-style formatting.

Usage:
    python generate_publications.py

This script reads publications.bib and generates a formatted markdown file
with publications organized by category and numbered in reverse order.
"""

import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode
from collections import defaultdict
import re


def format_authors_apa(authors_str, highlight_author="Korfiatis"):
    """Format authors in APA style: Last, F.I., Last, F.I., & Last, F.I.

    Underlines the specified author name for highlighting.
    """
    if not authors_str:
        return ""

    # Split by ' and ' to get individual authors
    authors = [a.strip() for a in authors_str.replace('\n', ' ').split(' and ')]
    formatted = []

    for author in authors:
        # Handle "Last, First" format
        if ',' in author:
            parts = author.split(',', 1)
            last = parts[0].strip()
            first = parts[1].strip() if len(parts) > 1 else ""
        else:
            # Handle "First Last" format
            parts = author.strip().split()
            if len(parts) >= 2:
                last = parts[-1]
                first = ' '.join(parts[:-1])
            else:
                last = author
                first = ""

        # Get initials
        if first:
            initials = '.'.join([n[0].upper() for n in first.split() if n]) + '.'
            author_formatted = f"{last}, {initials}"
        else:
            author_formatted = last

        # Highlight the specified author with underline
        if highlight_author and highlight_author.lower() in last.lower():
            author_formatted = f"<u>{author_formatted}</u>"

        formatted.append(author_formatted)

    # APA style: use & before last author
    if len(formatted) > 1:
        return ', '.join(formatted[:-1]) + ', & ' + formatted[-1]
    return formatted[0] if formatted else ""


def format_entry_apa(entry):
    """Format a single BibTeX entry in APA style."""
    entry_type = entry.get('ENTRYTYPE', 'article').lower()

    authors = format_authors_apa(entry.get('author', ''))
    year = entry.get('year', '')
    title = entry.get('title', '').replace('{', '').replace('}', '')

    # Get optional fields
    journal = entry.get('journal', '')
    booktitle = entry.get('booktitle', '')
    volume = entry.get('volume', '')
    number = entry.get('number', '')
    pages = entry.get('pages', '')
    publisher = entry.get('publisher', '')
    address = entry.get('address', '')
    doi = entry.get('doi', '')
    url = entry.get('url', '')
    note = entry.get('note', '')
    school = entry.get('school', '')
    institution = entry.get('institution', '')
    editor = entry.get('editor', '')
    cabs = entry.get('cabs', '')  # Custom field for CABS ranking
    nct = entry.get('nct', '')  # Custom field for clinical trial ID

    result = f"{authors} ({year}). {title}."

    if entry_type == 'article':
        if journal:
            result += f" *{journal}*"
            if volume:
                result += f", {volume}"
                if number:
                    result += f"({number})"
            if pages:
                result += f", {pages}"
            result += "."

    elif entry_type == 'inproceedings' or entry_type == 'conference':
        if booktitle:
            result += f" *{booktitle}*"
            if pages:
                result += f", {pages}"
            result += "."
        if address:
            result += f" {address}."

    elif entry_type == 'incollection' or entry_type == 'inbook':
        if editor:
            ed_formatted = format_authors_apa(editor)
            result += f" In {ed_formatted} (Ed" + ("s" if ' and ' in editor else "") + f".), *{booktitle}*"
        elif booktitle:
            result += f" In *{booktitle}*"
        if pages:
            result += f", {pages}"
        result += "."
        if publisher:
            result += f" {publisher}."

    elif entry_type == 'phdthesis' or entry_type == 'mastersthesis':
        if address:
            result += f" {address}:"
        if school:
            result += f" *{school}*"
            if pages:
                result += f", {pages} p."
            else:
                result += "."
        if note:
            result += f" ({note})"

    elif entry_type == 'techreport':
        if institution:
            result += f" *{institution}*."
        if number:
            result += f" ({number})."

    elif entry_type == 'misc':
        if journal:
            result += f" *{journal}*"
            if volume:
                result += f", {volume}"
            if pages:
                result += f", {pages}"
            result += "."
        if note:
            result += f" {note}"

    # Add CABS ranking if present
    if cabs:
        result += f" **(CABS {cabs})**"

    # Add NCT identifier if present
    if nct:
        result += f" **(NCT{nct})**"

    # Add URL links if present
    urls = []
    if url:
        urls.append(f"[{entry.get('urlname', 'Link')}]({url})")
    url2 = entry.get('url2', '')
    if url2:
        urls.append(f"[{entry.get('urlname2', 'Link')}]({url2})")
    if urls:
        result += " " + " | ".join(urls)

    return result


def load_bibtex(filename):
    """Load and parse BibTeX file."""
    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode

    with open(filename, 'r', encoding='utf-8') as f:
        bib_database = bibtexparser.load(f, parser=parser)

    return bib_database.entries


def generate_markdown(entries, output_file='publications.md'):
    """Generate markdown file from BibTeX entries."""

    # Organize entries by category
    categories = defaultdict(list)

    for entry in entries:
        cat = entry.get('category', 'other').lower()
        categories[cat].append(entry)

    # Sort each category by year (descending)
    for cat in categories:
        categories[cat].sort(key=lambda x: int(x.get('year', '0')), reverse=True)

    # Category order and titles
    category_order = [
        ('software', 'Released Software'),
        ('dissertation', 'Dissertations'),
        ('journal', 'Journal Articles'),
        ('conference', 'Conference Proceedings'),
        ('book', 'Contributions in Books and Edited Volumes'),
        ('deliverable', 'Deliverables and Project Related Publications'),
    ]

    lines = [
        "[[CABS Ranked]](ref.md)  [[Clinical Trials]](clinical_trials.md)",
        "",
        "# Full List of Publications (Chronological Order)",
        "",
        "_Note: CABS denotes classification from CABS Ranking_",
        "",
    ]

    for cat_key, cat_title in category_order:
        if cat_key not in categories:
            continue

        lines.append("---")
        lines.append("")
        lines.append(f"## {cat_title}")
        lines.append("")

        cat_entries = categories[cat_key]
        total = len(cat_entries)

        for i, entry in enumerate(cat_entries):
            num = total - i
            formatted = format_entry_apa(entry)
            lines.append(f"**[{num}]** {formatted}")
            lines.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated {output_file} with {len(entries)} entries")


if __name__ == '__main__':
    entries = load_bibtex('publications.bib')
    generate_markdown(entries)
