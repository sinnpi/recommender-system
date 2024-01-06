import numpy as np


from sqlalchemy.exc import IntegrityError
from models import Movie, Ratings, User

import tensorflow as tf


def test(db):
    print(f"User count {User.query.count()}")
    print(f"Movie count {Movie.query.count()}")
    print(f"Ratings count {Ratings.query.count()}")

    # mapping from movie_id to index
    movie_to_index = {}
    for i, movie in enumerate(Movie.query.all()):
        movie_to_index[movie.id] = i

    R = np.zeros((User.query.count(), Movie.query.count()))
    counter = 0

    for rating in Ratings.query.all():
        #R[rating.user_id - 1, rating.movie_id - 1] = rating.rating
        try:
            R[rating.user_id - 1, movie_to_index[rating.movie_id]] = rating.rating
            counter += 1
        except KeyError as e:
            print(f"KeyError: Movie {rating.movie_id} does not exist")
            print(f"Exception: {e}")
        except IndexError as e:
            print(f"IndexError: User {rating.user_id} or Movie {rating.movie_id} does not exist")
            print(f"Exception: {e}")

    print(f"{counter} added")

    # print first 10 rows and columns
    print(R.shape)
    print(R[:10, :10])

    # print how many ratings are 0 and how many are not
    print(f"Number of ratings: {np.count_nonzero(R)}")
    print(f"Number of missing ratings: {np.count_nonzero(R == 0)}")

    # how many percent are filled
    print(f"Percent filled: {np.count_nonzero(R) / R.size * 100}%")

