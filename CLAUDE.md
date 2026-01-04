# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Glumoo 是一个专注于小红书宠物内容创作的 AI 图文生成Agent。它使用 AI 模型生成大纲、内容文本（标题、正文、标签）和风格化图片。

**Tech Stack:**
- **Backend**: Python 3.11+ with Flask, managed by `uv` package manager
- **Frontend**: Vue 3 + TypeScript + Vite + Pinia
- **AI Providers**: Google Gemini for text generation, configurable image generation (Google GenAI, OpenAI-compatible APIs)

## Development Commands

### Backend

```bash
# Install dependencies
uv sync

# Run backend server (from project root)
uv run python -m backend.app
# Server runs on http://localhost:12398
```

### Frontend

```bash
# Install dependencies
cd frontend
pnpm install

# Run dev server
pnpm dev
# Server runs on http://localhost:5173

# Build for production
pnpm build
```

### One-Click Startup

```bash
# macOS/Linux
./start.sh

# Windows
start.bat
```

### Docker

```bash
# Run with docker-compose
docker-compose up -d

# Or run directly
docker run -d -p 12398:12398 -v ./history:/app/history -v ./output:/app/output histonemax/redink:latest
```

### Testing

The project has backend unit tests located in `tests/`. Run with pytest (though test runner commands aren't explicitly documented in the codebase - use standard pytest commands).

## Architecture

### Backend Structure (Modular Blueprint Design)

The backend uses Flask Blueprints for modular organization:

```
backend/
├── app.py              # Flask app entry point, logging setup
├── config.py           # Config loader for YAML-based provider configs
├── routes/             # API routes (all under /api prefix)
│   ├── __init__.py     # Blueprint registration
│   ├── outline_routes.py    # POST /api/outline - Generate content outline
│   ├── image_routes.py      # POST /api/generate, /api/regenerate_image - Image generation
│   ├── history_routes.py    # History CRUD operations
│   ├── config_routes.py     # GET/PUT /api/config - Provider config management
│   └── content_routes.py    # Content generation (titles, text, tags)
├── services/           # Business logic layer
│   ├── outline.py      # Outline generation service
│   ├── image.py        # Image generation service
│   ├── history.py      # History persistence service
│   └── content.py      # Content generation service
├── generators/         # AI provider implementations
│   ├── factory.py      # ImageGeneratorFactory - provider selection
│   ├── base.py         # ImageGeneratorBase - abstract interface
│   ├── google_genai.py       # Google Gemini image generator
│   ├── openai_compatible.py  # OpenAI-compatible API generator
│   └── image_api.py          # Generic image API generator
├── prompts/            # AI prompt templates
└── utils/              # Shared utilities
```

**Key Design Patterns:**
- **Factory Pattern**: `ImageGeneratorFactory` creates appropriate generator based on `provider.type` from YAML config
- **Blueprint Modularity**: Routes are split by domain (outline, images, history, config, content) and registered to a main API blueprint
- **Service Layer**: Business logic separated from routes for testability

### Frontend Structure (Vue 3 + Pinia)

```
frontend/src/
├── views/              # Page-level components (route targets)
│   ├── HomeView.vue         # Landing page
│   ├── OutlineView.vue      # Outline editing
│   ├── GenerateView.vue     # Image generation progress
│   ├── ResultView.vue       # Generated content display
│   ├── HistoryView.vue      # Historical records
│   └── SettingsView.vue     # Provider config UI
├── components/         # Reusable UI components
│   ├── home/           # Home page components
│   ├── history/        # ImageGalleryModal, OutlineModal
│   ├── result/         # Result display components
│   └── settings/       # Config form components
├── stores/
│   └── generator.ts    # Pinia store - app state management
├── router/
│   └── index.ts        # Vue Router config
└── api/                # Backend API client
```

**State Management:**
- Single Pinia store (`generator.ts`) manages all app state: outline, images, history, config
- Store methods handle API calls and state updates

### Configuration System

Two YAML config files (auto-loaded or web UI editable):

1. **`text_providers.yaml`**: Text generation (Gemini, OpenAI-compatible)
   - `active_provider`: Currently active text provider
   - `providers`: Dict of provider configs (api_key, base_url, model)

2. **`image_providers.yaml`**: Image generation providers
   - `active_provider`: Currently active image provider
   - `providers`: Dict with provider configs
   - `high_concurrency`: Boolean flag (parallel image generation, disabled by default for GCP trial accounts)

**Config Loading:**
- `backend/config.py` loads YAML on startup with caching (`_image_providers_config`, `_text_providers_config`)
- `Config.reload_config()` clears cache when config is updated via web UI
- Config API at `/api/config` supports GET/PUT for runtime updates

### Image Generation Flow

1. **Outline Generation**: User input → AI generates page-by-page outline (title + description per page)
2. **Image Generation**:
   - Cover image generated first with full context
   - Content pages generated (parallel if `high_concurrency=true`, sequential if false)
   - Each generation includes outline context + previous cover reference for style consistency
3. **Regeneration**: Single image can be regenerated while preserving style (passes cover image + full outline as context)

**Generator Interface:**
- All generators extend `ImageGeneratorBase`
- Core method: `generate_image(prompt, outline_context, cover_image_path, index)` → saves to `output/` and returns filename
- Generator type selected by `ImageGeneratorFactory.create(provider_type, config)`

### History Persistence

- Records saved to `history/` directory (JSON metadata + image references)
- Each record has a `record_id`, stores outline, generated images, timestamps
- History routes provide CRUD operations + search

## Important Notes

### Configuration Validation

- On startup, `backend/app.py` validates both YAML configs and warns if API keys are missing
- Missing configs fallback to empty defaults (won't crash, but generation will fail until configured)

### Docker Deployment

- `Dockerfile` builds frontend static files and serves them via Flask in production
- `app.py` detects `frontend/dist/` existence to enable static file serving
- Docker images don't include API keys - users must configure via web UI or volume-mount YAML files

### Provider Types

The `type` field in YAML config determines which generator class is instantiated:
- `google_genai` → `GoogleGenAIGenerator`
- `openai` / `openai_compatible` → `OpenAICompatibleGenerator`
- `image_api` → `ImageApiGenerator`

### High Concurrency Mode

Disabled by default (`high_concurrency: false`) to avoid rate limits on GCP $300 trial accounts. When enabled, generates all images (up to 15) in parallel using concurrent requests.

### Logging

Custom logging format in `app.py:setup_logging()`:
- DEBUG level for backend modules
- INFO level for werkzeug
- WARNING level for urllib3

## Common Workflows

### Adding a New Image Provider Type

1. Create new generator class in `backend/generators/` extending `ImageGeneratorBase`
2. Implement `generate_image()` method
3. Register in `ImageGeneratorFactory.GENERATORS` dict
4. Add corresponding `type` option in YAML config docs

### Adding New API Routes

1. Create route module in `backend/routes/` with `create_<name>_blueprint()` function
2. Register blueprint in `backend/routes/__init__.py:create_api_blueprint()`
3. Create corresponding service in `backend/services/` if business logic is complex

### Modifying AI Prompts

Prompts are located in `backend/prompts/` - update templates there to change AI generation behavior.

## API Endpoints Reference

All endpoints under `/api` prefix:

- `POST /api/outline` - Generate outline from user input
- `POST /api/generate` - Generate images from outline
- `POST /api/regenerate_image` - Regenerate single image
- `GET /api/images/<filename>` - Serve generated images
- `GET /api/history` - List history records
- `POST /api/history` - Save new record
- `GET /api/history/<record_id>` - Get specific record
- `DELETE /api/history/<record_id>` - Delete record
- `GET /api/config` - Get provider configs (API keys masked)
- `PUT /api/config` - Update provider configs
- `POST /api/content/title` - Generate title
- `POST /api/content/text` - Generate body text
- `POST /api/content/tags` - Generate tags
