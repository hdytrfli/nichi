#!/usr/bin/env python3
"""
Main entry point for the Video File Organizer with Translation
Extended version with Google Gemini translation capabilities
"""

import os
import sys
import argparse
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))

try:
    from nichi.tui import ExtendedVideoOrganizerTUI
except ImportError as e:
    print(f"Error: Could not import required modules: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)


def check_environment():
    """Check environment setup and provide helpful messages"""
    # Check in current working directory first, then in script directory
    cwd_env = Path.cwd() / ".env"
    script_env = Path(__file__).parent / ".env"

    env_file = None
    if cwd_env.exists():
        env_file = cwd_env
    elif script_env.exists():
        env_file = script_env

    if not env_file:
        print("\n" + "=" * 60)
        print("⚠️  TRANSLATION SETUP NOTICE")
        print("=" * 60)
        print("Translation features require a .env file with your Google AI API key.")
        print()
        print("To enable translation:")
        print("1. Create a .env file in your current directory or script directory")
        print("2. Add: GOOGLE_AI_API_KEY=your_api_key_here")
        print("3. Add: DEFAULT_TARGET_LANGUAGE=id (optional, defaults to 'id')")
        print("4. Get your API key from: https://makersuite.google.com/app/apikey")
        print()
        print("The application will continue with existing features enabled.")
        print("Translation options will be disabled until properly configured.")
        print("=" * 60)
        print()

        try:
            response = (
                input("Continue without translation features? (y/n): ").lower().strip()
            )
            if response not in ["y", "yes", ""]:
                print("Setup cancelled. Please configure your .env file and try again.")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user.")
            sys.exit(0)
    else:
        print(f"✅ Found .env file at: {env_file}")


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
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(
        description="Video File Organizer with Translation - Organize video files and translate subtitles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
        nichi                    
        nichi /path/to/videos    
        nichi ~/Downloads        

        Features:
        • Convert VTT files to SRT format
        • Organize MP4 and subtitle files into folders
        • Translate SRT files using Google Gemini AI (requires API key)
        • Support for 20+ languages

        For translation setup, see: https://makersuite.google.com/app/apikey
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
    parser.add_argument(
        "--skip-env-check",
        action="store_true",
        help="Skip environment configuration check",
    )

    args = parser.parse_args()
    working_directory = validate_directory(args.directory)

    if not args.skip_env_check:
        check_environment()

    try:
        print(f"Starting Video File Organizer in: {working_directory}")
        print("Press Ctrl+C at any time to exit.\n")
        app = ExtendedVideoOrganizerTUI(working_directory)
        app.run()

    except KeyboardInterrupt:
        print("\n\n✅ Application closed by user. Goodbye!")
        sys.exit(0)
    except ImportError as e:
        print(f"\n\nImport Error: {e}")
        print("Please ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print("If this error persists, please check your environment setup.")
        sys.exit(1)


if __name__ == "__main__":
    main()
