"""Application constants and remote endpoints."""

from __future__ import annotations

APP_NAME = "Binglish"
VERSION = "2.0.0"
PROJECT_URL = "https://github.com/klemperer/binglish"

# Dual-track distribution:
# - CDN (ss.blueforge.org): fast auto-update path used by tray "检查更新"
# - GitHub Releases: authoritative build; users may download/verify manually
GITHUB_REPO = "klemperer/binglish"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"
GITHUB_LATEST_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Remote service (legacy host; all learning assets live here today)
SERVICE_BASE = "https://ss.blueforge.org"
IMAGE_URL = f"{SERVICE_BASE}/bing?v={VERSION}"
RELEASE_JSON_URL = f"{SERVICE_BASE}/bing/release.json"
DOWNLOAD_URL = f"{SERVICE_BASE}/bing/binglish.exe"
MUSIC_JSON_URL = f"{SERVICE_BASE}/bing/songoftheday.json"
REMOTE_REMIND_URL = f"{SERVICE_BASE}/remind.json"
USELESS_FACT_URL = f"{SERVICE_BASE}/bing/uselessfact.json"
HISTORY_URL_BASE = f"{SERVICE_BASE}/getHistory"
GAME_DATA_URL = f"{SERVICE_BASE}/bing/games.json"
WORDLE_VALIDATE_URL = f"{SERVICE_BASE}/valid"
CROSSWORD_URL = f"{SERVICE_BASE}/dailyCrossword"
VOCAB_TEST_URL = f"{SERVICE_BASE}/getVocabTest"
SHARE_URL_TEMPLATE = f"{SERVICE_BASE}/bing/s/{{image_id}}.htm"
BING_HOME = "https://www.bing.com"
PLAYPHRASE_URL = (
    "https://www.playphrase.me/#/reels/en?source=custom-search"
    "&q={word}&translate-direction=zh-cn&ct=phrases"
)

UPDATE_INTERVAL_SECONDS = 3 * 60 * 60
DOWNLOAD_RETRY_INTERVAL_SECONDS = 30
INTERNET_CHECK_INTERVAL_SECONDS = 60

ICON_FILENAME = "binglish.ico"
WALLPAPER_FILENAME = "wallpaper.jpg"
CONFIG_FILENAME = "binglish.ini"
DEBUG_LOG_FILENAME = "binglish_debug.log"

REST_INTERVAL_DEFAULT = 2700
IDLE_RESET_DEFAULT = 300
REST_LOCK_DEFAULT = 30
OVERLAY_COLOR_DEFAULT = "#2C3E50"

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

# Palette used by overlays / games (shared visual language)
COLOR_BG = "#2C3E50"
COLOR_GOLD = "#F1C40F"
COLOR_MUTED = "#BDC3C7"
COLOR_DIM = "#7F8C8D"
COLOR_GREEN = "#2ECC71"
COLOR_RED = "#E74C3C"
COLOR_ORANGE = "#E67E22"
COLOR_BLUE = "#3498DB"
COLOR_PURPLE = "#9B59B6"
COLOR_LIGHT = "#ECF0F1"
