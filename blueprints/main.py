from collections import OrderedDict

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import current_user, login_required

from models import Episode, Movie
from utils import classify_external_url

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def library():
    search = request.args.get("q", "").strip()
    media_type = request.args.get("typ", "").strip()  # "" | "movie" | "series"

    query = Movie.query
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))
    if media_type in ("movie", "series"):
        query = query.filter(Movie.media_type == media_type)

    movies = query.order_by(Movie.created_at.desc()).all()

    featured = movies[0] if movies and not search else None

    rows = OrderedDict()
    for movie in movies:
        genre = movie.genre or "Bez kategorii"
        rows.setdefault(genre, []).append(movie)

    return render_template(
        "main/library.html",
        movies=movies,
        rows=rows,
        featured=featured,
        search=search,
        media_type=media_type,
    )


@bp.route("/film/<int:movie_id>")
@login_required
def player(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if movie.is_series():
        abort(404)

    embed = None
    if movie.source_type == "external" and movie.external_url:
        embed = classify_external_url(movie.external_url)

    return render_template(
        "main/player.html",
        title=movie.title,
        meta_year=movie.release_year,
        meta_genre=movie.genre,
        meta_duration=movie.duration_label,
        description=movie.description,
        source_type=movie.source_type,
        stream_url=url_for("main.stream", movie_id=movie.id),
        embed=embed,
        back_url=url_for("main.library"),
        back_label="Biblioteka",
    )


@bp.route("/stream/<int:movie_id>")
@login_required
def stream(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if movie.is_series() or movie.source_type != "upload" or not movie.video_path:
        abort(404)

    # conditional=True obsługuje nagłówek Range, dzięki czemu przewijanie
    # (seek) w odtwarzaczu działa tak jak w Netflixie/YouTube
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER_VIDEOS"],
        movie.video_path,
        conditional=True,
    )


@bp.route("/serial/<int:series_id>")
@login_required
def series_detail(series_id):
    series = Movie.query.get_or_404(series_id)
    if not series.is_series():
        abort(404)

    seasons = series.seasons()
    season_param = request.args.get("sezon", type=int)
    if season_param not in seasons:
        season_param = next(iter(seasons), None)

    return render_template(
        "main/series.html",
        series=series,
        seasons=seasons,
        active_season=season_param,
    )


@bp.route("/serial/<int:series_id>/odcinek/<int:episode_id>")
@login_required
def episode_player(series_id, episode_id):
    series = Movie.query.get_or_404(series_id)
    episode = Episode.query.get_or_404(episode_id)
    if not series.is_series() or episode.series_id != series.id:
        abort(404)

    embed = None
    if episode.source_type == "external" and episode.external_url:
        embed = classify_external_url(episode.external_url)

    meta_bits = [f"Sezon {episode.season_number}", f"Odcinek {episode.episode_number}"]

    return render_template(
        "main/player.html",
        title=f"{series.title} — {episode.display_title()}",
        meta_year=None,
        meta_genre=" · ".join(meta_bits),
        meta_duration=episode.duration_label,
        description=episode.description or series.description,
        source_type=episode.source_type,
        stream_url=url_for("main.episode_stream", episode_id=episode.id),
        embed=embed,
        back_url=url_for("main.series_detail", series_id=series.id, sezon=episode.season_number),
        back_label=series.title,
    )


@bp.route("/stream-odcinek/<int:episode_id>")
@login_required
def episode_stream(episode_id):
    episode = Episode.query.get_or_404(episode_id)

    if episode.source_type != "upload" or not episode.video_path:
        abort(404)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER_VIDEOS"],
        episode.video_path,
        conditional=True,
    )
