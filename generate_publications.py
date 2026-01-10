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
                result += f", Vol. {volume}"
                if number:
                    result += f", No. {number}"
            if pages:
                result += f", pp. {pages}"
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
    if doi:
        urls.append(f"[DOI](https://doi.org/{doi})")
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
        ('workingpaper', 'Working Papers'),
        ('conference', 'Conference Proceedings'),
        ('book', 'Contributions in Books and Edited Volumes'),
        ('deliverable', 'Deliverables and Project Related Publications'),
    ]

    lines = [
        "[[CABS Ranked]](ref.md)  [[By Year]](by_year.md)  [[Clinical Trials]](clinical_trials.md)  [[Policy Impact]](policy_citations.md)",
        "",
        "# Full List of Publications (Chronological Order)",
        "",
        "_Note: CABS denotes classification ranked according to the Chartered Association of Business Schools (CABS) Academic Journal Guide_",
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

    # Clinical trial metadata: NCT ID -> (name, cancer type, phase)
    trial_info = {
        '03568097': ('PAVE: Intercalated Avelumab plus platinum-based chemotherapy in patients with Extensive-Stage Small-Cell Lung Cancer', 'Lung Cancer', 'Phase II'),
        '05372081': ('SNF-CLIMEDIN: Digital support and intervention in patients with advanced NSCLC', 'Lung Cancer', 'Non-interventional'),
        '03311750': ('A-REPEAT: Anti-EGFR re-challenge with chemotherapy in RAS wild-type advanced colorectal cancer', 'Colorectal Cancer', 'Phase II'),
        '02512458': ('CabaBone: Cabazitaxel in patients with castration-resistant prostate cancer and osseous metastases', 'Prostate Cancer', 'Translational'),
        '04829890': ('Dose-dense sequential adjuvant chemotherapy in patients with resected high-risk breast cancer', 'Breast Cancer', 'Phase III'),
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
        "[[Publications List]](publications.md)  [[CABS Ranked]](ref.md)  [[By Year]](by_year.md)  [[Policy Impact]](policy_citations.md)",
        "",
        "# Clinical Trials",
        "",
        "_The following is a list of Clinical trials by therapeutic areas which I have coordinated as Senior Statistician at the Hellenic Cooperative Oncology Group (HeCOG). Clinicaltrials.gov identifier in brackets_",
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
            trial_data = trial_info.get(nct, ('Unknown Trial', '', ''))
            trial_name = trial_data[0]
            trial_phase = trial_data[2] if len(trial_data) > 2 else ''
            phase_str = f" [{trial_phase}]" if trial_phase else ""
            lines.append(f"**[{trial_num}]** ClinicalTrials.gov Identifier: **[NCT{nct}](https://clinicaltrials.gov/study/NCT{nct})** - {trial_name}{phase_str}")
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


def generate_cabs_ranked(entries, output_file='ref.md'):
    """Generate CABS ranked publications markdown file from BibTeX entries."""

    # Filter entries with CABS ranking
    cabs_entries = [e for e in entries if e.get('cabs', '')]

    # Group by CABS ranking
    cabs_groups = defaultdict(list)
    for entry in cabs_entries:
        cabs_rank = entry.get('cabs', '')
        cabs_groups[cabs_rank].append(entry)

    # Sort each group by year (descending)
    for rank in cabs_groups:
        cabs_groups[rank].sort(key=lambda x: int(x.get('year', '0')), reverse=True)

    # CABS rankings in order (highest first)
    cabs_order = ['4', '3', '2', '1']

    lines = [
        "[[Publications List]](publications.md)  [[By Year]](by_year.md)  [[Clinical Trials]](clinical_trials.md)  [[Policy Impact]](policy_citations.md)",
        "",
        "# CABS Ranked Publications",
        "",
        "_Publications ranked according to the Chartered Association of Business Schools (CABS) Academic Journal Guide_",
        "",
    ]

    for rank in cabs_order:
        if rank not in cabs_groups:
            continue

        lines.append("---")
        lines.append("")
        lines.append(f"## CABS {rank}")
        lines.append("")

        rank_entries = cabs_groups[rank]
        total = len(rank_entries)

        for i, entry in enumerate(rank_entries):
            num = total - i
            formatted = format_entry_apa(entry)
            # Remove the CABS indicator since it's already in the section header
            formatted = formatted.replace(f" **(CABS {rank})**", "")
            lines.append(f"**[{num}]** {formatted}")
            lines.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated {output_file} with {len(cabs_entries)} CABS ranked publications")


def generate_by_year(entries, output_file='by_year.md'):
    """Generate publications grouped by year markdown file from BibTeX entries."""

    # Group entries by year
    year_groups = defaultdict(list)
    for entry in entries:
        year = entry.get('year', 'Unknown')
        year_groups[year].append(entry)

    # Sort years descending
    sorted_years = sorted(year_groups.keys(), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)

    lines = [
        "[[Publications List]](publications.md)  [[CABS Ranked]](ref.md)  [[Clinical Trials]](clinical_trials.md)  [[Policy Impact]](policy_citations.md)",
        "",
        "# Publications by Year",
        "",
        "_All publications grouped by year of publication_",
        "",
    ]

    for year in sorted_years:
        lines.append("---")
        lines.append("")
        lines.append(f"## {year}")
        lines.append("")

        year_entries = year_groups[year]
        total = len(year_entries)
        for i, entry in enumerate(year_entries):
            num = total - i
            formatted = format_entry_apa(entry)
            lines.append(f"**[{num}]** {formatted}")
            lines.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated {output_file} with publications across {len(sorted_years)} years")


def generate_policy_citations(entries, output_file='policy_citations.md'):
    """Generate policy and patent citations markdown file from BibTeX entries."""

    # Filter entries with policy citations or patent citations
    impact_entries = [e for e in entries if e.get('policycitation', '') or e.get('patentcitation', '')]

    # Sort by publication year (most recent first)
    def get_publication_year(entry):
        try:
            return int(entry.get('year', '0'))
        except ValueError:
            return 0

    impact_entries.sort(key=get_publication_year, reverse=True)

    # Count total citations
    total_policy = 0
    total_patents = 0
    for entry in impact_entries:
        citations_str = entry.get('policycitation', '')
        if citations_str:
            total_policy += len(citations_str.split(';;'))
        patent_str = entry.get('patentcitation', '')
        if patent_str:
            total_patents += len(patent_str.split(';;'))

    lines = [
        "[[Publications List]](publications.md)  [[CABS Ranked]](ref.md)  [[By Year]](by_year.md)  [[Clinical Trials]](clinical_trials.md)",
        "",
        "# Policy Impact",
        "",
        "_Research cited in policy documents, governmental/intergovernmental publications, and patents_",
        "",
        "---",
        "",
    ]

    def format_coauthors(authors_str):
        """Format co-authors, excluding Korfiatis."""
        if not authors_str:
            return ""
        authors = [a.strip() for a in authors_str.replace('\n', ' ').split(' and ')]
        coauthors = []
        for author in authors:
            if 'korfiatis' not in author.lower():
                # Handle "Last, First" format
                if ',' in author:
                    parts = author.split(',', 1)
                    last = parts[0].strip().replace('{', '').replace('}', '').replace("'", '').replace('\\', '')
                    first = parts[1].strip() if len(parts) > 1 else ""
                else:
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
                    coauthors.append(f"{last}, {initials}")
                else:
                    coauthors.append(last)
        if not coauthors:
            return ""
        if len(coauthors) == 1:
            return coauthors[0]
        return ', '.join(coauthors[:-1]) + ' and ' + coauthors[-1]

    total = len(impact_entries)
    for i, entry in enumerate(impact_entries):
        num = total - i
        # Get publication details
        title = entry.get('title', '').replace('{', '').replace('}', '')
        journal = entry.get('journal', '')
        year = entry.get('year', '')
        cabs = entry.get('cabs', '')
        doi = entry.get('doi', '')
        authors = entry.get('author', '')

        cabs_str = f" (CABS {cabs})" if cabs else ""
        doi_link = f" [DOI](https://doi.org/{doi})" if doi else ""
        coauthors = format_coauthors(authors)
        coauthor_str = f", co-authored with {coauthors}" if coauthors else ""

        # Parse all policy citations (multiple separated by ;;)
        citations_str = entry.get('policycitation', '')
        if citations_str:
            citations = citations_str.split(';;')
            for citation in citations:
                parts = citation.split('|')
                if len(parts) >= 3:
                    cite_title = parts[0].strip()
                    cite_source = parts[1].strip()
                    cite_year = parts[2].strip()
                else:
                    cite_title = citation.strip()
                    cite_source = ""
                    cite_year = ""
                lines.append(f"**[{num}]** The {year} paper «{title}»{coauthor_str}, published in *{journal}*{cabs_str}, has been cited in the document «{cite_title}» ({cite_year}) by *{cite_source}*.{doi_link}")
                lines.append("")

        # Parse all patent citations (format: title|company|patent_id|year)
        patent_str = entry.get('patentcitation', '')
        if patent_str:
            patents = patent_str.split(';;')
            for patent in patents:
                parts = patent.split('|')
                if len(parts) >= 4:
                    patent_title = parts[0].strip()
                    patent_company = parts[1].strip()
                    patent_id = parts[2].strip()
                    patent_year = parts[3].strip()
                else:
                    patent_title = patent.strip()
                    patent_company = ""
                    patent_id = ""
                    patent_year = ""
                lines.append(f"**[{num}]** The {year} paper «{title}»{coauthor_str}, published in *{journal}*{cabs_str}, has been cited as Prior Art in the *{patent_company}* patent titled «{patent_title}» with USPTO assignment code [{patent_id}](https://patents.google.com/patent/{patent_id}) ({patent_year}).{doi_link}")
                lines.append("")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated {output_file} with {total_policy} policy citations and {total_patents} patent citations across {len(impact_entries)} publications")


def format_authors_latex(authors_str, highlight_author="Korfiatis"):
    """Format authors in APA style for LaTeX: Last, F.I., Last, F.I., \\& Last, F.I.

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

        # Escape LaTeX special characters
        author_formatted = author_formatted.replace('&', '\\&')

        # Highlight the specified author with underline
        if highlight_author and highlight_author.lower() in last.lower():
            author_formatted = f"\\underline{{{author_formatted}}}"

        formatted.append(author_formatted)

    # APA style: use \& before last author
    if len(formatted) > 1:
        return ', '.join(formatted[:-1]) + ', \\& ' + formatted[-1]
    return formatted[0] if formatted else ""


def escape_latex(text):
    """Escape LaTeX special characters in text."""
    if not text:
        return text
    # Order matters - escape backslash first
    text = text.replace('&', '\\&')
    text = text.replace('%', '\\%')
    text = text.replace('_', '\\_')
    text = text.replace('#', '\\#')
    text = text.replace('$', '\\$')
    return text


def format_entry_latex(entry):
    """Format a single BibTeX entry in APA style for LaTeX."""
    entry_type = entry.get('ENTRYTYPE', 'article').lower()

    authors = format_authors_latex(entry.get('author', ''))
    year = entry.get('year', '')
    title = entry.get('title', '').replace('{', '').replace('}', '').replace('---', '---').replace('--', '--')
    # Escape LaTeX special characters in title
    title = escape_latex(title)

    # Get optional fields
    journal = entry.get('journal', '')
    booktitle = entry.get('booktitle', '')
    volume = escape_latex(entry.get('volume', ''))
    number = escape_latex(entry.get('number', ''))
    pages = entry.get('pages', '').replace('--', '--')
    publisher = entry.get('publisher', '')
    address = entry.get('address', '')
    doi = entry.get('doi', '')
    url = entry.get('url', '')
    editor = entry.get('editor', '')
    cabs = entry.get('cabs', '')  # CABS ranking
    scimago = entry.get('scimago', '')  # Scimago quartile

    # Escape special chars in journal/booktitle
    journal = escape_latex(journal)
    booktitle = escape_latex(booktitle)

    result = f"{authors} ({year}). {title}."

    if entry_type == 'article':
        if journal:
            result += f" \\textit{{{journal}}}"
            if volume:
                result += f", Vol. {volume}"
                if number:
                    result += f", No. {number}"
            if pages:
                result += f", pp. {pages}"
            result += "."

    elif entry_type == 'inproceedings' or entry_type == 'conference':
        if booktitle:
            result += f" \\textit{{{booktitle}}}"
            if pages:
                result += f", {pages}"
            result += "."
        if address:
            result += f" {address}."

    elif entry_type == 'incollection' or entry_type == 'inbook':
        if editor:
            ed_formatted = format_authors_latex(editor, highlight_author=None)
            result += f" In {ed_formatted} (Ed" + ("s" if ' and ' in editor else "") + f".), \\textit{{{booktitle}}}"
        elif booktitle:
            result += f" In \\textit{{{booktitle}}}"
        if pages:
            result += f", {pages}"
        result += "."
        if publisher:
            result += f" {publisher}."

    # Add CABS ranking and Scimago quartile if present
    rankings = []
    if cabs:
        rankings.append(f"CABS {cabs}")
    if scimago:
        rankings.append(f"Scimago {scimago}")
    if rankings:
        result += f" \\textbf{{({', '.join(rankings)})}}"

    # Add URL links if present
    urls = []
    if doi:
        urls.append(f"\\href{{https://doi.org/{doi}}}{{DOI}}")
    if url:
        urlname = entry.get('urlname', 'Link')
        urls.append(f"\\href{{{url}}}{{{urlname}}}")
    url2 = entry.get('url2', '')
    if url2:
        urlname2 = entry.get('urlname2', 'Link')
        urls.append(f"\\href{{{url2}}}{{{urlname2}}}")
    if urls:
        result += " " + " | ".join(urls)

    return result


def generate_latex_publications(entries, output_file='cv_academic/publications_generated.tex'):
    """Generate LaTeX publications file from BibTeX entries."""

    # Organize entries by category
    categories = defaultdict(list)

    for entry in entries:
        cat = entry.get('category', 'other').lower()
        categories[cat].append(entry)

    # Sort each category by year (descending)
    for cat in categories:
        categories[cat].sort(key=lambda x: int(x.get('year', '0')), reverse=True)

    # Category order and titles for LaTeX
    category_order = [
        ('journal', 'Journal Articles'),
        ('conference', 'Conference Proceedings'),
        ('book', 'Books and Edited Volumes'),
    ]

    lines = [
        "% Auto-generated publications list from publications.bib",
        "% Generated by generate_publications.py",
        "",
    ]

    # Generate Software first
    if 'software' in categories:
        lines.append("\\subsection{Software}")
        lines.append("\\begin{enumerate}[leftmargin=*, topsep=0pt, itemsep=4pt, label={[\\arabic*]}]")
        for entry in categories['software']:
            formatted = format_entry_latex(entry)
            lines.append(f"    \\item {formatted}")
            lines.append("")
        lines.append("\\end{enumerate}")
        lines.append("")

    # Generate Journal Articles
    lines.append("\\subsection{Journal Articles}")
    lines.append("\\begin{enumerate}[leftmargin=*, topsep=0pt, itemsep=4pt, label={[\\arabic*]}]")

    if 'journal' in categories:
        for entry in categories['journal']:
            formatted = format_entry_latex(entry)
            lines.append(f"    \\item {formatted}")
            lines.append("")

    lines.append("\\end{enumerate}")
    lines.append("")

    # Generate Conference Proceedings
    lines.append("\\subsection{Conference Proceedings}")
    lines.append("\\begin{enumerate}[leftmargin=*, topsep=0pt, itemsep=4pt, label={[\\arabic*]}]")

    if 'conference' in categories:
        for entry in categories['conference']:
            formatted = format_entry_latex(entry)
            lines.append(f"    \\item {formatted}")
            lines.append("")

    lines.append("\\end{enumerate}")
    lines.append("")

    # Generate Books
    lines.append("\\subsection{Books and Edited Volumes}")
    lines.append("\\begin{enumerate}[leftmargin=*, topsep=0pt, itemsep=4pt, label={[\\arabic*]}]")

    if 'book' in categories:
        for entry in categories['book']:
            formatted = format_entry_latex(entry)
            lines.append(f"    \\item {formatted}")
            lines.append("")

    lines.append("\\end{enumerate}")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated {output_file} with LaTeX publications")


if __name__ == '__main__':
    entries = load_bibtex('publications.bib')
    generate_markdown(entries)
    generate_clinical_trials(entries)
    generate_cabs_ranked(entries)
    generate_by_year(entries)
    generate_policy_citations(entries)
    generate_latex_publications(entries)
