from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movies_added = db.relationship(
        "Movie", back_populates="added_by", foreign_keys="Movie.added_by_id"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.username}>"


class InviteCode(db.Model):
    __tablename__ = "invite_codes"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    grants_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_used = db.Column(db.Boolean, nullable=False, default=False)

    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    used_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, unique=True
    )

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    used_at = db.Column(db.DateTime, nullable=True)

    created_by = db.relationship("User", foreign_keys=[created_by_id])
    used_by = db.relationship("User", foreign_keys=[used_by_id])

    def __repr__(self):
        return f"<InviteCode {self.code} used={self.is_used}>"


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    release_year = db.Column(db.Integer, nullable=True)
    duration_label = db.Column(db.String(20), nullable=True)  # np. "1g 42min"

    poster_path = db.Column(db.String(500), nullable=True)  # plik wgrany lokalnie
    poster_url = db.Column(db.String(500), nullable=True)  # zewnętrzny URL plakatu

    source_type = db.Column(db.String(20), nullable=False)  # "upload" | "external"
    video_path = db.Column(db.String(500), nullable=True)  # plik wgrany lokalnie
    external_url = db.Column(db.String(500), nullable=True)  # link zewnętrzny

    added_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    added_by = db.relationship(
        "User", back_populates="movies_added", foreign_keys=[added_by_id]
    )

    def poster_src(self) -> str:
        """Zwraca URL plakatu do wyświetlenia w szablonie."""
        if self.poster_path:
            return f"/zjebflix/static/uploads/posters/{self.poster_path}"
        if self.poster_url:
            return self.poster_url
        return "/zjebflix/static/img/placeholder-poster.svg"

    def __repr__(self):
        return f"<Movie {self.title}>"
