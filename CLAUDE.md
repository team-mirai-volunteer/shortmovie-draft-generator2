# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Python project that automatically generates short video drafts. It transcribes audio from video files using Whisper API and generates drafts using ChatGPT API.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync
```

### Running Tests
```bash
make test    # Run all tests
# or
uv run pytest tests/unit/  # Unit tests only
uv run pytest -k "test_name"  # Run specific test
```

### Type Checking & Linting
```bash
make lint    # ruff check & mypy
# or individually
uv run ruff check .
uv run mypy .
```

### Code Formatting
```bash
make fmt     # ruff format
```

### Running the Application
```bash
# Single video processing
uv run python -m src.main generate-single video.mp4 --use-cache

# Google Drive batch processing
uv run python -m src.main batch-process --update
```

## Architecture Structure

### Clean Architecture Layers
```
src/
├── main.py              # DI Container setup and CLI entry point
├── usecases/           # Use case layer (business rules)
├── service/            # Service layer (domain logic)
├── clients/            # External API integration layer
├── sources/            # Data source layer
├── builders/           # Helper layer (prompt building)
└── models/             # Data model definitions
```

### Key Design Principles
- Each layer doesn't depend on layers above it (Dependency Inversion Principle)
- DIContainer class (main.py) manages all dependencies
- External API clients are injected through interfaces
- Each component follows the Single Responsibility Principle

### Main Component Responsibilities

**GenerateShortDraftUseCase**: Main flow for generating drafts from videos
- Audio transcription → Prompt building → ChatGPT API call → Result formatting

**GoogleDriveBatchProcessUseCase**: Google Drive batch processing
- Processes videos in specified folder and uploads results

**DraftGenerator**: Draft generation business logic
- Manages prompt templates and generation parameters

**Various Clients**: External API integrations
- WhisperClient: Audio transcription
- ChatGPTClient: AI draft generation
- GoogleDriveClient: File operations
- SlackClient: Notification sending

## Environment Variables
Set the following in `.env` file:
```
# Required
OPENAI_API_KEY=

# Optional - Google Service Account Authentication (choose one):
# Option 1: File path
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=path/to/service-account-key.json

# Option 2: JSON string
GOOGLE_SERVICE_ACCOUNT_KEY_JSON='{"type":"service_account","project_id":"..."}'

# Option 3: Base64 encoded JSON (recommended for Cloud Run Jobs)
GOOGLE_SERVICE_ACCOUNT_KEY_BASE64=eyJ0eXBlIjoic2VydmljZV9hY2NvdW50IiwicHJvamVjdF9pZCI6Li4ufQ==

# Google Drive batch processing folders (both formats supported)
# Format 1:
INPUT_DRIVE_FOLDER=https://drive.google.com/drive/folders/xxx
OUTPUT_DRIVE_FOLDER=https://drive.google.com/drive/folders/yyy

# Format 2 (alternative):
GOOGLE_DRIVE_SOURCE_FOLDER_URL=https://drive.google.com/drive/folders/xxx  
GOOGLE_DRIVE_DESTINATION_FOLDER_URL=https://drive.google.com/drive/folders/yyy

# Other optional
GOOGLE_DRIVE_UPLOAD_FOLDER_ID=
SLACK_WEBHOOK_URL=
```

## Testing Strategy
- Unit tests for each component (tests/unit/)
- External APIs are tested using mocks
- Leverage DIContainer to swap dependencies