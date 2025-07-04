# TeleFwdBot - Telegram 消息转发机器人

一个功能强大且可扩展的 Telegram 消息转发机器人，允许您管理多个用户帐户并设置自定义转发规则。
Telegram 版本的防撤回

## 功能特性

- **多用户管理**: 安全地添加、删除和列出被管理的 Telegram 帐户。
- **自定义转发规则**: 定义规则，将来自特定源聊天（用户、群组、频道）的消息转发到指定目的地。
- **健壮与异步**: 基于 Pyrogram 和 Asyncio 构建，性能卓越。
- **现代化工具**: 使用 `uv` 和 `pyproject.toml` 进行快速可靠的依赖管理。
- **日志轮转**: 自动轮转日志文件以节省空间，保留最近3天的日志。
- **服务管理**: 内置守护进程支持，支持启动/停止/重启功能。

## 先决条件

- Python 3.8+
- [uv](https://github.com/astral-sh/uv): 一个速度极快的 Python 包安装器和解析器。

## 项目初始化与设置

请按照以下步骤启动和运行机器人。

### 1. 克隆仓库 (可选)

如果您本地已有代码，可以跳过此步骤。

```bash
git clone git@github.com:xiabin/TelegramFowardBot.git
cd TeleFwdBot
```

### 2. 安装依赖

使用 `uv sync` 命令自动创建虚拟环境并从 `pyproject.toml` 安装所有依赖：

```bash
uv sync
```

这将自动：
- 创建虚拟环境（如果不存在）
- 安装 `pyproject.toml` 中定义的所有依赖
- 生成或更新 `uv.lock` 文件以锁定依赖版本

如需安装开发依赖，可以使用：

```bash
uv sync --extra dev
```

### 3. 配置环境变量

机器人通过 `.env` 文件进行配置。请在项目根目录中创建名为 `.env` 的文件，并添加以下内容。请将占位符值替换为您的实际凭据。

```ini
# 必填
API_ID=1234567
API_HASH=your_api_hash_from_my.telegram.org
BOT_TOKEN=your_bot_token_from_@BotFather
OWNER_ID=your_telegram_user_id

# 数据库
MONGO_URI=mongodb://localhost:27017/

# 可选: 用于将严重错误记录到指定频道
# LOG_CHANNEL=-1001234567890

# 可选: 日志等级设置 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# LOG_LEVEL=INFO

# 可选: 代理配置 (适用于所有客户端，包括机器人、用户客户端和临时认证客户端)
# PROXY_URL=socks5://user:pass@host:port
# PROXY_URL=http://proxy_host:port
```

- `API_ID` 和 `API_HASH`: 从 [my.telegram.org](https://my.telegram.org) 获取。
- `BOT_TOKEN`: 通过在 Telegram 上与 [@BotFather](https://t.me/BotFather) 创建一个新机器人来获取。
- `OWNER_ID`: 您的个人 Telegram 用户 ID。您可以从 [@userinfobot](https://t.me/userinfobot) 等机器人处获取。

### 4. 运行机器人

机器人包含服务管理脚本，支持守护进程操作。使用以下命令：

#### 服务管理（推荐）

```bash
# 启动机器人后台服务
./run.sh start

# 停止机器人服务
./run.sh stop

# 重启机器人服务
./run.sh restart

# 检查服务状态
./run.sh status

# 查看实时日志
./run.sh logs

# 显示帮助信息
./run.sh help
```

#### 其他运行方式

如果您更喜欢直接运行机器人：

**方式一：使用 uv run**
```bash
uv run python main.py
```

**方式二：直接运行**
```bash
python main.py
```

**方式三：通过环境变量运行**
```bash
API_ID=1234567 API_HASH=xxx BOT_TOKEN=xxx OWNER_ID=123456 uv run python main.py
```

## 服务管理功能

`run.sh` 脚本提供完整的守护进程功能：

- **后台运行**: 使用 `nohup` 作为守护进程运行
- **进程管理**: 自动 PID 文件管理和进程监控
- **优雅关闭**: 先发送 SIGTERM 信号，必要时使用 SIGKILL 强制终止
- **日志管理**: 所有输出重定向到 `logs/bot.log`
- **状态监控**: 查看进程信息和日志文件大小
- **实时日志**: 使用 `tail -f` 实时查看日志

### 文件位置

- **PID文件**: `.bot.pid`
- **日志文件**: `logs/bot.log`
- **配置文件**: `.env`

## 使用方法

在 Telegram 上与您的管理机器人进行交互。所有命令都仅限于您指定的 `OWNER_ID` 使用。

- `/adduser`: 开始一个对话，以添加并授权一个新的用户帐户进行管理。
- `/listusers`: 列出所有当前活动中的被管理用户帐户。
- `/deluser <user_id>`: 停用一个被管理的用户帐户。

- `/addrule <user_id> <source_id> <dest_id>`: 为被管理的用户添加一条转发规则。
- `/listrules <user_id>`: 列出特定用户的所有转发规则。
- `/delrule <rule_id>`: 通过其唯一ID删除一条特定的转发规则。

**注意:** 聊天 ID 可以是用户、群组或频道的 ID。对于频道和超级群组，它们是负数（例如 `-100123456789`）。 