#!/usr/bin/env python3
"""
PDF to Markdown Converter

Converts PDF files to markdown format using pymupdf4llm.

Installation:
    pip install pymupdf4llm

Usage:
    python pdf_to_markdown.py <input.pdf> [output.md]
    python pdf_to_markdown.py <directory>  # Convert all PDFs in directory
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

try:
    import pymupdf4llm
except ImportError:
    print("Error: pymupdf4llm not installed.")
    print("Install with: pip install pymupdf4llm")
    sys.exit(1)


def convert_pdf_to_markdown(pdf_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Convert a PDF file to markdown.

    Args:
        pdf_path: Path to the input PDF file
        output_path: Optional path for output markdown file.
                    If not provided, uses the same name with .md extension.

    Returns:
        Path to the created markdown file
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if output_path is None:
        output_path = pdf_path.with_suffix(".md")

    print(f"Converting: {pdf_path.name}")

    # Convert PDF to markdown
    md_text = pymupdf4llm.to_markdown(str(pdf_path))

    # Write output
    output_path.write_text(md_text, encoding="utf-8")

    print(f"  -> {output_path.name}")
    return output_path


def convert_directory(directory: Path, recursive: bool = False) -> List[Path]:
    """
    Convert all PDFs in a directory to markdown.

    Args:
        directory: Path to directory containing PDFs
        recursive: If True, search subdirectories as well

    Returns:
        List of paths to created markdown files
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdf_files = sorted(directory.glob(pattern))

    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return []

    print(f"Found {len(pdf_files)} PDF file(s)")

    converted = []
    for pdf_path in pdf_files:
        try:
            output_path = convert_pdf_to_markdown(pdf_path)
            converted.append(output_path)
        except Exception as e:
            print(f"  Error converting {pdf_path.name}: {e}")

    return converted


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf                 # Convert single PDF
  %(prog)s document.pdf output.md       # Convert with custom output name
  %(prog)s ./pdfs/                       # Convert all PDFs in directory
  %(prog)s ./pdfs/ -r                    # Convert PDFs recursively
        """,
    )
    parser.add_argument("input", type=Path, help="PDF file or directory containing PDFs")
    parser.add_argument("output", type=Path, nargs="?", help="Output markdown file (only for single PDF conversion)")
    parser.add_argument("-r", "--recursive", action="store_true", help="Recursively search for PDFs in subdirectories")

    args = parser.parse_args()

    input_path = args.input.resolve()

    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            print(f"Error: {input_path} is not a PDF file")
            sys.exit(1)

        output_path = args.output.resolve() if args.output else None
        try:
            convert_pdf_to_markdown(input_path, output_path)
            print("Done!")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif input_path.is_dir():
        if args.output:
            print("Warning: Output argument ignored for directory conversion")

        converted = convert_directory(input_path, args.recursive)
        print(f"\nConverted {len(converted)} file(s)")

    else:
        print(f"Error: {input_path} does not exist")
        sys.exit(1)


if __name__ == "__main__":
    main()
