from collections import OrderedDict
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

    # "movie" (pojedynczy film) | "series" (serial z sezonami/odcinkami)
    media_type = db.Column(db.String(20), nullable=False, default="movie")

    poster_path = db.Column(db.String(500), nullable=True)  # plik wgrany lokalnie
    poster_url = db.Column(db.String(500), nullable=True)  # zewnętrzny URL plakatu

    # Pola poniżej dotyczą wyłącznie filmów (media_type == "movie").
    # Dla seriali wideo trzyma się na poziomie odcinków (patrz: Episode).
    source_type = db.Column(db.String(20), nullable=True)  # "upload" | "external"
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

    episodes = db.relationship(
        "Episode",
        back_populates="series",
        cascade="all, delete-orphan",
        order_by="[Episode.season_number, Episode.episode_number]",
    )

    def poster_src(self) -> str:
        """Zwraca URL plakatu do wyświetlenia w szablonie."""
        if self.poster_path:
            return f"/zflix/static/uploads/posters/{self.poster_path}"
        if self.poster_url:
            return self.poster_url
        return "/zflix/static/img/placeholder-poster.svg"

    def is_series(self) -> bool:
        return self.media_type == "series"

    def seasons(self):
        """Grupuje odcinki serialu wg numeru sezonu, w kolejności rosnącej."""
        grouped = OrderedDict()
        for episode in self.episodes:
            grouped.setdefault(episode.season_number, []).append(episode)
        return grouped

    def episode_count(self) -> int:
        return len(self.episodes)

    def __repr__(self):
        kind = "Series" if self.is_series() else "Movie"
        return f"<{kind} {self.title}>"


class Episode(db.Model):
    __tablename__ = "episodes"
    __table_args__ = (
        db.UniqueConstraint(
            "series_id", "season_number", "episode_number", name="uq_episode_position"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey("movies.id"), nullable=False)

    season_number = db.Column(db.Integer, nullable=False, default=1)
    episode_number = db.Column(db.Integer, nullable=False, default=1)

    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    duration_label = db.Column(db.String(20), nullable=True)

    source_type = db.Column(db.String(20), nullable=False)  # "upload" | "external"
    video_path = db.Column(db.String(500), nullable=True)
    external_url = db.Column(db.String(500), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    series = db.relationship("Movie", back_populates="episodes")

    def display_title(self) -> str:
        base = f"Odcinek {self.episode_number}"
        return f"{base}: {self.title}" if self.title else base

    def __repr__(self):
        return f"<Episode S{self.season_number}E{self.episode_number} of series_id={self.series_id}>"
