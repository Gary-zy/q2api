# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup
```bash
# Install dependencies
uv venv
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env as needed
```

### Running the Service
```bash
# Development mode (hot reload)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production mode (4 workers)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

# Docker Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Testing Endpoints
```bash
# Health check
curl http://localhost:8000/healthz

# OpenAI endpoint
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4", "messages": [{"role": "user", "content": "test"}]}'

# Claude endpoint
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4.5", "max_tokens": 100, "messages": [{"role": "user", "content": "test"}]}'
```

## Architecture Overview

### Request Flow: Claude API → Amazon Q

The service acts as a protocol translator between Claude Messages API and Amazon Q's internal API:

1. **API Layer** (`app.py`): FastAPI endpoints receive Claude or OpenAI format requests
2. **Conversion** (`claude_converter.py`): Transforms Claude request to Amazon Q format
   - Maps message roles: `user` → `userInputMessage`, `assistant` → `aiMessage`
   - Converts tool definitions to Amazon Q schema
   - Handles multi-modal content (text, images)
3. **Upstream** (`replicate.py`): Sends request to Amazon Q using OIDC token
   - Parses binary event stream protocol
   - Extracts events: `assistantResponseEvent`, `codeReferenceEvent`, etc.
4. **Response** (`claude_stream.py`): Converts Amazon Q events back to Claude SSE format
   - Generates: `message_start`, `content_block_delta`, `message_stop`, etc.

### Module Responsibilities

- **app.py**: Main FastAPI app, account management, token refresh, API endpoints
- **db.py**: Database abstraction (SQLite/PostgreSQL/MySQL), auto-selects based on `DATABASE_URL`
- **replicate.py**: Amazon Q request replication, binary event stream parsing
- **auth_flow.py**: Device authorization flow (URL login via AWS OIDC)
- **claude_types.py**: Pydantic models for Claude API (ClaudeRequest, ClaudeMessage, ClaudeTool)
- **claude_converter.py**: Claude → Amazon Q request transformation
- **claude_parser.py**: Amazon Q event stream parsing (extracts text, citations, errors)
- **claude_stream.py**: Amazon Q → Claude SSE response generation

### Account Management

Accounts are stored in the `accounts` table with these key fields:
- `enabled`: 1=active, 0=disabled
- `error_count`: Auto-increments on failure, resets on success
- `success_count`: Tracks successful requests
- `accessToken`/`refreshToken`: OIDC tokens (auto-refreshed every 25 min)

**Selection Strategy:**
- Default: Random selection from all `enabled=1` accounts
- Lazy Pool: When `LAZY_ACCOUNT_POOL_ENABLED=true`, selects from top N accounts (sorted by `LAZY_ACCOUNT_POOL_ORDER_BY`)

**Auto-Disable:** When `error_count >= MAX_ERROR_COUNT`, account is automatically disabled

### Token Refresh

Two mechanisms:
1. **Background task** (`_refresh_stale_tokens`): Runs every 5 minutes, refreshes tokens older than 25 minutes
2. **On-demand**: If `accessToken` is missing during request, triggers immediate refresh

## Key Implementation Details

### Dynamic Module Loading

`app.py` uses `importlib.util` to dynamically load modules (`replicate.py`, `claude_*.py`) to avoid package initialization issues. This allows the service to run as a single-file application without requiring a proper Python package structure.

### Binary Event Stream Protocol

Amazon Q uses a custom binary protocol for event streams (not standard SSE). `replicate.py` implements the parser:
- 4-byte prelude: total length + headers length
- Variable-length headers (name-value pairs with type encoding)
- Payload (JSON or binary)
- 4-byte CRC32 checksum

### Database Backend Selection

`db.py` auto-detects database type from `DATABASE_URL`:
- Empty/unset → SQLite (`data.sqlite3`)
- `postgres://` or `postgresql://` → PostgreSQL (asyncpg)
- `mysql://` → MySQL (aiomysql)

All backends implement the same `DatabaseBackend` interface.

### Environment Variables

Critical settings in `.env`:
- `OPENAI_KEYS`: API key whitelist (empty = dev mode, no auth)
- `DATABASE_URL`: Database connection (empty = SQLite)
- `MAX_ERROR_COUNT`: Error threshold for auto-disable (default: 100)
- `ENABLE_CONSOLE`: Enable/disable web console (default: true)
- `ADMIN_PASSWORD`: Console login password (default: "admin")
- `LAZY_ACCOUNT_POOL_*`: Virtual account pool settings for performance

### Admin Console Authentication

When `ENABLE_CONSOLE=true`:
- Login endpoint: `POST /api/login` with `{"password": "..."}`
- Returns session token valid for 30 days
- All admin endpoints require `Authorization: Bearer <token>` header
- Frontend stores token in localStorage

## Common Patterns

### Adding a New API Endpoint

1. Define Pydantic request/response models
2. Add endpoint in `app.py` with `@app.post()` or `@app.get()`
3. Use `Depends(require_account)` for endpoints needing account selection
4. Use `Depends(verify_admin_password)` for admin-only endpoints
5. Update account stats with `await _update_stats(account_id, success: bool)`

### Modifying Claude → Amazon Q Conversion

Edit `claude_converter.py`:
- `convert_claude_to_amazonq_request()`: Main conversion function
- `convert_tool()`: Tool definition mapping
- `extract_images_from_content()`: Multi-modal content handling

### Changing Event Stream Parsing

Edit `claude_parser.py`:
- `EventStreamParser.parse_stream()`: Main parsing logic
- `extract_event_info()`: Event type extraction

### Database Schema Changes

1. Modify schema in `db.py` (all three backends: SQLite, PostgreSQL, MySQL)
2. For existing deployments, create migration script in `scripts/migrate_db.py`
3. Test with all three database backends

## File Structure Notes

- `templates/streaming_request.json`: Amazon Q request template (URL, headers, body)
- `frontend/index.html`: Web console (single-file HTML/CSS/JS)
- `frontend/login.html`: Login page
- `scripts/`: Utility scripts for account management and database operations
- `account-feeder/`: Separate service for batch account feeding (optional)
