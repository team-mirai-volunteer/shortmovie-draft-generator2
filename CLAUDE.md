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
OPENAI_API_KEY=
GOOGLE_SERVICE_ACCOUNT_KEY_PATH=
GOOGLE_DRIVE_TARGET_FOLDER_ID=
SLACK_WEBHOOK_URL=
```

## Testing Strategy
- Unit tests for each component (tests/unit/)
- External APIs are tested using mocks
- Leverage DIContainer to swap dependencies