# Contains parts from: https://flask-user.readthedocs.io/en/latest/quickstart_app.html

from flask import Flask, render_template, request, g, url_for, redirect, jsonify
from flask_user import login_required, UserManager, current_user
from sqlalchemy.orm import joinedload


from models import db, User, Movie, MovieGenre, Link, Tags, TagNames, Ratings
from read_data import check_and_read_data

from datetime import datetime
import time

import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists('logs'):
    os.mkdir('logs')

# logging
logger = logging.getLogger('api_flask')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('logs/api_flask.log', maxBytes=10*1024*1024, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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
app.debug = True  # only for development
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db
db.init_app(app)  # initialize database
db.create_all()  # create database if necessary
user_manager = UserManager(app, db, User)  # initialize Flask-User management


# global variables
MOVIES_PER_PAGE = 5
RATING_RANGE = (0, 5)

def create_test_user():
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

@app.cli.command('modelbased')
def modelbased_command():
    import model_based
    model_based.test(db)

@app.before_request
def start_timer():
    g.start = time.time()

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    # render home.html template
    return render_template("home.html")

# The Members page is only accessible to authenticated users via the @login_required decorator
@app.route('/movies')
@login_required  # User must be authenticated
def movies_page():
    page = request.args.get('page', 1, type=int)
    # String-based templates
    pagination = Movie.query.paginate(page=page, per_page=MOVIES_PER_PAGE, count=False, error_out=False)
    movies = pagination.items
    pagination.has_next
    # print(f'movies count: {len(movies)}')
    # print(f'pagination: {pagination}')

    return render_template("movies.html", movies=movies, pagination=pagination)

# @app.route('/movies/genres/<genres>')
@app.route('/movies/genres')
@login_required  # User must be authenticated
def movies_by_genres():

    logger.info(f'genres: {request.args.get("genres", None)}')

    # get genres page number from query parameters
    genres_param = request.args.get('genres', None)
    page = request.args.get('page', 1, type=int)

    # split the genres parameter into a list of genres
    genres = genres_param.split(',') if genres_param else []
    genres = list(set(genres)) # remove duplicates
    genres.sort() # sort alphabetically
    if not genres:
        logger.info(f'genres: {genres}')
        return redirect(url_for('movies_page', page=page ))

    # get all movies of the selected genres, paginated
    # movies = Movie.query.filter(Movie.genres.any(MovieGenre.genre.in_(genres))).limit(10).all()

    query = Movie.query.filter(Movie.genres.any(MovieGenre.genre.in_(genres)))
    pagination = query.paginate(page=page, per_page=MOVIES_PER_PAGE, count=False, error_out=False)
    movies = pagination.items
    
    return render_template("movies.html", movies=movies, genres=genres, pagination=pagination)

# @app.route('/movies/int:<movie_id>')
# @login_required  # User must be authenticated
# def movie_page(movie_id):
#     movie = Movie.query.get(movie_id)
#     return render_template("movie_info.html", movie=movie)

@app.route('/rate_movie', methods=['POST'])
@login_required  # User must be authenticated
def rate_movie():
    logger.info(f'rate_movie')

    data = request.get_json()
    movie_id = data['movie_id']
    rating = data['rating']
    user_id = current_user.id
    timestamp = datetime.now()

    logger.info(f'movie_id: {movie_id}, rating: {rating}, user_id: {user_id}, timestamp: {timestamp}')

    # check if rating value is valid
    # check if rating is a number
    try:
        rating = float(rating)
    except ValueError:
        return jsonify({'success': False, 'message': f'Invalid rating value type, expected float, got {type(rating)}'})
    # check if rating is in the correct range
    if rating < RATING_RANGE[0] or rating > RATING_RANGE[1]:
        return jsonify({'success': False, 'message': f'Invalid rating value, expected value between {RATING_RANGE[0]} and {RATING_RANGE[1]}, got {rating}'})
    
    # check if rating already exists
    rating_obj = Ratings.query.filter_by(movie_id=movie_id, user_id=user_id).first()
    if rating_obj:
        logger.info(f'rating already exists: {rating_obj.rating}')
        # overwrite rating
        rating_obj.rating = rating
        rating_obj.timestamp = timestamp
        db.session.commit()
        logger.info(f'rating updated: {rating_obj.rating}')
    else:
        logger.info(f'creating new rating')
        rating_obj = Ratings(movie_id=movie_id, user_id=user_id, rating=rating, timestamp=timestamp)
        db.session.add(rating_obj)
        db.session.commit()
        logger.info(f'rating created: {rating_obj.rating}')

    return jsonify({'success': True})


# Start development web server
if __name__ == '__main__':
    app.run(port=5000, debug=True)
