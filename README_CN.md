# Amazon Q to API Bridge - 主服务

## Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=CassiopeiaCode/q2api&type=date&legend=top-left)](https://www.star-history.com/#CassiopeiaCode/q2api&type=date&legend=top-left)

将 Amazon Q Developer 转换为兼容 OpenAI 和 Claude API 的服务，支持多账号管理、流式响应和智能负载均衡。

**项目地址：**
- GitHub: https://github.com/CassiopeiaCode/q2api
- Codeberg: https://codeberg.org/Korieu/amazonq2api

**致谢：**
- 感谢 [amq2api](https://github.com/mucsbr/amq2api) 项目提供的 Claude 消息格式转换参考

## ✨ 核心特性

### API 兼容性
- **OpenAI Chat Completions API** - 完全兼容 `/v1/chat/completions` 端点
- **Claude Messages API** - 完全兼容 `/v1/messages` 端点，支持流式和非流式
- **Tool Use 支持** - 完整支持 Claude 格式的工具调用和结果返回
- **System Prompt** - 支持系统提示词和多模态内容（文本、图片）

### 账号管理
- **多账号支持** - 管理多个 Amazon Q 账号，灵活启用/禁用
- **自动令牌刷新** - 后台定时刷新过期令牌，请求时自动重试
- **智能统计** - 自动统计成功/失败次数，错误超阈值自动禁用
- **设备授权登录** - 通过 URL 快速登录并自动创建账号（5分钟超时）

### 负载与监控
- **随机负载均衡** - 从启用的账号中随机选择，均衡分配负载
- **Lazy 号池策略** - 可选的虚拟账号池，提高性能和账号利用率
- **健康检查** - 实时监控服务状态
- **Web 控制台** - 美观的前端界面，支持账号管理和 Chat 测试

### 网络与安全
- **HTTP 代理支持** - 可配置代理服务器，支持所有 HTTP 请求
- **API Key 白名单** - 可选的访问控制，支持开发模式
- **持久化存储** - 支持 SQLite（默认）、PostgreSQL、MySQL 数据库
- **会话管理** - 管理控制台登录会话有效期 30 天

## 🚀 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑 .env 文件（可选）
# 配置 OPENAI_KEYS、MAX_ERROR_COUNT 等

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

服务访问地址：
- 🏠 Web 控制台：http://localhost:8000/
- 💚 健康检查：http://localhost:8000/healthz
- 📘 API 文档：http://localhost:8000/docs

### 方式二：本地部署

#### 1. 安装依赖

推荐使用 `uv` 进行环境管理和依赖安装。

```bash
# 安装 uv
pip install uv

# 创建虚拟环境并安装依赖
uv venv
uv pip install -r requirements.txt
```

#### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 根据需要编辑 .env 文件
```

**.env 配置说明：**

```bash
# 数据库连接URL（留空使用本地SQLite）
# PostgreSQL: DATABASE_URL="postgres://user:password@host:5432/dbname?sslmode=require"
# MySQL: DATABASE_URL="mysql://user:password@host:3306/dbname"
DATABASE_URL=""

# OpenAI 风格 API Key 白名单（仅用于授权，与账号无关）
# 多个用逗号分隔，例如：OPENAI_KEYS="key1,key2,key3"
# 留空则为开发模式，不校验 Authorization
OPENAI_KEYS=""

# Token 计数倍率（影响 /v1/messages/count_tokens 和 /v1/messages 的输入 token 统计）
# 默认值为 1.0，可根据实际需要调整（如设置为 1.5 表示返回 1.5 倍的 token 数）
TOKEN_COUNT_MULTIPLIER="1.0"

# 出错次数阈值，超过此值自动禁用账号
MAX_ERROR_COUNT=100

# HTTP代理设置（留空不使用代理）
# 例如：HTTP_PROXY="http://127.0.0.1:7890"
HTTP_PROXY=""

# 管理控制台开关（默认启用）
# 设置为 "false" 或 "0" 可禁用管理控制台和相关API端点
ENABLE_CONSOLE="true"

# 管理控制台登录密码（默认 "admin"）
# 用于访问管理控制台的密码，会话有效期为30天
ADMIN_PASSWORD="admin"

# 主服务端口（默认 8000）
PORT=8000

# Lazy 号池策略（可选）
LAZY_ACCOUNT_POOL_ENABLED="false"
LAZY_ACCOUNT_POOL_SIZE=20
LAZY_ACCOUNT_POOL_REFRESH_OFFSET=10
LAZY_ACCOUNT_POOL_ORDER_BY="created_at"
LAZY_ACCOUNT_POOL_ORDER_DESC="false"
```

**配置要点：**
- `OPENAI_KEYS` 为空：开发模式，不校验 Authorization
- `OPENAI_KEYS` 设置后：仅白名单中的 key 可访问 API
- API Key 仅用于访问控制，不映射到特定账号
- 账号选择策略：从所有启用账号中随机选择
- `ENABLE_CONSOLE` 设为 `false` 或 `0`：禁用 Web 管理控制台和账号管理 API
- `ADMIN_PASSWORD`：管理控制台登录密码，默认为 "admin"，建议修改为强密码

#### 3. 启动服务

```bash
# 开发模式（带热重载）
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# 生产模式（4个worker）
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📖 使用指南

### 管理控制台登录

首次访问管理控制台需要登录：

1. 访问 http://localhost:8000/ 将自动跳转到登录页面
2. 输入管理员密码（默认为 `admin`，可通过 `ADMIN_PASSWORD` 环境变量配置）
3. 登录成功后，会话有效期为 **30 天**
4. 会话过期后需要重新登录

**安全建议：**
- 生产环境务必修改 `ADMIN_PASSWORD` 为强密码
- 登录凭证存储在浏览器 localStorage 中
- 所有管理 API 请求需要在 Authorization 头中携带会话 token

### 账号管理

#### 方式一：Web 控制台（推荐）

登录管理控制台后，使用可视化界面：
- 查看所有账号及详细状态
- URL 登录（设备授权）快速添加账号
- 创建/删除/编辑账号
- 启用/禁用账号切换
- 手动刷新 Token
- Chat 功能测试

#### 方式二：URL 登录（最简单）

快速添加账号的推荐方式：

1. **启动登录流程**
```bash
curl -X POST http://localhost:8000/v2/auth/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-admin-token>" \
  -d '{"label": "我的账号", "enabled": true}'
```

2. **在浏览器中打开返回的 `verificationUriComplete` 完成登录**

3. **等待并创建账号**（最多5分钟）
```bash
curl -X POST http://localhost:8000/v2/auth/claim/{authId} \
  -H "Authorization: Bearer <your-admin-token>"
```

成功后自动创建并启用账号，立即可用。

#### 方式三：REST API 手动管理

**注意：** 所有管理 API 请求需要携带登录凭证（Authorization Bearer Token）

**先登录获取 Token**
```bash
# 登录并获取 token
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"password": "admin"}' \
  | jq -r '.token'
```

登录成功后，返回格式：
```json
{
  "success": true,
  "message": "Login successful"
}
```

**创建账号**
```bash
curl -X POST http://localhost:8000/v2/accounts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-admin-token>" \
  -d '{
    "label": "手动创建的账号",
    "clientId": "your-client-id",
    "clientSecret": "your-client-secret",
    "refreshToken": "your-refresh-token",
    "enabled": true
  }'
```

**列出所有账号**
```bash
curl http://localhost:8000/v2/accounts \
  -H "Authorization: Bearer <your-admin-token>"
```

**更新账号**
```bash
curl -X PATCH http://localhost:8000/v2/accounts/{account_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-admin-token>" \
  -d '{"enabled": false}'
```

**刷新 Token**
```bash
curl -X POST http://localhost:8000/v2/accounts/{account_id}/refresh \
  -H "Authorization: Bearer <your-admin-token>"
```

**删除账号**
```bash
curl -X DELETE http://localhost:8000/v2/accounts/{account_id} \
  -H "Authorization: Bearer <your-admin-token>"
```

### OpenAI 兼容 API

#### 非流式请求

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "claude-sonnet-4",
    "stream": false,
    "messages": [
      {"role": "system", "content": "你是一个乐于助人的助手"},
      {"role": "user", "content": "你好，请讲一个简短的故事"}
    ]
  }'
```

#### 流式请求（SSE）

```bash
curl -N -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "claude-sonnet-4",
    "stream": true,
    "messages": [
      {"role": "user", "content": "讲一个笑话"}
    ]
  }'
```

#### Python 示例

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"  # 如果配置了 OPENAI_KEYS
)

response = client.chat.completions.create(
    model="claude-sonnet-4",
    messages=[
        {"role": "user", "content": "你好"}
    ]
)

print(response.choices[0].message.content)
```

### Claude Messages API

本项目完整支持 Claude Messages API 格式，包括流式响应、工具调用、多模态内容等。

#### 基础文本对话

```bash
curl -X POST http://localhost:8000/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "model": "claude-sonnet-4.5",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "你好"}
    ]
  }'
```

#### Python SDK 示例

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"
)

# 基础对话
message = client.messages.create(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "你好"}
    ]
)
print(message.content[0].text)

# 流式响应
with client.messages.stream(
    model="claude-sonnet-4.5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "写一首诗"}
    ]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

#### Token 计数

```bash
curl -X POST http://localhost:8000/v1/messages/count_tokens \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4.5",
    "messages": [
      {"role": "user", "content": "你好，这是一条测试消息"}
    ]
  }'
```

返回格式：
```json
{
  "input_tokens": 15
}
```

## 🔐 授权与账号选择

### 授权机制
- **开发模式**（`OPENAI_KEYS` 未设置）：不校验 Authorization
- **生产模式**（`OPENAI_KEYS` 已设置）：必须提供白名单中的 key

### 账号选择策略
- **默认策略**：从所有 `enabled=1` 的账号中**随机选择**
- **Lazy 号池策略**：启用后，从排序后的前 N 个账号中随机选择，提高性能和账号利用率
- API Key 不映射到特定账号（与 AWS 账号解耦）
- 无可用账号时返回 401

### Token 自动刷新
- **后台刷新**：每5分钟检查一次，超过25分钟未刷新的令牌自动刷新
- **请求时刷新**：若账号缺少 accessToken，自动刷新后重试
- **手动刷新**：支持通过 API 或 Web 控制台手动刷新

## 🏗️ 架构设计

### 请求流程：Claude API → Amazon Q

服务作为协议转换器，连接 Claude Messages API 和 Amazon Q 内部 API：

1. **API 层** ([app.py](app.py))：FastAPI 端点接收 Claude 或 OpenAI 格式请求
2. **转换** ([claude_converter.py](claude_converter.py))：将 Claude 请求转换为 Amazon Q 格式
   - 映射消息角色：`user` → `userInputMessage`，`assistant` → `aiMessage`
   - 转换工具定义到 Amazon Q schema
   - 处理多模态内容（文本、图片）
3. **上游** ([replicate.py](replicate.py))：使用 OIDC token 发送请求到 Amazon Q
   - 解析二进制事件流协议
   - 提取事件：`assistantResponseEvent`，`codeReferenceEvent` 等
4. **响应** ([claude_stream.py](claude_stream.py))：将 Amazon Q 事件转换回 Claude SSE 格式
   - 生成：`message_start`，`content_block_delta`，`message_stop` 等

### 核心模块职责

- **[app.py](app.py)** - 主 FastAPI 应用、账号管理、令牌刷新、API 端点
- **[db.py](db.py)** - 数据库抽象层（SQLite/PostgreSQL/MySQL），基于 `DATABASE_URL` 自动选择
- **[replicate.py](replicate.py)** - Amazon Q 请求复制、二进制事件流解析
- **[auth_flow.py](auth_flow.py)** - 设备授权流程（通过 AWS OIDC URL 登录）
- **[claude_types.py](claude_types.py)** - Claude API 的 Pydantic 模型
- **[claude_converter.py](claude_converter.py)** - Claude → Amazon Q 请求转换
- **[claude_parser.py](claude_parser.py)** - Amazon Q 事件流解析（提取文本、引用、错误）
- **[claude_stream.py](claude_stream.py)** - Amazon Q → Claude SSE 响应生成

### 账号管理

账号存储在 `accounts` 表中，关键字段：
- `enabled`：1=启用，0=禁用
- `error_count`：失败时自动递增，成功时重置
- `success_count`：跟踪成功请求
- `accessToken`/`refreshToken`：OIDC 令牌（每 25 分钟自动刷新）

**选择策略：**
- 默认：从所有 `enabled=1` 账号中随机选择
- Lazy 号池：当 `LAZY_ACCOUNT_POOL_ENABLED=true` 时，从排序后的前 N 个账号中选择

**自动禁用：** 当 `error_count >= MAX_ERROR_COUNT` 时，账号自动禁用

### Token 刷新机制

两种机制：
1. **后台任务** (`_refresh_stale_tokens`)：每5分钟运行一次，刷新超过25分钟的令牌
2. **按需刷新**：如果请求时 `accessToken` 缺失，触发立即刷新

## 🔧 高级配置

### 环境变量

| 变量 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `DATABASE_URL` | 数据库连接URL | 空（使用SQLite） | `"postgres://user:pass@host:5432/db"` |
| `OPENAI_KEYS` | API Key 白名单（逗号分隔） | 空（开发模式） | `"key1,key2"` |
| `TOKEN_COUNT_MULTIPLIER` | Token 计数倍率 | `1.0` | `"1.5"` |
| `MAX_ERROR_COUNT` | 错误次数阈值 | 100 | `50` |
| `HTTP_PROXY` | HTTP代理地址 | 空 | `"http://127.0.0.1:7890"` |
| `ENABLE_CONSOLE` | 管理控制台开关 | `"true"` | `"false"` |
| `ADMIN_PASSWORD` | 管理控制台登录密码 | `"admin"` | `"your-secure-password"` |
| `PORT` | 服务端口 | 8000 | `8080` |
| `LAZY_ACCOUNT_POOL_ENABLED` | 是否启用 Lazy 号池 | `"false"` | `"true"` |
| `LAZY_ACCOUNT_POOL_SIZE` | Lazy 号池大小（聊天） | `20` | `50` |
| `LAZY_ACCOUNT_POOL_REFRESH_OFFSET` | Lazy 号池刷新偏移量 | `10` | `20` |
| `LAZY_ACCOUNT_POOL_ORDER_BY` | Lazy 号池排序字段 | `"created_at"` | `"success_count"` |
| `LAZY_ACCOUNT_POOL_ORDER_DESC` | Lazy 号池是否降序 | `"false"` | `"true"` |

### Lazy 号池策略

Lazy 号池是一种优化策略，可以提高账号利用率和服务性能：

**工作原理：**
- 从所有启用账号中，按指定字段排序
- 只从前 N 个账号中随机选择（N = `LAZY_ACCOUNT_POOL_SIZE`）
- 后台刷新时，刷新前 N + Offset 个账号（Offset = `LAZY_ACCOUNT_POOL_REFRESH_OFFSET`）

**适用场景：**
- 账号数量较多（>100）
- 希望优先使用某些账号（如新创建的账号、成功率高的账号）
- 减少不必要的 token 刷新开销

**配置示例：**
```bash
LAZY_ACCOUNT_POOL_ENABLED="true"
LAZY_ACCOUNT_POOL_SIZE=20              # 只从前 20 个账号中选择
LAZY_ACCOUNT_POOL_REFRESH_OFFSET=10    # 刷新前 30 个账号
LAZY_ACCOUNT_POOL_ORDER_BY="created_at" # 按创建时间排序
LAZY_ACCOUNT_POOL_ORDER_DESC="true"    # 降序（最新的在前）
```

### 数据库结构

```sql
CREATE TABLE accounts (
    id TEXT PRIMARY KEY,                -- UUID
    label TEXT,                         -- 账号标签
    clientId TEXT,                      -- OIDC 客户端 ID
    clientSecret TEXT,                  -- OIDC 客户端密钥
    refreshToken TEXT,                  -- 刷新令牌
    accessToken TEXT,                   -- 访问令牌
    other TEXT,                         -- JSON 格式的额外信息
    last_refresh_time TEXT,             -- 最后刷新时间
    last_refresh_status TEXT,           -- 最后刷新状态
    created_at TEXT,                    -- 创建时间
    updated_at TEXT,                    -- 更新时间
    enabled INTEGER DEFAULT 1,          -- 1=启用, 0=禁用
    error_count INTEGER DEFAULT 0,      -- 连续错误次数
    success_count INTEGER DEFAULT 0     -- 成功请求次数
);
```

## 📝 完整 API 端点列表

### 管理员认证（需启用 ENABLE_CONSOLE）
- `POST /api/login` - 管理员登录，获取会话 token
- `GET /login` - 登录页面
- `GET /login.html` - 登录页面（备用路径）

### 账号管理（需启用 ENABLE_CONSOLE，需登录）
- `POST /v2/accounts` - 创建账号
- `POST /v2/accounts/feed` - 批量创建账号（后台验证）
- `GET /v2/accounts` - 列出所有账号
- `GET /v2/accounts/{id}` - 获取账号详情
- `PATCH /v2/accounts/{id}` - 更新账号
- `DELETE /v2/accounts/{id}` - 删除账号
- `POST /v2/accounts/{id}/refresh` - 刷新 Token

### 设备授权（需启用 ENABLE_CONSOLE，需登录）
- `POST /v2/auth/start` - 启动登录流程
- `GET /v2/auth/status/{authId}` - 查询登录状态
- `POST /v2/auth/claim/{authId}` - 等待并创建账号（最多5分钟）

### OpenAI 兼容
- `POST /v1/chat/completions` - Chat Completions API

### Claude 兼容
- `POST /v1/messages` - Messages API（支持流式、工具调用、多模态）
- `POST /v1/messages/count_tokens` - Token 计数接口（预先统计消息的 token 数量）

### 其他
- `GET /` - Web 控制台首页（需启用 ENABLE_CONSOLE，需登录）
- `GET /healthz` - 健康检查
- `GET /docs` - API 文档（Swagger UI）

## 📁 项目结构

```
q2api/
├── app.py                          # FastAPI 主应用
├── db.py                           # 数据库抽象层 (SQLite/PG/MySQL)
├── replicate.py                    # Amazon Q 请求复刻
├── auth_flow.py                    # 设备授权登录
├── claude_types.py                 # Claude API 类型定义
├── claude_converter.py             # Claude 到 Amazon Q 转换
├── claude_parser.py                # Event Stream 解析
├── claude_stream.py                # Claude SSE 流式处理
├── requirements.txt                # Python 依赖
├── .env.example                    # 环境变量示例
├── .env                            # 环境变量配置（需自行创建）
├── docker-compose.yml              # Docker Compose 配置
├── Dockerfile                      # Docker 镜像配置
├── data.sqlite3                    # SQLite 数据库（自动创建）
├── README.md                       # 英文文档
├── README_CN.md                    # 中文文档
├── CLAUDE.md                       # Claude Code 开发指南
├── templates/
│   └── streaming_request.json      # Amazon Q 请求模板
├── frontend/
│   ├── index.html                  # Web 控制台
│   └── login.html                  # 登录页面
└── scripts/
    ├── account_stats.py            # 账号统计脚本
    ├── retry_failed_accounts.py    # 重试失败账号脚本
    ├── reset_accounts.py           # 重置账号脚本
    ├── delete_disabled_zero_success_accounts.py  # 删除无效账号
    └── migrate_db.py               # 数据库迁移脚本
```

## 🛠️ 技术栈

- **后端框架**: FastAPI + Python 3.11+
- **数据库**: SQLite3 (aiosqlite) / PostgreSQL (asyncpg) / MySQL (aiomysql)
- **HTTP 客户端**: httpx（支持异步和代理）
- **Token 计数**: tiktoken
- **前端**: 纯 HTML/CSS/JavaScript（无依赖）
- **认证**: AWS OIDC 设备授权流程

## 🐛 故障排查

### 401 Unauthorized
**可能原因：**
- API Key 不在 `OPENAI_KEYS` 白名单中
- 没有启用的账号（`enabled=1`）
- 管理控制台登录凭证过期

**解决方法：**
1. 检查 `.env` 中的 `OPENAI_KEYS` 配置
2. 访问 `/v2/accounts` 确认至少有一个启用的账号
3. 重新登录管理控制台获取新凭证

### Token 刷新失败
**可能原因：**
- refreshToken 已过期
- 网络连接问题
- AWS OIDC 服务不可用

**解决方法：**
1. 查看账号的 `last_refresh_status` 字段
2. 检查网络连接和代理配置
3. 删除旧账号，通过 URL 登录重新添加

### 数据库锁定错误
**可能原因：**
- SQLite 并发写入冲突
- 数据库文件权限问题

**解决方法：**
1. 使用 PostgreSQL 或 MySQL 替代 SQLite（推荐生产环境）
2. 检查数据库文件权限
3. 减少并发请求数量

### 流式响应中断
**可能原因：**
- 客户端断开连接
- 上游服务超时
- 网络不稳定

**解决方法：**
1. 检查客户端超时设置
2. 检查代理服务器配置
3. 增加 `read` 超时时间（在 [app.py:165](app.py#L165) 中配置）

## 🚀 生产环境部署

### Uvicorn 多进程模式

```bash
# 使用多个 worker 提高并发性能
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # SSE 支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

### Docker 部署

```bash
# 构建镜像
docker build -t q2api:latest .

# 运行容器
docker run -d \
  --name q2api \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/data.sqlite3:/app/data.sqlite3 \
  q2api:latest
```

### 使用 PostgreSQL（推荐）

```bash
# 1. 启动 PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=q2api \
  -p 5432:5432 \
  postgres:15

# 2. 配置 DATABASE_URL
echo 'DATABASE_URL="postgresql://postgres:yourpassword@localhost:5432/q2api"' >> .env

# 3. 启动服务
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔒 安全建议

1. **生产环境必须修改 `ADMIN_PASSWORD` 为强密码**
2. **生产环境必须配置 `OPENAI_KEYS`**
3. **使用 HTTPS 反向代理（Nginx + Let's Encrypt）**
4. **定期备份数据库**（SQLite: `data.sqlite3`，或 PG/MySQL 数据库）
5. **限制数据库访问权限**
6. **配置防火墙规则，限制访问来源**
7. **管理控制台会话有效期为 30 天，建议定期重新登录**
8. **使用 PostgreSQL 或 MySQL 替代 SQLite（生产环境）**
9. **启用 Lazy 号池策略以提高性能**
10. **定期清理禁用账号和错误日志**

## 🔧 常见开发模式

### 添加新 API 端点

1. 在 [app.py](app.py) 中定义 Pydantic 请求/响应模型
2. 使用 `@app.post()` 或 `@app.get()` 添加端点
3. 对需要账号选择的端点使用 `Depends(require_account)`
4. 对管理员端点使用 `Depends(verify_admin_password)`
5. 使用 `await _update_stats(account_id, success: bool)` 更新账号统计

### 修改 Claude → Amazon Q 转换

编辑 [claude_converter.py](claude_converter.py)：
- `convert_claude_to_amazonq_request()`：主转换函数
- `convert_tool()`：工具定义映射
- `extract_images_from_content()`：多模态内容处理

### 修改事件流解析

编辑 [claude_parser.py](claude_parser.py)：
- `EventStreamParser.parse_stream()`：主解析逻辑
- `extract_event_info()`：事件类型提取

### 数据库 Schema 变更

1. 修改 [db.py](db.py) 中的 schema（所有三个后端：SQLite、PostgreSQL、MySQL）
2. 对现有部署，在 `scripts/migrate_db.py` 中创建迁移脚本
3. 使用所有三个数据库后端测试

## 📄 许可证

本项目仅供学习和测试使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

**贡献指南：**
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 🙏 致谢

- [amq2api](https://github.com/mucsbr/amq2api) - Claude 消息格式转换参考
- FastAPI - 现代 Python Web 框架
- Amazon Q Developer - 底层 AI 服务
- 所有贡献者和用户的支持

## 📞 联系方式

- GitHub Issues: https://github.com/CassiopeiaCode/q2api/issues
- Codeberg Issues: https://codeberg.org/Korieu/amazonq2api/issues

## 📚 相关文档

- [CLAUDE.md](CLAUDE.md) - Claude Code 开发指南
- [README.md](README.md) - 英文文档
- [API 文档](http://localhost:8000/docs) - Swagger UI（需启动服务）
