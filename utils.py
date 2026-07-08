import re
import secrets
import string
from urllib.parse import urlparse, parse_qs

from flask import current_app


def generate_invite_code() -> str:
    """Generuje czytelny, losowy kod zaproszenia w formacie XXXX-XXXX-XXXX."""
    alphabet = string.ascii_uppercase + string.digits
    # usuwamy znaki, które łatwo pomylić (0/O, 1/I)
    alphabet = alphabet.translate(str.maketrans("", "", "0O1I"))
    groups = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return "-".join(groups)


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def is_allowed_video(filename: str) -> bool:
    return allowed_file(filename, current_app.config["ALLOWED_VIDEO_EXTENSIONS"])


def is_allowed_image(filename: str) -> bool:
    return allowed_file(filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"])


def safe_unique_filename(filename: str) -> str:
    """Tworzy bezpieczną, unikalną nazwę pliku zachowując rozszerzenie."""
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    token = secrets.token_hex(12)
    return f"{token}.{ext}" if ext else token


_YOUTUBE_HOSTS = {"www.youtube.com", "youtube.com", "m.youtube.com", "youtu.be"}
_VIMEO_HOSTS = {"vimeo.com", "www.vimeo.com"}


def classify_external_url(url: str) -> dict:
    """
    Analizuje zewnętrzny link i zwraca informacje potrzebne odtwarzaczowi:
    - kind: "youtube" | "vimeo" | "direct"
    - embed_url: adres do osadzenia w <iframe> (dla youtube/vimeo)
    Dla linków bezpośrednich (np. .mp4) odtwarzacz użyje zwykłego <video>.
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in _YOUTUBE_HOSTS:
        video_id = None
        if host == "youtu.be":
            video_id = parsed.path.lstrip("/")
        else:
            qs = parse_qs(parsed.query)
            if "v" in qs:
                video_id = qs["v"][0]
            else:
                match = re.search(r"/embed/([^/?]+)", parsed.path)
                if match:
                    video_id = match.group(1)
        if video_id:
            return {
                "kind": "youtube",
                "embed_url": f"https://www.youtube.com/embed/{video_id}?rel=0&autoplay=1",
            }

    if host in _VIMEO_HOSTS:
        match = re.search(r"/(\d+)", parsed.path)
        if match:
            return {
                "kind": "vimeo",
                "embed_url": f"https://player.vimeo.com/video/{match.group(1)}?autoplay=1",
            }

    # domyślnie zakładamy bezpośredni link do pliku wideo
    return {"kind": "direct", "embed_url": url}
