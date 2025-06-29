# TeleFwdBot - Telegram Message Forwarding Bot

A powerful and extensible Telegram message forwarding bot that allows you to manage multiple user accounts and set up custom forwarding rules. Includes anti-revoke features for Telegram.

## Features

- **Multi-user management**: Securely add, remove, and list managed Telegram accounts.
- **Custom forwarding rules**: Define rules to forward messages from specific source chats (users, groups, channels) to designated destinations.
- **Robust & Asynchronous**: Built with Pyrogram and Asyncio for excellent performance.
- **Modern tooling**: Uses `uv` and `pyproject.toml` for fast and reliable dependency management.
- **Log rotation**: Automatically rotates log files to save space, keeping logs for the last 3 days.
- **Service management**: Built-in daemon support with start/stop/restart functionality.

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv): A lightning-fast Python package installer and resolver.

## Project Initialization & Setup

Follow these steps to start and run the bot.

### 1. Clone the Repository (Optional)

Skip this step if you already have the code locally.

```bash
git clone git@github.com:xiabin/TelegramFowardBot.git
cd TeleFwdBot
```

### 2. Install Dependencies

Use the `uv sync` command to automatically create a virtual environment and install all dependencies from `pyproject.toml`:

```bash
uv sync
```

This will automatically:
- Create a virtual environment (if it doesn't exist)
- Install all dependencies defined in `pyproject.toml`
- Generate or update the `uv.lock` file to lock dependency versions

To install development dependencies, use:

```bash
uv sync --extra dev
```

### 3. Configure Environment Variables

The bot is configured via a `.env` file. Create a file named `.env` in the project root and add the following content, replacing placeholder values with your actual credentials.

```ini
# Required
API_ID=1234567
API_HASH=your_api_hash_from_my.telegram.org
BOT_TOKEN=your_bot_token_from_@BotFather
OWNER_ID=your_telegram_user_id

# Database
MONGO_URI=mongodb://localhost:27017/

# Optional: Log severe errors to a specific channel
# LOG_CHANNEL=-1001234567890

# Optional: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# LOG_LEVEL=INFO

# Optional: Proxy configuration (applies to all clients, including bot, user clients, and temporary auth clients)
# PROXY_URL=socks5://user:pass@host:port
# PROXY_URL=http://proxy_host:port
```

- `API_ID` and `API_HASH`: Obtain from [my.telegram.org](https://my.telegram.org).
- `BOT_TOKEN`: Obtain by creating a new bot with [@BotFather](https://t.me/BotFather) on Telegram.
- `OWNER_ID`: Your personal Telegram user ID. You can get it from bots like [@userinfobot](https://t.me/userinfobot).

### 4. Run the Bot

The bot includes a service management script that supports daemon operation. Use the following commands:

#### Service Management (Recommended)

```bash
# Start the bot as a background service
./run.sh start

# Stop the bot service
./run.sh stop

# Restart the bot service
./run.sh restart

# Check service status
./run.sh status

# View real-time logs
./run.sh logs

# Show help
./run.sh help
```

#### Alternative Methods

If you prefer to run the bot directly:

**Method 1: Using uv run**
```bash
uv run python main.py
```

**Method 2: Direct execution**
```bash
python main.py
```

**Method 3: With environment variables**
```bash
API_ID=1234567 API_HASH=xxx BOT_TOKEN=xxx OWNER_ID=123456 uv run python main.py
```

## Service Management Features

The `run.sh` script provides full daemon functionality:

- **Background operation**: Runs as a daemon process using `nohup`
- **Process management**: Automatic PID file management and process monitoring
- **Graceful shutdown**: SIGTERM followed by SIGKILL if necessary
- **Log management**: All output redirected to `logs/bot.log`
- **Status monitoring**: View process information and log file size
- **Real-time logging**: Live log viewing with `tail -f`

### File Locations

- **PID file**: `.bot.pid`
- **Log file**: `logs/bot.log`
- **Config file**: `.env`

## Usage

Interact with your management bot on Telegram. All commands are restricted to the `OWNER_ID` you specified.

- `/adduser`: Start a conversation to add and authorize a new user account for management.
- `/listusers`: List all currently active managed user accounts.
- `/deluser <user_id>`: Deactivate a managed user account.

- `/addrule <user_id> <source_id> <dest_id>`: Add a forwarding rule for a managed user.
- `/listrules <user_id>`: List all forwarding rules for a specific user.
- `/delrule <rule_id>`: Delete a specific forwarding rule by its unique ID.

**Note:** Chat IDs can be user, group, or channel IDs. For channels and supergroups, they are negative numbers (e.g., `-100123456789`). 