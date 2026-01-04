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
            author_formatted = f"<ins>{author_formatted}</ins>"

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
    title = entry.get('title', '').replace('{', '').replace('}', '').replace('---', '—').replace('--', '–')

    # Get optional fields
    journal = entry.get('journal', '')
    booktitle = entry.get('booktitle', '')
    volume = entry.get('volume', '')
    number = entry.get('number', '')
    pages = entry.get('pages', '').replace('--', '–')  # Convert LaTeX dash to en-dash
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


def generate_clinical_trials(entries, output_file='clinical_trials.md'):
    """Generate clinical trials markdown file from BibTeX entries."""

    # Clinical trial metadata: NCT ID -> (name, cancer type)
    trial_info = {
        '03568097': ('PAVE: Intercalated Avelumab plus platinum-based chemotherapy in patients with Extensive-Stage Small-Cell Lung Cancer', 'Lung Cancer'),
        '05372081': ('SNF-CLIMEDIN: Digital support and intervention in patients with advanced NSCLC', 'Lung Cancer'),
        '03311750': ('A-REPEAT: Anti-EGFR re-challenge with chemotherapy in RAS wild-type advanced colorectal cancer', 'Colorectal Cancer'),
        '02512458': ('CabaBone: Cabazitaxel in patients with castration-resistant prostate cancer and osseous metastases', 'Prostate Cancer'),
        '04829890': ('Dose-dense sequential adjuvant chemotherapy in patients with resected high-risk breast cancer', 'Breast Cancer'),
    }

    # Group entries by NCT ID
    trials = defaultdict(list)
    for entry in entries:
        nct = entry.get('nct', '')
        if nct:
            trials[nct].append(entry)

    # Sort publications within each trial by year (descending)
    for nct in trials:
        trials[nct].sort(key=lambda x: int(x.get('year', '0')), reverse=True)

    # Group trials by cancer type
    cancer_types = defaultdict(list)
    for nct, pubs in trials.items():
        if nct in trial_info:
            cancer_type = trial_info[nct][1]
            cancer_types[cancer_type].append((nct, pubs))

    # Order cancer types
    cancer_order = ['Lung Cancer', 'Colorectal Cancer', 'Prostate Cancer', 'Breast Cancer']

    lines = [
        "[[Publications List]](publications.md)  [[CABS Ranked]](ref.md)",
        "",
        "# Clinical Trials",
        "",
        "_Clinical trials coordinated statistically as Senior Statistician at the Hellenic Cooperative Oncology Group (HeCOG)_",
        "",
    ]

    trial_num = len(trials)
    for cancer_type in cancer_order:
        if cancer_type not in cancer_types:
            continue

        lines.append("---")
        lines.append("")
        lines.append(f"## {cancer_type}")
        lines.append("")

        for nct, pubs in cancer_types[cancer_type]:
            trial_name = trial_info.get(nct, ('Unknown Trial', ''))[0]
            lines.append(f"**[{trial_num}]** ClinicalTrials.gov Identifier: **[NCT{nct}](https://clinicaltrials.gov/study/NCT{nct})** - {trial_name}")
            lines.append("")

            # List all publications for this trial
            for entry in pubs:
                formatted = format_entry_apa(entry)
                # Remove the NCT identifier from the formatted string since it's already in the header
                formatted = formatted.replace(f" **(NCT{nct})**", "")
                lines.append(f"   * {formatted}")
                lines.append("")

            trial_num -= 1

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated {output_file} with {len(trials)} clinical trials")


if __name__ == '__main__':
    entries = load_bibtex('publications.bib')
    generate_markdown(entries)
    generate_clinical_trials(entries)
