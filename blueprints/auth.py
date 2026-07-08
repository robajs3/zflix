from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from models import InviteCode, User

bp = Blueprint("auth", __name__)


@bp.route("/rejestracja", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.library"))

    if request.method == "POST":
        invite_code_raw = request.form.get("invite_code", "").strip().upper()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        errors = []

        invite = InviteCode.query.filter_by(code=invite_code_raw).first()
        if not invite:
            errors.append("Nieprawidłowy kod zaproszenia.")
        elif invite.is_used:
            errors.append("Ten kod zaproszenia został już wykorzystany.")

        if not username or len(username) < 3:
            errors.append("Nazwa użytkownika musi mieć co najmniej 3 znaki.")
        elif User.query.filter_by(username=username).first():
            errors.append("Ta nazwa użytkownika jest już zajęta.")

        if not email or "@" not in email:
            errors.append("Podaj prawidłowy adres e-mail.")
        elif User.query.filter_by(email=email).first():
            errors.append("Ten adres e-mail jest już zarejestrowany.")

        if len(password) < 8:
            errors.append("Hasło musi mieć co najmniej 8 znaków.")
        elif password != password_confirm:
            errors.append("Hasła nie są identyczne.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "auth/register.html",
                username=username,
                email=email,
            )

        user = User(username=username, email=email, is_admin=invite.grants_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # żeby user.id był dostępny

        invite.is_used = True
        invite.used_by_id = user.id
        invite.used_at = datetime.utcnow()

        db.session.commit()

        login_user(user)
        flash(f"Witaj w Zjebflixie, {user.username}!", "success")
        return redirect(url_for("main.library"))

    return render_template("auth/register.html")


@bp.route("/logowanie", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.library"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (db.func.lower(User.username) == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Zalogowano jako {user.username}.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or url_for("main.library"))

        flash("Nieprawidłowa nazwa użytkownika/e-mail lub hasło.", "error")

    return render_template("auth/login.html")


@bp.route("/wyloguj")
@login_required
def logout():
    logout_user()
    flash("Wylogowano. Do zobaczenia!", "info")
    return redirect(url_for("auth.login"))
