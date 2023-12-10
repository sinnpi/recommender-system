import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Ratings
from datetime import datetime
from tqdm import tqdm

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
                total = sum(1 for row in csv.reader(csvfile)) - 1
            csvfile.close()

            next(reader, None)  # skip the header row
            for i, row in enumerate(tqdm(reader, total=total)):
                    try:
                        id = row[0]
                        title = row[1]
                        movie = Movie(id=id, title=title)
                        db.session.add(movie)
                        genres = row[2].split('|')  # genres is a list of genres
                        for genre in genres:  # add each genre to the movie_genre table
                            movie_genre = MovieGenre(movie_id=id, genre=genre)
                            db.session.add(movie_genre)
                        db.session.commit()  # save data to database
                    except IntegrityError:
                        print("Ignoring duplicate movie: " + title)
                        db.session.rollback()
                        pass

    if Ratings.query.count() == 0:
        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
                total = sum(1 for row in csv.reader(csvfile)) - 1  # count rows in the file
            csvfile.close()

            next(reader, None) # skip the header row
            for i, row in enumerate(tqdm(reader, total=total)):
                try:
                    timestamp = datetime.fromtimestamp(int(row[3]))
                    rating = Ratings(movie_id=row[1], user_id=row[0], rating=row[2], timestamp=timestamp)
                    db.session.add(rating)
                    if i % 1000 == 0: # batch size, faster
                        db.session.commit()
                except IntegrityError:
                    print("Ignoring duplicate rating: " + row[0] + " " + row[1])
                    db.session.rollback()
                    pass

