import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Ratings, TagNames, Tags, Link, User
from datetime import datetime
from tqdm import tqdm
import re

import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists('logs'):
    os.mkdir('logs')

# logging
logger = logging.getLogger('read_data')
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('logs/read_data.log', maxBytes=10*1024*1024, backupCount=3)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# TODO
# - when an error occurs when commiting a batch,
commit_batch_size = 1000 # commit every 1000 rows for faster performance
commit_batch_size_movies = 100 # commit from the movies files every x rows ( lower number for better duplicate handling )

def count_rows(filename, encoding='utf8'):
    return sum(1 for row in csv.reader(open(filename, newline='', encoding=encoding))) - 1

# TODO , fix the individual commit when error accurs in a better way
# - add title without the year
def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    unique_users = set()

    if Movie.query.count() == 0:
        # read movies from csv
        total = count_rows('data/movies.csv')
        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            rowcount = Counter(name='Movies added')
            dupecount = Counter(name='Duplicate movies')
            movie_with_no_year = Counter(name='Movies with no year')
            reader = csv.reader(csvfile, delimiter=',')
            next(reader, None)  # skip the header row
            batch = []
            for i, row in enumerate(tqdm(reader, total=total), start=1):
                batch.append(row)
                try:
                    rowcount.increment()
                    add_movie_and_genre(db, row, movie_with_no_year_counter=movie_with_no_year)
                    if i % commit_batch_size_movies == 0:  # batch size, faster
                        db.session.commit()  # save data to database
                        batch = []
                except IntegrityError as err:
                    logger.debug('error: ', err)
                    # print(f"Ignoring duplicate movie id: {id} , title: {original_title}")
                    db.session.rollback()
                    commit_problematic_batch(db, batch,movie_with_no_year_counter=movie_with_no_year,
                                            rowcount=rowcount, dupecount=dupecount)
                    batch = []
                    pass
            try:
                db.session.commit()
            except IntegrityError as err:
                logger.debug('error: ', err)
                db.session.rollback()
                commit_problematic_batch(db, batch, movie_with_no_year_counter=movie_with_no_year,
                                        rowcount=rowcount, dupecount=dupecount)
                batch = []
                pass

            logger.info('Movies:')
            logger.info(f"{total} rows read. Added {rowcount} movies to the database. Ignored {dupecount} duplicates. {movie_with_no_year} movies with no year.")

    if Ratings.query.count() == 0:
        total = count_rows('data/ratings.csv')

        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            rowcount = 0
            dupecount = 0

            reader = csv.reader(csvfile, delimiter=',')
            next(reader, None) # skip the header row
            for i, row in enumerate(tqdm(reader, total=total)):
                try:
                    user_id = row[0]
                    timestamp = datetime.fromtimestamp(int(row[3]))
                    rating = Ratings(movie_id=row[1], user_id=user_id, rating=row[2], timestamp=timestamp)
                    db.session.add(rating)

                    # add the user to the database if it doesn't exist
                    if user_id not in unique_users:
                        add_user(db, user_id)
                        unique_users.add(user_id)

                    if i % commit_batch_size == 0: # batch size, faster
                        db.session.commit()
                    rowcount += 1
                except IntegrityError:
                    dupecount += 1
                    db.session.rollback()
                    pass
            try:
                db.session.commit()
            except IntegrityError:
                dupecount += 1
                db.session.rollback()
                pass

            logger.info('Ratings:')
            logger.info(f"{total} rows read. Added {rowcount} ratings to the database. Ignored {dupecount} duplicates.")


    if Tags.query.count() == 0:
        total = count_rows('data/tags.csv')

        with open('data/tags.csv', newline='', encoding='utf8') as csvfile:
            rowcount = 0
            dupecount = 0
            unique_tag_count = 0

            reader = csv.reader(csvfile, delimiter=',')
            next(reader, None)  # skip the header row
            for i, row in enumerate(tqdm(reader, total=total)):
                try:
                    user_id = row[0]
                    movie_id = row[1]
                    tag_name = row[2]
                    timestamp = datetime.fromtimestamp(int(row[3]))

                    # check if the tag name already exists
                    tagname = TagNames.query.filter_by(name=tag_name).first()

                    if tagname is None:
                        # if the tag name doesn't exist, create a new Tagname
                        tagname = TagNames(name=tag_name)
                        db.session.add(tagname)
                        db.session.commit()  # commit immediately to get the new Tagname's ID
                        unique_tag_count += 1

                    # create a new Tag with the Tagname's ID
                    tag = Tags(user_id=user_id, movie_id=movie_id, tag_name_id=tagname.id, timestamp=timestamp)
                    db.session.add(tag)

                    # add the user to the database if it doesn't exist
                    if user_id not in unique_users:
                        add_user(db, user_id)
                        unique_users.add(user_id)

                    if i % commit_batch_size == 0:  # batch size, faster
                        db.session.commit()
                    rowcount += 1
                except IntegrityError:
                    dupecount += 1
                    db.session.rollback()
                    pass
            try:
                db.session.commit()
            except IntegrityError:
                dupecount += 1
                db.session.rollback()
                pass

            logger.info('Tags:')
            logger.info(f"{total} rows read. Added {rowcount} tags to the database. Ignored {dupecount} duplicates. {unique_tag_count} unique tags added.")


	
    if Link.query.count() == 0:
        total = count_rows('data/links.csv')

        with open('data/links.csv', newline='', encoding='utf8') as csvfile:
            rowcount = 0
            dupecount = 0

            reader = csv.reader(csvfile, delimiter=',')
            next(reader, None)
            for i, row in enumerate(tqdm(reader, total=total)):
                try:
                    movie_id = row[0]
                    ml_id = row[0]
                    imdb_id = row[1]
                    tmdb_id = row[2]

                    ml_url = f"https://movielens.org/movies/{ml_id}"
                    imdb_url = f"https://www.imdb.com/title/tt{imdb_id}"
                    tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}"

                    link = Link(movie_id=movie_id, ml_url=ml_url, imdb_url=imdb_url, tmdb_url=tmdb_url
                                 )
                    db.session.add(link)
                    if i % commit_batch_size == 0:  # batch size, faster
                        db.session.commit()
                    rowcount += 1
                except IntegrityError:
                    logger.debug(f"Ignoring movie id: {movie_id}")
                    dupecount += 1
                    db.session.rollback()
                    pass
            try:
                db.session.commit()
            except IntegrityError:
                logger.debug(f"Ignoring movie id: {movie_id}")
                dupecount += 1
                db.session.rollback()
                pass

            logger.info('Links:')
            logger.info(f"{total} rows read. Added {rowcount} Links to the database. Ignored {dupecount} duplicates.")

        logger.info('Users:')
        logger.info(f"added {len(unique_users)} users to the database.")


def add_user(db, user_id):
    # logger.info(f"creating new user: {user_id}")
    username = f'user_{user_id}'
    # passwrod: User123
    password = '$2b$12$Yx/CbwsNtJaW38hrY5Nvfe/nUHkZPdfSOPY.cAuPtrn2Ogw5zp/vq' # hashed password with the user_manager

    user = User(id=user_id, username=username, password=password)
    db.session.add(user)
    

def commit_problematic_batch(db, batch, rowcount, dupecount, **kwargs):
    # commit a batch of data that had an error,commit each row/entry individually
    # this is slower but allows us to identify the problematic row and keeps the counters accurate
    print(f'committing {len(batch)} rows individually')
    for row in batch:
        try:
            add_movie_and_genre(db, row, **kwargs)
            db.session.commit()  # commit immediately to get the new movie's ID
        except IntegrityError:
            logger.info(f"Ignoring duplicate movie id: {row[0]} , title: {row[1]}")
            db.session.rollback()
            rowcount.decrement()
            dupecount.increment()
            pass

def add_movie_and_genre(db, row, movie_with_no_year_counter=None, **kwargs):
    id = row[0]
    original_title = row[1]
    year_match = re.search(r'\((\d{4})\)\s*$', original_title) # match the year at the end of the title
    if year_match:
        year = year_match.group(1) # get the year 
        title = re.sub(r'\(\d{4}\)\s*$', '', original_title).strip()
    else:
        year = None
        title = original_title.strip()
        # logger.info(f"--Movie with no year: {original_title}")
        if movie_with_no_year_counter:
            movie_with_no_year_counter.increment()
    movie = Movie(id=id, title=original_title, title_stripped=title, year=year)
    db.session.add(movie)
    genres = row[2].split('|')  # genres is a list of genres
    for genre in genres:  # add each genre to the movie_genre table
        movie_genre = MovieGenre(movie_id=id, genre=genre)
        db.session.add(movie_genre)


# simple counter class
class Counter:
    def __init__(self, start=0, name='Counter'):
        self.val = start
        self.name = name

    def increment(self):
        self.val += 1
        return self.val

    def decrement(self):
        self.val -= 1
        return self.val
    
    def change_by(self, amount):
        self.val += amount
        return self.val
    
    def set(self, val):
        self.val = val
        return self.val
    
    def get(self):
        return self.val
    
    def reset(self):
        self.val = 0
        return self.val
    
    def __str__(self):
        # return f'{self.name}: {self.val}'
        return str(self.val)
    
