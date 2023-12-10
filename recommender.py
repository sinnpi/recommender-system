# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template
from flask_user import login_required, UserManager

from models import db, User, Movie, MovieGenre
from read_data import check_and_read_data

from datetime import datetime

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

    # Flask-SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///movie_recommender.sqlite'  # File-based SQL database
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Avoids SQLAlchemy warning

    # Flask-User settings
    USER_APP_NAME = "Movie Recommender"  # Shown in and email templates and page footers
    USER_ENABLE_EMAIL = False  # Disable email authentication
    USER_ENABLE_USERNAME = True  # Enable username authentication
    USER_REQUIRE_RETYPE_PASSWORD = True  # Simplify register form

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management


def create_test_user():
    from werkzeug.security import generate_password_hash

    # Test123
    hashed_password = '$2b$12$2PbFYnIt5NSfYIaVxSrxmOiDGbpvgc.RBNHhEs5QPCRYzn/bHTrfe'
    test_user = User(username='testuser', password=hashed_password)

    db.session.add(test_user)
    db.session.commit()
    print(f'Created test user with username: {test_user.username} and password: Test123')


@app.cli.command('initdb')
def initdb_command():
    global db
    """Creates the database tables."""
    check_and_read_data(db)
    print('Initialized the database.')
    
    create_test_user()


# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")


# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    # String-based templates

    # show list of genres
    genres = MovieGenre.query.distinct(MovieGenre.genre).all()

    # first 10 movies
    movies = Movie.query.limit(10).all()

    # only Romance movies
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre == 'Romance')).limit(10).all()

    # only Romance AND Horror movies
    # movies = Movie.query\
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Romance')) \
    #     .filter(Movie.genres.any(MovieGenre.genre == 'Horror')) \
    #     .limit(10).all()

    return render_template("movies.html", movies=movies)


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
