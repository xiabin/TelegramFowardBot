# TeleFwdBot - Telegram 消息转发机器人

一个功能强大且可扩展的 Telegram 消息转发机器人，允许您管理多个用户帐户并设置自定义转发规则。

## 功能特性

- **多用户管理**: 安全地添加、删除和列出被管理的 Telegram 帐户。
- **自定义转发规则**: 定义规则，将来自特定源聊天（用户、群组、频道）的消息转发到指定目的地。
- **健壮与异步**: 基于 Pyrogram 和 Asyncio 构建，性能卓越。
- **现代化工具**: 使用 `uv` 和 `pyproject.toml` 进行快速可靠的依赖管理。
- **日志轮转**: 自动轮转日志文件以节省空间，保留最近3天的日志。

## 先决条件

- Python 3.8+
- [uv](https://github.com/astral-sh/uv): 一个速度极快的 Python 包安装器和解析器。

## 项目初始化与设置

请按照以下步骤启动和运行机器人。

### 1. 克隆仓库 (可选)

如果您本地已有代码，可以跳过此步骤。

```bash
git clone <your-repository-url>
cd TeleFwdBot
```

### 2. 创建并激活虚拟环境

本项目使用 `uv` 管理虚拟环境和依赖项。

首先，创建虚拟环境。此命令将在您的项目文件夹中创建一个 `.venv` 目录。

```bash
uv venv
```

接下来，激活虚拟环境。

**在 macOS 和 Linux 上:**
```bash
source .venv/bin/activate
```

**在 Windows 上:**
```bash
.venv\Scripts\activate
```

您的终端提示符现在应以 `(.venv)` 开头，表示虚拟环境已激活。

### 3. 安装依赖

在虚拟环境激活状态下，`uv` 可以直接从 `pyproject.toml` 文件中安装所有必需的包。

```bash
uv pip install -e .
```
*(注意: 使用 `-e .` 会以"可编辑"模式安装项目，这在开发中是很好的实践。)*

### 4. 配置环境变量

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

# 可选: 代理配置
# USE_PROXY=True
# HTTP_PROXY=http://your_proxy_address:port
```

- `API_ID` 和 `API_HASH`: 从 [my.telegram.org](https://my.telegram.org) 获取。
- `BOT_TOKEN`: 通过在 Telegram 上与 [@BotFather](https://t.me/BotFather) 创建一个新机器人来获取。
- `OWNER_ID`: 您的个人 Telegram 用户 ID。您可以从 [@userinfobot](https://t.me/userinfobot) 等机器人处获取。

### 5. 运行机器人

现在您已准备好启动应用程序。

```bash
python main.py
```

机器人将会启动，连接到 Telegram，并初始化数据库中找到的所有被管理的用户客户端。

## 使用方法

在 Telegram 上与您的管理机器人进行交互。所有命令都仅限于您指定的 `OWNER_ID` 使用。

- `/adduser`: 开始一个对话，以添加并授权一个新的用户帐户进行管理。
- `/listusers`: 列出所有当前活动中的被管理用户帐户。
- `/deluser <user_id>`: 停用一个被管理的用户帐户。

- `/addrule <user_id> <source_id> <dest_id>`: 为被管理的用户添加一条转发规则。
- `/listrules <user_id>`: 列出特定用户的所有转发规则。
- `/delrule <rule_id>`: 通过其唯一ID删除一条特定的转发规则。

**注意:** 聊天 ID 可以是用户、群组或频道的 ID。对于频道和超级群组，它们是负数（例如 `-100123456789`）。 