# Video File Organizer with AI Translation

A simple TUI video file organizer with Google Gemini AI-powered translation capabilities for SRT subtitle files. This tool helps you organize your video files and translate subtitle files to any supported language with AI translation.

## Features

### Core Features

- **File Organization**: Organize video files by language and format
- **VTT to SRT Conversion**: Convert WebVTT subtitle files to SRT format
- **Interactive TUI**: Beautiful terminal user interface with Rich library

### AI Translation Features ✨

- **SRT Translation**: Translate subtitle files using Google Gemini AI
- **Batch Translation**: Translate multiple SRT files simultaneously
- **Smart Language Detection**: Automatically detect source language from filenames
- **Concurrent Processing**: Fast translation with concurrent batch processing
- **Error Handling**: Robust retry logic with exponential backoff
- **Progress Tracking**: Real-time progress indication with detailed statistics
- **20+ Language Support**: Support for major world languages

## Project Structure

```
.
|-- LICENSE
|-- readme.md
|-- requirements.txt
|-- setup.py
`-- src
    |-- __init__.py
    |-- main.py
    `-- nichi
        |-- __init__.py
        |-- converter.py
        |-- env_loader.py
        |-- gemini_translator.py
        |-- jellyfin_parser.py
        |-- operations.py
        |-- organizer.py
        |-- srt_parser.py
        |-- timing_adjuster.py
        |-- translator.py
        |-- tui.py
        |-- ui_components.py
        `-- user_input.py
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:

- `google-generativeai>=0.3.0` - Google Gemini AI SDK
- `python-dotenv>=1.0.0` - Environment variable management
- `rich>=13.0.0` - Beautiful terminal interface

### 2. Set up Google AI API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key for Google Gemini
3. Create a `.env` file in your project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your configuration
GOOGLE_AI_API_KEY=your_actual_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp
```

### 3. Install the Package

```bash
# Development installation
pip install -e .

# Or production installation
pip install .
```

## Usage

### Running the Application

```bash
# Run from current directory
python src/main.py

# Or if installed as package
nichi
```

### Menu Options

1. **Organize files by language** - Sort video files by detected language
2. **Convert VTT to SRT** - Convert WebVTT subtitle files to SRT format
3. **Translate SRT file** - Translate a single SRT file to another language
4. **Translate directory** - Batch translate all SRT files in a directory
5. **Show supported languages** - Display available language codes

### Translation Features

The AI translation system offers:

- **Fast Processing**: Concurrent batch processing with configurable batch sizes (default: 200 entries)
- **Smart Retry**: Automatic retry with exponential backoff for failed requests
- **Progress Tracking**: Real-time progress bars with success/failure statistics
- **Language Auto-detection**: Automatically detects source language from filenames
- **Terminal User Interface**: Beautiful TUI with Rich library

## Supported Languages

| Code | Language | Code | Language   | Code | Language   |
| ---- | -------- | ---- | ---------- | ---- | ---------- |
| en   | English  | es   | Spanish    | fr   | French     |
| de   | German   | it   | Italian    | pt   | Portuguese |
| ru   | Russian  | ja   | Japanese   | ko   | Korean     |
| zh   | Chinese  | ar   | Arabic     | hi   | Hindi      |
| th   | Thai     | vi   | Vietnamese | nl   | Dutch      |
| sv   | Swedish  | da   | Danish     | no   | Norwegian  |
| fi   | Finnish  | pl   | Polish     | tr   | Turkish    |

## Configuration

### Environment Variables

Create a `.env` file with:

```bash

# Required Configuration
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GEMINI_MODEL_NAME=gemini-2.0-flash-exp

# Optional Configuration
# GOOGLE_AI_PROJECT_ID=your_project_id_here
# TRANSLATION_BATCH_SIZE=10
# DEFAULT_TARGET_LANGUAGE=id

# Optional Configuration (Gemini)
# GEMINI_MAX_RETRIES=3
# GEMINI_BASE_DELAY=1
# GEMINI_MAX_DELAY=60
```

## Performance

The translation system is optimized for speed:

- **Large Batches**: Processes 200 subtitle entries per batch by default
- **Concurrent Processing**: Handles up to 5 batches simultaneously
- **Smart Retry**: Exponential backoff prevents API rate limiting
- **Progress Tracking**: Real-time feedback on translation progress

## Troubleshooting

### Translation Not Available

If translation features are unavailable:

1. **Check API Key**: Ensure `.env` file exists with valid `GOOGLE_AI_API_KEY`
2. **Verify Installation**: Run `pip list | grep google-generativeai`
3. **Test Connection**: Check internet connectivity
4. **API Quota**: Verify your Google AI API has remaining quota

### Common Issues

**Encoding Errors**: The translator automatically handles UTF-8, Latin-1, and CP1252 encodings
**Rate Limiting**: The system includes automatic retry with exponential backoff
**Large Files**: For very large subtitle files, the system automatically splits them into manageable batches

## Security

- Keep your `.env` file secure and never commit it to version control
- Add `.env` to your `.gitignore` file
- API keys are only used for Google Gemini translation requests
- No subtitle content is stored or logged
