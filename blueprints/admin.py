import os
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from extensions import db
from models import InviteCode, Movie
from utils import (
    generate_invite_code,
    is_allowed_image,
    is_allowed_video,
    safe_unique_filename,
)

bp = Blueprint("admin", __name__)


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


@bp.route("/")
@login_required
@admin_required
def dashboard():
    movies = Movie.query.order_by(Movie.created_at.desc()).all()
    return render_template("admin/dashboard.html", movies=movies)


def _save_poster(file_storage):
    if file_storage and file_storage.filename and is_allowed_image(file_storage.filename):
        filename = safe_unique_filename(file_storage.filename)
        file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER_POSTERS"], filename))
        return filename
    return None


def _save_video(file_storage):
    if file_storage and file_storage.filename and is_allowed_video(file_storage.filename):
        filename = safe_unique_filename(file_storage.filename)
        file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER_VIDEOS"], filename))
        return filename
    return None


def _delete_file_if_exists(folder, filename):
    if not filename:
        return
    path = os.path.join(folder, filename)
    if os.path.isfile(path):
        os.remove(path)


@bp.route("/filmy/nowy", methods=["GET", "POST"])
@login_required
@admin_required
def movie_new():
    if request.method == "POST":
        errors = _validate_movie_form(request.form, request.files, is_edit=False)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("admin/movie_form.html", movie=None, form=request.form)

        movie = Movie(added_by_id=current_user.id)
        _apply_movie_form(movie, request.form, request.files)
        db.session.add(movie)
        db.session.commit()

        flash(f'Dodano film "{movie.title}" do biblioteki.', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/movie_form.html", movie=None, form=None)


@bp.route("/filmy/<int:movie_id>/edytuj", methods=["GET", "POST"])
@login_required
@admin_required
def movie_edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == "POST":
        errors = _validate_movie_form(request.form, request.files, is_edit=True, movie=movie)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("admin/movie_form.html", movie=movie, form=request.form)

        _apply_movie_form(movie, request.form, request.files, is_edit=True)
        db.session.commit()

        flash(f'Zaktualizowano film "{movie.title}".', "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin/movie_form.html", movie=movie, form=None)


@bp.route("/filmy/<int:movie_id>/usun", methods=["POST"])
@login_required
@admin_required
def movie_delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    _delete_file_if_exists(current_app.config["UPLOAD_FOLDER_VIDEOS"], movie.video_path)
    _delete_file_if_exists(current_app.config["UPLOAD_FOLDER_POSTERS"], movie.poster_path)

    title = movie.title
    db.session.delete(movie)
    db.session.commit()

    flash(f'Usunięto film "{title}" z biblioteki.', "info")
    return redirect(url_for("admin.dashboard"))


def _validate_movie_form(form, files, is_edit, movie=None):
    errors = []

    if not form.get("title", "").strip():
        errors.append("Podaj tytuł filmu.")

    source_type = form.get("source_type")
    if source_type not in ("upload", "external"):
        errors.append("Wybierz źródło wideo: plik wgrywany lub link zewnętrzny.")

    if source_type == "external" and not form.get("external_url", "").strip():
        errors.append("Podaj link do materiału wideo.")

    if source_type == "upload":
        video_file = files.get("video_file")
        has_new_file = video_file and video_file.filename
        has_existing_file = is_edit and movie and movie.video_path
        if not has_new_file and not has_existing_file:
            errors.append("Wgraj plik wideo.")
        if has_new_file and not is_allowed_video(video_file.filename):
            errors.append("Niedozwolony format pliku wideo.")

    poster_file = files.get("poster_file")
    if poster_file and poster_file.filename and not is_allowed_image(poster_file.filename):
        errors.append("Niedozwolony format pliku plakatu.")

    release_year = form.get("release_year", "").strip()
    if release_year and not release_year.isdigit():
        errors.append("Rok premiery musi być liczbą.")

    return errors


def _apply_movie_form(movie, form, files, is_edit=False):
    movie.title = form.get("title", "").strip()
    movie.description = form.get("description", "").strip() or None
    movie.genre = form.get("genre", "").strip() or None
    movie.duration_label = form.get("duration_label", "").strip() or None

    release_year = form.get("release_year", "").strip()
    movie.release_year = int(release_year) if release_year.isdigit() else None

    source_type = form.get("source_type")
    movie.source_type = source_type

    if source_type == "external":
        movie.external_url = form.get("external_url", "").strip()
        if movie.video_path:
            _delete_file_if_exists(current_app.config["UPLOAD_FOLDER_VIDEOS"], movie.video_path)
            movie.video_path = None
    else:
        movie.external_url = None
        video_file = files.get("video_file")
        if video_file and video_file.filename:
            if is_edit and movie.video_path:
                _delete_file_if_exists(current_app.config["UPLOAD_FOLDER_VIDEOS"], movie.video_path)
            movie.video_path = _save_video(video_file)

    poster_file = files.get("poster_file")
    poster_url = form.get("poster_url", "").strip()
    if poster_file and poster_file.filename:
        if is_edit and movie.poster_path:
            _delete_file_if_exists(current_app.config["UPLOAD_FOLDER_POSTERS"], movie.poster_path)
        movie.poster_path = _save_poster(poster_file)
        movie.poster_url = None
    elif poster_url:
        movie.poster_url = poster_url
        if is_edit and movie.poster_path:
            _delete_file_if_exists(current_app.config["UPLOAD_FOLDER_POSTERS"], movie.poster_path)
        movie.poster_path = None


@bp.route("/kody", methods=["GET", "POST"])
@login_required
@admin_required
def invite_codes():
    if request.method == "POST":
        grants_admin = bool(request.form.get("grants_admin"))
        new_code = InviteCode(
            code=generate_invite_code(),
            grants_admin=grants_admin,
            created_by_id=current_user.id,
        )
        db.session.add(new_code)
        db.session.commit()
        flash(f"Wygenerowano nowy kod: {new_code.code}", "success")
        return redirect(url_for("admin.invite_codes"))

    codes = InviteCode.query.order_by(InviteCode.created_at.desc()).all()
    return render_template("admin/codes.html", codes=codes)


@bp.route("/kody/<int:code_id>/usun", methods=["POST"])
@login_required
@admin_required
def invite_code_delete(code_id):
    code = InviteCode.query.get_or_404(code_id)
    if code.is_used:
        flash("Nie można usunąć kodu, który został już wykorzystany.", "error")
    else:
        db.session.delete(code)
        db.session.commit()
        flash("Usunięto nieużywany kod zaproszenia.", "info")
    return redirect(url_for("admin.invite_codes"))
