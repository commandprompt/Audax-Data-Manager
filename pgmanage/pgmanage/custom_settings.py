from pathlib import Path

# PgManage settings
PGMANAGE_VERSION = 'Dev'
PGMANAGE_SHORT_VERSION = 'dev'
DEV_MODE = True
DESKTOP_MODE = False
APP_TOKEN = None
PATH = ''
HOME_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path(__file__).resolve().parent.parent
MAX_UPLOAD_SIZE = 1024**2 * 30000
APP_DB_NAME = 'pgmanage'

# Django settings
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False