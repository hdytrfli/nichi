#!/usr/bin/env python3
"""
Main entry point for the Video File Organizer with Translation
Simplified version with Google Gemini translation capabilities
"""

import os
import sys
import argparse
from pathlib import Path
from nichi.tui import ExtendedVideoOrganizerTUI

sys.path.insert(0, str(Path(__file__).parent))


def validate_directory(directory_path: str) -> str:
    """Validate and resolve directory path"""
    wdir = os.path.abspath(os.path.expanduser(directory_path))

    if not os.path.exists(wdir):
        print(f"Error: Directory '{wdir}' does not exist.")
        sys.exit(1)

    if not os.path.isdir(wdir):
        print(f"Error: '{wdir}' is not a directory.")
        sys.exit(1)

    return wdir


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Video File Organizer with Translation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        nichi                    # Use current directory
        nichi /path/to/videos    # Use specific directory
        nichi ~/Downloads        # Use home directory path

        Features:
        • Convert VTT files to SRT format
        • Organize MP4 and subtitle files into folders  
        • Translate SRT files using Google Gemini AI
        • Support for 16+ languages

        For translation setup: https://makersuite.google.com/app/apikey
        """,
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Working directory (default: current directory)",
    )
    parser.add_argument(
        "--version", action="version", version="Video File Organizer v2.0.0"
    )

    args = parser.parse_args()
    working_directory = validate_directory(args.directory)

    try:
        print(f"Starting Video File Organizer in: {working_directory}")
        print("Press Ctrl+C at any time to exit.\n")

        app = ExtendedVideoOrganizerTUI(working_directory)
        app.run()

    except KeyboardInterrupt:
        print("\n\nApplication closed by user. Goodbye!")
        sys.exit(0)
    except ImportError as e:
        print(f"\n\nImport Error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
