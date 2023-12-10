from flask_sqlalchemy import SQLAlchemy
from flask_user import UserMixin

db = SQLAlchemy()

MAX_URL_LENGTH = 255

# Define the User data-model.
# NB: Make sure to add flask_user UserMixin as this adds additional fields and properties required by Flask-User
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

    # User authentication information. The collation='NOCASE' is required
    # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
    username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    email_confirmed_at = db.Column(db.DateTime())

    # User information
    first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
    last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')


class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
    genres = db.relationship('MovieGenre', backref='movie', lazy=True)


class MovieGenre(db.Model):
    __tablename__ = 'movie_genres'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    genre = db.Column(db.String(255), nullable=False, server_default='')

class Ratings(db.Model):
    __tablename__ = 'movie_ratings'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class TagNames(db.Model):
    __tablename__ = 'movie_tagnames'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Tags(db.Model):
    __tablename__ = 'movie_tags'
    id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('movie_tagnames.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

class Links(db.Model):
    __tablename__ = 'movie_links'
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    ml_link = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    imdb_link = db.Column(db.String(MAX_URL_LENGTH), nullable=False)
    tmdb_link = db.Column(db.String(MAX_URL_LENGTH), nullable=False)