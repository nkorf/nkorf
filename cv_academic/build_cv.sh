#!/bin/bash
#
# build_cv.sh - Build the Academic CV
#
# This script generates the academic CV PDF by:
# 1. Running the Python script to generate publications from BibTeX
# 2. Compiling the LaTeX document twice (for proper references)
#
# Prerequisites:
# - Python 3 with bibtexparser package (use the .venv in parent directory)
# - pdflatex (e.g., from TinyTeX or TeX Live)
#
# Usage:
#   ./build_cv.sh
#
# The script should be run from the cv_academic directory or the parent directory.
#

set -e  # Exit on error

# Determine script location and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== Building Academic CV ==="
echo ""

# Step 1: Generate publications from BibTeX
echo "Step 1: Generating publications from BibTeX..."
cd "$PROJECT_ROOT"

# Activate virtual environment and run Python script
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python generate_publications.py
    deactivate
else
    echo "Warning: .venv not found, trying system Python..."
    python3 generate_publications.py
fi

echo ""

# Step 2: Compile LaTeX document
echo "Step 2: Compiling LaTeX document..."
cd "$SCRIPT_DIR"

# First pass
pdflatex -interaction=nonstopmode nikolaos_korfiatis_academic_cv.tex > /dev/null 2>&1

# Second pass (for references)
pdflatex -interaction=nonstopmode nikolaos_korfiatis_academic_cv.tex > /dev/null 2>&1

echo ""
echo "=== Build complete ==="
echo "Output: $SCRIPT_DIR/nikolaos_korfiatis_academic_cv.pdf"
