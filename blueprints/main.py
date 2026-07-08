from collections import OrderedDict

from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    request,
    send_from_directory,
)
from flask_login import current_user, login_required

from models import Movie
from utils import classify_external_url

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def library():
    search = request.args.get("q", "").strip()

    query = Movie.query
    if search:
        query = query.filter(Movie.title.ilike(f"%{search}%"))

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
    )


@bp.route("/film/<int:movie_id>")
@login_required
def player(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    embed = None
    if movie.source_type == "external" and movie.external_url:
        embed = classify_external_url(movie.external_url)

    return render_template("main/player.html", movie=movie, embed=embed)


@bp.route("/stream/<int:movie_id>")
@login_required
def stream(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if movie.source_type != "upload" or not movie.video_path:
        abort(404)

    # conditional=True obsługuje nagłówek Range, dzięki czemu przewijanie
    # (seek) w odtwarzaczu działa tak jak w Netflixie/YouTube
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER_VIDEOS"],
        movie.video_path,
        conditional=True,
    )
