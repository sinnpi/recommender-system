import csv
from sqlalchemy.exc import IntegrityError
from models import Movie, MovieGenre, Ratings, TagNames, Tags
from datetime import datetime
from tqdm import tqdm

def check_and_read_data(db):
    # check if we have movies in the database
    # read data if database is empty
    if Movie.query.count() == 0:
        # read movies from csv
        total = sum(1 for row in csv.reader(open('data/movies.csv', newline='', encoding='utf8'))) - 1

        with open('data/movies.csv', newline='', encoding='utf8') as csvfile:
            rowcount = 0
            dupecount = 0
            
            reader = csv.reader(csvfile, delimiter=',')
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
                        if i % 10 == 0:  # batch size, faster
                            db.session.commit()  # save data to database
                        rowcount += 1
                    except IntegrityError:
                        dupecount += 1
                        db.session.rollback()
                        pass
            db.session.commit()
        
            print(f"{total} rows read. Added {rowcount} movies to the database. Ignored {dupecount} duplicates.")

    if Ratings.query.count() == 0:
        total = sum(1 for row in csv.reader(open('data/ratings.csv', newline='', encoding='utf8'))) - 1

        with open('data/ratings.csv', newline='', encoding='utf8') as csvfile:
            rowcount = 0
            dupecount = 0

            reader = csv.reader(csvfile, delimiter=',')
            next(reader, None) # skip the header row
            for i, row in enumerate(tqdm(reader, total=total)):
                try:
                    timestamp = datetime.fromtimestamp(int(row[3]))
                    rating = Ratings(movie_id=row[1], user_id=row[0], rating=row[2], timestamp=timestamp)
                    db.session.add(rating)
                    if i % 1000 == 0: # batch size, faster
                        db.session.commit()
                    rowcount += 1
                except IntegrityError:
                    dupecount += 1
                    db.session.rollback()
                    pass

            db.session.commit()
            print(f"{total} rows read. Added {rowcount} ratings to the database. Ignored {dupecount} duplicates.")


    if Tags.query.count() == 0:
        total = sum(1 for row in csv.reader(open('data/tags.csv', newline='', encoding='utf8'))) - 1

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
                    tag = Tags(user_id=user_id, movie_id=movie_id, tag_id=tagname.id, timestamp=timestamp)
                    db.session.add(tag)

                    if i % 10 == 0:  # batch size, faster
                        db.session.commit()
                    rowcount += 1
                except IntegrityError:
                    dupecount += 1
                    db.session.rollback()
                    pass
            db.session.commit()
            print(f"{total} rows read. Added {rowcount} tags to the database. Ignored {dupecount} duplicates. {unique_tag_count} unique tags added.")