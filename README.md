# 🎬 THUMBIFY — Telegram Auto Thumbnail Bot

**THUMBIFY** is a modular, personal Telegram bot built using **Python 3.12+**, **Telethon (Telegram MTProto)**, and **Pillow**. It automatically applies your permanently configured custom thumbnail image to any video or document file you upload, returning the processed media back to your private Telegram chat while preserving original filenames, extensions, and captions.

---

## 🌟 Key Features

- **Direct Telegram MTProto Engine:** Uses Telethon to stream large files (200 MB–400 MB+) directly over Telegram MTProto. Unlike the standard Telegram HTTP Bot API (which imposes strict 20 MB upload and 50 MB download limits), MTProto allows bot accounts to transfer files up to 2,000 MB (2 GB) without requiring a local Telegram Bot API server.
- **Fixed Permanent Thumbnail:** Automatically loads, validates, resizes, and compresses `assets/thumbnail.jpg` at startup (optimized to 320×180 JPEG, ≤ 20 KB) and applies it to every file without re-prompting.
- **Video & Document Support:**
  - **Videos:** MP4, MKV, MOV, AVI, WEBM, FLV, WMV, 3GP, TS (with video attributes: duration, width, height, and streaming enabled).
  - **Documents / Archives:** PDF, ZIP, RAR, APK, DOCX, XLSX, PPTX, TXT, and all other Telegram-supported document types.
- **Strict Owner-Only Security:** Every request is authenticated against your numeric `OWNER_ID`. Unauthorized users and group messages are blocked/ignored.
- **Streaming Transfer with Throttled Progress:** Transfers files in streaming chunks (preventing RAM exhaustion) with throttled Telegram message edits to avoid `FloodWait` limits.
- **Active Job Control:** Single-job concurrency protection with safe job cancellation via `/cancel`.
- **Automatic Cleanup:** Safely cleans up temporary downloads and incomplete transfers upon completion or failure.
- **Production-Ready Logging:** Rotating file logs (`logs/thumbify.log`) and console logging with automatic credential masking.

---

## 📁 Project Architecture

```
THUMBIFY/
│
├── app/
│   ├── __init__.py          # Package initialization & version
│   ├── config.py            # Environment configuration & validation
│   ├── bot.py               # Telethon MTProto client coordinator
│   ├── main.py              # Application entrypoint & graceful exit
│   │
│   ├── handlers/            # Event dispatchers & commands
│   │   ├── __init__.py
│   │   ├── start.py         # /start handler
│   │   ├── commands.py      # /help, /status, /id, /cancel, /thumbnail, /info
│   │   └── uploads.py       # Video & document media upload dispatcher
│   │
│   ├── services/            # Core business logic
│   │   ├── __init__.py
│   │   ├── thumbnail.py     # Fixed thumbnail validation, resizing & caching
│   │   ├── file_transfer.py # Large-file streaming transfer & progress tracking
│   │   ├── media_info.py    # Media inspection (Hachoir & FFprobe)
│   │   └── cleanup.py       # Safe temporary file cleanup & stale file purging
│   │
│   └── utils/               # Helpers & cross-cutting concerns
│       ├── __init__.py
│       ├── validators.py    # Filename sanitization, path traversal & size checks
│       └── logger.py        # Rotating file logger with secret redaction
│
├── assets/
│   └── thumbnail.jpg        # Your fixed thumbnail image
│
├── downloads/               # Temporary transfer workspace
├── logs/                    # Rotating log files
│
├── tests/                   # Automated pytest suite
│   ├── test_config.py
│   ├── test_thumbnail.py
│   ├── test_validators.py
│   ├── test_cleanup.py
│   └── test_bot_handlers.py
│
├── .env.example             # Configuration template
├── .gitignore               # Ignored secrets, sessions, and temp files
├── requirements.txt         # Pinned production dependencies
├── pytest.ini               # Pytest configuration
├── run.bat                  # One-click Windows launcher
├── Dockerfile               # Production Docker container
├── docker-compose.yml       # Docker Compose definition
└── README.md                # Comprehensive documentation
```

---

## ⚙️ Prerequisites & Installation

### Windows 10/11 Setup

1. **Install Python 3.12 or newer**:
   - Download from [python.org](https://www.python.org/downloads/).
   - **Important:** Ensure you check **"Add python.exe to PATH"** during setup.

2. **Open PowerShell in the project directory**:
   ```powershell
   cd "d:\Eniyan\My Websites\Thumbify"
   ```

3. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. **Install pinned dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🔑 Obtaining Telegram Credentials

### 1. Telegram API ID and API Hash
1. Log in to [my.telegram.org](https://my.telegram.org) with your Telegram phone number.
2. Go to **"API development tools"**.
3. Create a new application (e.g. app title `Thumbify`, short name `thumbify`).
4. Copy the numeric **`api_id`** (e.g., `12345678`) and string **`api_hash`** (e.g., `0123456789abcdef0123456789abcdef`).

### 2. Bot Token from BotFather
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to choose a name and username (ending in `bot`, e.g. `MyPersonalThumbifyBot`).
3. Copy the token provided (format: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 3. Finding Your Owner User ID
1. Search for [@userinfobot](https://t.me/userinfobot) on Telegram and start it.
2. Note your numeric **Id** (e.g. `987654321`).
3. Alternatively, start your THUMBIFY bot, send `/id`, and check the bot console output.

---

## 🖼 Fixed Thumbnail Setup

Place your desired thumbnail image at `assets/thumbnail.jpg`.

- **Recommended specs:** 320 × 180 pixels, JPEG format, ≤ 20 KB.
- **Automatic Handling:** If your image is in another format (PNG, WEBP) or larger (e.g. 1920×1080, 2 MB), THUMBIFY will automatically convert, resize, and compress it into an optimized compliant JPEG stored at `assets/thumbnail_optimized.jpg`.
- The thumbnail is loaded and verified once at bot startup and reused for all subsequent files.

---

## 🚀 Running the Bot

### Option 1: One-Click Windows Launcher
Double-click `run.bat` or execute in terminal:
```cmd
run.bat
```

### Option 2: PowerShell / Command Line
```powershell
# Copy template and edit credentials
cp .env.example .env

# Run the bot
.\.venv\Scripts\python.exe -m app.main
```

---

## 💬 Bot Commands Reference

| Command | Description |
| :--- | :--- |
| `/start` | Displays welcome message and usage instructions. |
| `/help` | Displays supported file types, size limits, and tips. |
| `/status` | Displays uptime, active jobs, thumbnail status, and limits. |
| `/thumbnail` | Sends a preview of your active fixed thumbnail with metadata. |
| `/cancel` | Safely cancels the active in-progress transfer job. |
| `/id` | Displays your numeric Telegram user ID and confirms owner role. |
| `/info` | Displays engine version, Python version, and system config. |

---

## 📱 Testing via Telegram on Android

1. Open Telegram on your Android device.
2. Open the private chat with your bot.
3. Send `/start` to verify connectivity.
4. Send `/thumbnail` to confirm your fixed thumbnail is rendered properly.
5. Tap the attachment icon (📎), select a video or document (e.g. a 50 MB MP4 or a 100 MB ZIP), and send it.
6. The bot will send live progress updates:
   - `⏳ File received. Validating...`
   - `📥 Starting download...`
   - `🎨 Applying fixed thumbnail...`
   - `📤 Uploading processed file...`
   - `✅ Completed successfully!`
7. On Android Telegram:
   - **Videos:** The custom thumbnail appears in the video player thumbnail preview and streams inline.
   - **Documents:** The custom thumbnail displays as the file icon/cover preview. Note that document thumbnail rendering depends on Android Telegram's local thumbnail caching and file type support.

---

## 🧪 Manual Integration Test Plan

| Target File | Expected Behavior | Verification |
| :--- | :--- | :--- |
| **10 MB MP4** | Rapid transfer (~3-10s), thumbnail applied, inline playback enabled. | Verify thumbnail in chat list & player. |
| **50 MB MP4** | Smooth transfer, progress throttled every 3-4s without FloodWait. | Video plays inline with custom cover. |
| **100 MB PDF** | Document transfer with fixed thumbnail attached as document icon. | Filename and extension preserved. |
| **200 MB ZIP** | Large document streaming, verified within application limit. | Download opens as valid archive. |
| **400 MB MP4** | Stress test for MTProto chunk streaming, RAM remains low (<100 MB). | Verifies large file capability. |
| **400 MB MKV** | MKV container handling with video duration/dimension detection. | Verifies non-MP4 container support. |

---

## 🔒 Security Best Practices

1. **Protect `.env` and Session Files:**
   - Never commit `.env` or `*.session` files. These are listed in `.gitignore`.
2. **Path Traversal Protection:**
   - All filenames received from Telegram are sanitized via `sanitize_filename()` to prevent directory traversal (`../`, absolute paths, control characters).
3. **Owner-Only Enforcement:**
   - Any message from a `sender_id` other than `OWNER_ID` is silently dropped and logged.
4. **Token Revocation Guide:**
   - If your bot token is accidentally exposed:
     1. Open Telegram and message [@BotFather](https://t.me/BotFather).
     2. Send `/mybots`, select your bot, and navigate to **API Token** > **Revoke current token**.
     3. Update `TG_BOT_TOKEN` in your `.env` file and restart THUMBIFY.

---

## ☁️ Deployment Guide

### A. Local Windows 24/7 Execution
If you wish to keep the bot running on a home Windows PC or mini-PC:
- You can configure `run.bat` to run at system startup using Windows Task Scheduler.
- In Task Scheduler: Create Basic Task > Trigger: "When I log on" > Action: Start a program > `D:\Eniyan\My Websites\Thumbify\run.bat`.

### B. Free Hosting Reality Check
Many free hosting platforms (e.g. Free-tier Render, Railway Free, Vercel, Heroku free plans) are **unsuitable** for 200 MB–400 MB file transfers due to:
- Strict ephemeral disk limits (usually < 512 MB, which fills up immediately when downloading and uploading a 400 MB file).
- 30–60 second HTTP request timeouts (which terminate MTProto background sockets).
- Strict monthly egress bandwidth quotas (e.g. 5 GB/month = only ~12 transfers).
- Cold sleeps / hibernation when inactive.

### C. Recommended: Cloud VPS (e.g. Hetzner, DigitalOcean, Linode)
For reliable 24/7 operation without keeping your laptop on:
- A $4–$5/month Linux VPS (1 CPU, 1-2 GB RAM, 20-40 GB SSD, 1 TB+ transfer).

#### Systemd Service Setup (Ubuntu/Debian VPS)
1. Clone your repo onto the VPS:
   ```bash
   git clone <your-private-repo> /opt/thumbify
   cd /opt/thumbify
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt
   cp .env.example .env && nano .env
   ```
2. Create service file `/etc/systemd/system/thumbify.service`:
   ```ini
   [Unit]
   Description=Thumbify Telegram Auto Thumbnail Bot
   After=network.target

   [Service]
   Type=simple
   User=root
   WorkingDirectory=/opt/thumbify
   ExecStart=/opt/thumbify/.venv/bin/python -m app.main
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable thumbify
   sudo systemctl start thumbify
   sudo systemctl status thumbify
   ```

### D. Docker Deployment
Run anywhere with Docker & Docker Compose:
```bash
docker compose up -d --build
```
View logs:
```bash
docker compose logs -f
```

---

## 🛠 Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `[CONFIGURATION ERROR] Missing required configuration` | `.env` file is missing or has template placeholders | Copy `.env.example` to `.env` and fill in real credentials. |
| `[THUMBNAIL ERROR] Thumbnail file not found` | `assets/thumbnail.jpg` is missing | Place a JPEG image in `assets/thumbnail.jpg`. |
| `FloodWaitError: A wait of X seconds is required` | Telegram rate limits triggered | THUMBIFY automatically throttles progress updates to 3.5s. If triggered, wait the specified seconds. |
| Document thumbnail does not show on Android | Telegram client limitation | Video thumbnails are always displayed; some document types depend on Android Telegram's internal file preview handler. |
| `Telethon.errors.rpcerrorlist.ApiIdInvalidError` | Invalid `TG_API_ID` or `TG_API_HASH` | Double-check values at [my.telegram.org](https://my.telegram.org). |

---

## 🧪 Automated Test Suite

To run all automated tests:
```powershell
.\.venv\Scripts\pytest.exe -v
```
All 24 test cases validate configuration, thumbnail optimization, security, sanitization, concurrency, and cleanup.

