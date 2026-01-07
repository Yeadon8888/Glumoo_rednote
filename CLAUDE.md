# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Glumoo 是一个专注于小红书和 Instagram 宠物内容创作的 AI 图文生成Agent。它使用 AI 模型生成大纲、内容文本（标题、正文、标签）和风格化图片，支持多平台风格切换。

**Tech Stack:**
- **Backend**: Python 3.11+ with Flask + Gunicorn, managed by `uv` package manager
- **Frontend**: Vue 3 + TypeScript + Vite + Pinia
- **AI Providers**: Google Gemini for text generation, configurable image generation (Google GenAI, OpenAI-compatible APIs)
- **Deployment**: Docker, Railway (with Volume support for data persistence)

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
# Build and run locally
docker-compose up -d

# Build without cache
docker-compose build --no-cache

# View logs
docker logs glumoo-pet-agent --tail 50

# Stop and remove
docker-compose down
```

**Important**: Docker uses volume mapping `./data:/app/data` for persistent storage.

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=backend
```

Tests are located in `tests/` with shared fixtures in `tests/conftest.py`.

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
├── prompts/            # AI prompt templates (text files)
│   ├── outline_prompt.txt              # Xiaohongshu outline generation
│   ├── outline_prompt_instagram.txt    # Instagram outline generation (English)
│   ├── image_prompt.txt                # Full image generation template
│   ├── image_prompt_short.txt          # Short image generation template
│   ├── content_prompt.txt              # Xiaohongshu content generation
│   └── content_prompt_instagram.txt    # Instagram content generation (English)
└── utils/              # Shared utilities
```

**Key Design Patterns:**
- **Factory Pattern**: `ImageGeneratorFactory` creates appropriate generator based on `provider.type` from YAML config
- **Blueprint Modularity**: Routes are split by domain (outline, images, history, config, content) and registered to a main API blueprint
  - Each route module has a `create_<name>_blueprint()` function that returns a new Blueprint instance
  - This pattern supports multiple `create_app()` calls (important for testing)
  - All blueprints registered to main `/api` Blueprint in `routes/__init__.py`
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
- State persisted to localStorage to survive page refreshes
- State flow: `input` → `outline` → `generating` → `result`

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
- **Environment Variables**: Supports `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `PORT`, `FLASK_HOST`, `FLASK_DEBUG`, `DATA_DIR`

### Data Directory Structure

**CRITICAL**: All persistent data is stored in a unified `/app/data` directory to support Railway's single-volume limitation:

```
/app/data/                    # Single volume mount point
├── history/                  # Historical records directory
│   ├── index.json           # History record index
│   ├── <record_id>.json     # Individual history records
│   └── <task_id>/           # Task-related files (images)
└── output/                   # Image output directory (legacy, may be merged)
```

**Path Configuration** (`backend/config.py`):
- `DATA_DIR`: Absolute path to data directory (defaults to `{project_root}/data`)
- `HISTORY_DIR`: `{DATA_DIR}/history`
- `OUTPUT_DIR`: `{DATA_DIR}/output`
- Uses absolute paths calculated from `__file__` to ensure reliability across environments

### Platform Support (Xiaohongshu vs Instagram)

The application supports generating content for two platforms with different styles:

**Implementation:**
- Frontend: Platform selector dropdown in `ComposerInput.vue`, state managed in Pinia store
- Backend: Dynamic prompt loading based on `platform` parameter ('xiaohongshu' | 'instagram')
- Routes: `outline_routes.py` and `content_routes.py` extract `platform` from request
- Services: `outline.py` and `content.py` use `_load_prompt_template(platform)` to load appropriate prompts

**Prompt Files:**
- Xiaohongshu: `outline_prompt.txt`, `content_prompt.txt` (Chinese)
- Instagram: `outline_prompt_instagram.txt`, `content_prompt_instagram.txt` (English)

**Default**: `platform='xiaohongshu'` if not specified

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

### Production Deployment

#### Gunicorn Configuration

The application uses Gunicorn as the production WSGI server (configured in Dockerfile):

```dockerfile
CMD uv run gunicorn --bind 0.0.0.0:${PORT:-12398} --workers 2 --threads 4 --timeout 120 --access-logfile - --error-logfile - "backend.app:app"
```

**Key Points:**
- Uses `${PORT}` environment variable (provided by Railway) or falls back to `12398`
- 2 workers with 4 threads each for handling concurrent requests
- 120s timeout for long-running image generation requests
- Logs to stdout/stderr for container environments
- Entry point is `backend.app:app` (the Flask app created by `create_app()`)

**CRITICAL**: The `backend/app.py` must export an `app` variable at module level for Gunicorn:
```python
# At bottom of backend/app.py
app = create_app()  # Required for Gunicorn
```

#### Railway Deployment

**Environment Variables Required:**
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`: API key for AI services
- `PORT`: Automatically provided by Railway (DO NOT override)

**Volume Configuration:**
- Railway supports only ONE volume per service
- Mount Path: `/app/data`
- This single volume contains both `history/` and `output/` subdirectories

**Deployment Steps:**
1. Push code to GitHub
2. Railway auto-deploys from main branch
3. In Railway Dashboard → Settings → Volumes:
   - Add Volume with Mount Path: `/app/data`
4. Set environment variable `GOOGLE_API_KEY` in Variables section
5. Railway will automatically redeploy

**Health Check:**
- Path: `/api/health` (configured in `railway.toml`)
- Timeout: 30s
- The healthcheck endpoint is in `image_routes.py:health_check()`

**Common Issues:**
- Healthcheck failure: Check that `PORT` environment variable is properly read and app binds to it
- Data persistence: Ensure volume is mounted at `/app/data` (not `/app/history` or `/app/output`)
- Path errors: All path references must use `Config.HISTORY_DIR` / `Config.DATA_DIR`, never hardcoded paths

### History Persistence

- Records saved to `history/` directory (JSON metadata + image references)
- Each record has a `record_id`, stores outline, generated images, timestamps
- History routes provide CRUD operations + search

## Important Notes

### Port Binding for Production

**CRITICAL**: When deploying to cloud platforms (Railway, Heroku, etc.):
- The platform provides a `PORT` environment variable that MUST be used
- `backend/config.py` reads `PORT` env var first, falls back to `FLASK_PORT`, then `12398`
- Gunicorn CMD in Dockerfile uses `${PORT:-12398}` for shell-level port binding
- Flask app uses `Config.PORT` which resolves the environment variable hierarchy

### Path Configuration Best Practices

**ALWAYS use Config constants for paths:**
```python
# ✅ CORRECT
from backend.config import Config
history_path = Config.HISTORY_DIR

# ❌ WRONG - Hardcoded paths will break in production
history_path = "history"
history_path = os.path.join(os.path.dirname(__file__), "../../history")
```

**Why absolute paths matter:**
- Docker containers may start with different working directories
- Railway deployment uses different directory structures
- Relative paths are unreliable in production environments

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

Prompts are stored as plain text files in `backend/prompts/`:

**Xiaohongshu (Chinese):**
- `outline_prompt.txt` - Controls outline structure and format
- `content_prompt.txt` - Template for title/text/tags generation

**Instagram (English):**
- `outline_prompt_instagram.txt` - Instagram carousel post structure
- `content_prompt_instagram.txt` - Instagram caption with hashtags

**Image Generation (Platform-agnostic):**
- `image_prompt.txt` - Main image generation prompt
- `image_prompt_short.txt` - Simplified image generation prompt

Edit these files directly to modify AI generation behavior. No code changes required. The service layer automatically loads the correct prompt based on the `platform` parameter.

## API Endpoints Reference

All endpoints under `/api` prefix:

**Content Generation:**
- `POST /api/outline` - Generate outline from user input (supports `platform` parameter)
- `POST /api/content` - Generate title, copywriting, and tags (supports `platform` parameter)
- `POST /api/generate` - Generate images from outline (SSE stream)
- `POST /api/regenerate_image` - Regenerate single image

**Images:**
- `GET /api/images/<task_id>/<filename>` - Serve generated images
- Query param `?thumbnail=true/false` for thumbnail vs full image

**History:**
- `GET /api/history` - List history records (pagination support)
- `POST /api/history` - Save new record
- `GET /api/history/<record_id>` - Get specific record
- `PUT /api/history/<record_id>` - Update record
- `DELETE /api/history/<record_id>` - Delete record
- `GET /api/history/<record_id>/exists` - Check if record exists
- `GET /api/history/search?keyword=<query>` - Search records
- `GET /api/history/stats` - Get statistics

**Configuration:**
- `GET /api/config` - Get provider configs (API keys masked)
- `PUT /api/config` - Update provider configs

**Health:**
- `GET /api/health` - Health check endpoint (returns `{"success": true, "message": "服务正常运行"}`)
