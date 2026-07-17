import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-zmien-mnie")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://zflix_user:zflix_pass@localhost:5432/zflix",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Prefiks, pod którym działa cała aplikacja
    URL_PREFIX = "/zflix"

    # Izolacja ciasteczka sesji, żeby nie gryzło się z innymi appkami
    # działającymi na tym samym hoście/domenie (np. pod Tailscale Funnel).
    # Bez tego wszystkie apki Flask na tej domenie dzielą ciasteczko "session"
    # i nadpisują sobie nawzajem logowanie.
    SESSION_COOKIE_NAME = "zflix_session"
    SESSION_COOKIE_PATH = URL_PREFIX
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "1") == "1"

    # Katalogi na pliki wgrywane przez admina
    UPLOAD_FOLDER_VIDEOS = str(BASE_DIR / "static" / "uploads" / "videos")
    UPLOAD_FOLDER_POSTERS = str(BASE_DIR / "static" / "uploads" / "posters")

    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "ogg", "mov", "mkv", "avi"}

    # Formaty, które trzeba przekonwertować do MP4, bo przeglądarki
    # nie odtwarzają ich natywnie przez <video>.
    VIDEO_EXTENSIONS_REQUIRING_TRANSCODE = {"avi"}
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 2048))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024

    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
