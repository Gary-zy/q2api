# Q2API Project Documentation

## Overview

**Q2API** is an API bridge service that converts Amazon Q Developer into OpenAI and Claude API-compatible endpoints. It provides multi-account management, streaming responses, and intelligent load balancing.

## Architecture

### Core Components

```
┌─────────────────┐
│   API Clients   │ (OpenAI SDK, Claude SDK, curl)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI Server │ (app.py)
│  - /v1/chat/completions (OpenAI)
│  - /v1/messages (Claude)
└────────┬────────┘
         │
         ├──► Account Pool (Random Selection)
         │
         ├──► Token Refresh (Background + On-Demand)
         │
         ▼
┌─────────────────┐
│  Amazon Q API   │
│  (OIDC + SSE)   │
└─────────────────┘
```

### Module Structure

| Module | Purpose |
|--------|---------|
| `app.py` | FastAPI application, API endpoints, account management |
| `replicate.py` | Amazon Q request replication and SSE handling |
| `auth_flow.py` | Device authorization flow (URL login) |
| `claude_types.py` | Claude API type definitions (Pydantic models) |
| `claude_converter.py` | Claude → Amazon Q request conversion |
| `claude_parser.py` | Amazon Q event stream parsing |
| `claude_stream.py` | Claude SSE response generation |
| `db.py` | Database abstraction (SQLite/PostgreSQL/MySQL) |

## API Compatibility

### OpenAI Chat Completions API

**Endpoint:** `POST /v1/chat/completions`

**Features:**
- Streaming and non-streaming responses
- System prompts
- Multi-turn conversations
- Token usage statistics

**Example:**
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"
)

response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Claude Messages API

**Endpoint:** `POST /v1/messages`

**Features:**
- Full Claude API compatibility
- Tool use (function calling)
- Multi-modal content (text, images)
- System prompts (string or array)
- Streaming with SSE

**Example:**
```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"
)

message = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Account Management

### Account Lifecycle

```
┌──────────────┐
│ Device Auth  │ (URL Login)
│ /v2/auth/*   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Account    │ (enabled=1)
│   Created    │
└──────┬───────┘
       │
       ├──► Token Refresh (every 25 min)
       │
       ├──► Request Handling
       │
       ├──► Error Tracking (MAX_ERROR_COUNT)
       │
       ▼
┌──────────────┐
│   Disabled   │ (enabled=0)
│ (if errors)  │
└──────────────┘
```

### Database Schema

```sql
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,
    label TEXT,
    clientId TEXT,
    clientSecret TEXT,
    refreshToken TEXT,
    accessToken TEXT,
    other TEXT,                    -- JSON metadata
    last_refresh_time TEXT,
    last_refresh_status TEXT,
    created_at TEXT,
    updated_at TEXT,
    enabled INTEGER DEFAULT 1,
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0
);
```

### Account Selection Strategy

**Default Mode:**
- Random selection from all `enabled=1` accounts
- No API key → account mapping

**Lazy Pool Mode** (`LAZY_ACCOUNT_POOL_ENABLED=true`):
- Select from top N accounts (sorted by `LAZY_ACCOUNT_POOL_ORDER_BY`)
- Reduces database queries
- Configurable pool size and refresh offset

## Authentication & Authorization

### API Key Authorization

**Environment Variable:** `OPENAI_KEYS`

```bash
# Development mode (no auth)
OPENAI_KEYS=""

# Production mode (whitelist)
OPENAI_KEYS="key1,key2,key3"
```

**Request Headers:**
- `Authorization: Bearer <key>` (OpenAI style)
- `x-api-key: <key>` (Claude style)

### Admin Console Authentication

**Environment Variables:**
- `ENABLE_CONSOLE` - Enable/disable web console (default: `true`)
- `ADMIN_PASSWORD` - Console login password (default: `admin`)

**Session Management:**
- 30-day session validity
- Token stored in browser localStorage
- All admin API endpoints require `Authorization: Bearer <token>`

## Token Management

### Automatic Refresh

**Background Task:**
- Runs every 5 minutes
- Refreshes tokens older than 25 minutes
- Updates `last_refresh_time` and `last_refresh_status`

**On-Demand Refresh:**
- Triggered when `accessToken` is missing
- Automatic retry on request failure
- Manual refresh via `/v2/accounts/{id}/refresh`

### OIDC Flow

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│ POST /token                      │
│ {                                │
│   grantType: "refresh_token",    │
│   clientId: "...",               │
│   clientSecret: "...",           │
│   refreshToken: "..."            │
│ }                                │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────┐
│ New Tokens   │
│ - accessToken│
│ - refreshToken│
└──────────────┘
```

## Request Flow

### Claude Messages → Amazon Q

**Conversion Steps:**

1. **Parse Claude Request**
   - Extract `messages`, `system`, `tools`, `max_tokens`
   - Validate required fields

2. **Convert to Amazon Q Format**
   - Map message roles (`user` → `userInputMessage`, `assistant` → `aiMessage`)
   - Convert tool definitions to Amazon Q schema
   - Handle multi-modal content (text, images)

3. **Send to Amazon Q**
   - Use `replicate.py` to send request
   - Handle SSE event stream

4. **Parse Amazon Q Events**
   - `assistantResponseEvent` → text content
   - `codeReferenceEvent` → citations
   - `supplementaryWebLinksEvent` → web links
   - `error` → error handling

5. **Generate Claude SSE Response**
   - `message_start` → initial metadata
   - `content_block_start` → content block initialization
   - `content_block_delta` → incremental content
   - `content_block_stop` → content block completion
   - `message_delta` → usage statistics
   - `message_stop` → end of stream

### Error Handling

**Account-Level:**
- Increment `error_count` on failure
- Auto-disable when `error_count >= MAX_ERROR_COUNT`
- Reset `error_count` on success

**Request-Level:**
- Return proper HTTP status codes (401, 502, etc.)
- Update account stats before raising exceptions
- Close upstream connections on error

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `""` | Database connection URL (empty = SQLite) |
| `OPENAI_KEYS` | `""` | API key whitelist (comma-separated) |
| `TOKEN_COUNT_MULTIPLIER` | `1.0` | Token count multiplier for billing |
| `MAX_ERROR_COUNT` | `100` | Error threshold for auto-disable |
| `HTTP_PROXY` | `""` | HTTP proxy URL |
| `ENABLE_CONSOLE` | `true` | Enable web console |
| `ADMIN_PASSWORD` | `admin` | Console login password |
| `PORT` | `8000` | Server port |
| `LAZY_ACCOUNT_POOL_ENABLED` | `false` | Enable lazy account pool |
| `LAZY_ACCOUNT_POOL_SIZE` | `20` | Pool size for chat requests |
| `LAZY_ACCOUNT_POOL_REFRESH_OFFSET` | `10` | Refresh offset for pool |
| `LAZY_ACCOUNT_POOL_ORDER_BY` | `created_at` | Pool sorting field |
| `LAZY_ACCOUNT_POOL_ORDER_DESC` | `false` | Pool sorting direction |

### Database Support

**SQLite (Default):**
```bash
DATABASE_URL=""  # Uses data.sqlite3
```

**PostgreSQL:**
```bash
DATABASE_URL="postgres://user:pass@host:5432/db?sslmode=require"
```

**MySQL:**
```bash
DATABASE_URL="mysql://user:pass@host:3306/db"
```

## Deployment

### Docker Compose

```bash
docker-compose up -d
```

**Services:**
- Main API: `http://localhost:8000`
- Health check: `http://localhost:8000/healthz`
- API docs: `http://localhost:8000/docs`

### Production Considerations

1. **Security:**
   - Change `ADMIN_PASSWORD` to strong password
   - Configure `OPENAI_KEYS` whitelist
   - Use HTTPS reverse proxy (Nginx + Let's Encrypt)
   - Restrict database access

2. **Performance:**
   - Use multiple Uvicorn workers: `--workers 4`
   - Enable lazy account pool for large deployments
   - Configure connection pooling for PostgreSQL/MySQL

3. **Monitoring:**
   - Check `/healthz` endpoint
   - Monitor account `error_count` and `success_count`
   - Track token refresh failures

4. **Backup:**
   - Regular database backups
   - Export account credentials securely

## API Endpoints

### Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/chat/completions` | OpenAI Chat Completions API |
| `POST` | `/v1/messages` | Claude Messages API |
| `POST` | `/v1/messages/count_tokens` | Token counting (no request) |
| `GET` | `/healthz` | Health check |
| `GET` | `/docs` | Swagger UI |

### Admin Endpoints (Requires `ENABLE_CONSOLE=true` + Login)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/login` | Admin login |
| `GET` | `/login` | Login page |
| `GET` | `/` | Web console |
| `POST` | `/v2/accounts` | Create account |
| `POST` | `/v2/accounts/feed` | Batch create accounts |
| `GET` | `/v2/accounts` | List accounts |
| `GET` | `/v2/accounts/{id}` | Get account details |
| `PATCH` | `/v2/accounts/{id}` | Update account |
| `DELETE` | `/v2/accounts/{id}` | Delete account |
| `POST` | `/v2/accounts/{id}/refresh` | Refresh token |
| `POST` | `/v2/auth/start` | Start device auth |
| `GET` | `/v2/auth/status/{authId}` | Check auth status |
| `POST` | `/v2/auth/claim/{authId}` | Claim auth (5 min timeout) |

## Troubleshooting

### Common Issues

**401 Unauthorized:**
- Check `OPENAI_KEYS` configuration
- Verify at least one account is enabled
- Confirm API key is in whitelist

**502 Bad Gateway:**
- Token refresh failed (check `last_refresh_status`)
- Network connectivity issues
- Proxy configuration problems

**Empty Response:**
- Account disabled due to errors
- Amazon Q service unavailable
- Invalid request format

### Debug Steps

1. Check service health: `curl http://localhost:8000/healthz`
2. List accounts: `curl http://localhost:8000/v2/accounts -H "Authorization: Bearer <token>"`
3. Check account status: Look at `enabled`, `error_count`, `last_refresh_status`
4. Test token refresh: `curl -X POST http://localhost:8000/v2/accounts/{id}/refresh`
5. Review logs: `docker-compose logs -f` or check console output

## Development

### Local Setup

```bash
# Install dependencies
uv venv
uv pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Testing

```bash
# Test OpenAI endpoint
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4", "messages": [{"role": "user", "content": "test"}]}'

# Test Claude endpoint
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"model": "claude-sonnet-4.5", "max_tokens": 100, "messages": [{"role": "user", "content": "test"}]}'
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear description

## License

For learning and testing purposes only.

## Credits

- [amq2api](https://github.com/mucsbr/amq2api) - Claude message format conversion reference
- FastAPI - Modern Python web framework
- Amazon Q Developer - Underlying AI service
