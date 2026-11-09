import os
import requests
from sqlalchemy.exc import SQLAlchemyError

from dotenv import load_dotenv

from models import db, User, Movie

load_dotenv()

OMDB_API_KEY = os.getenv("OMDB_API_KEY")

API_URL = "https://www.omdbapi.com/"


class DataManager:
    def create_user(self, name):
        """
        Fügt einen neuen Nutzer zu der Datenbank hinzu.
        :param name: Name des Nutzers
        :return:
        """
        try:
            new_user = User(name=name)
            db.session.add(new_user)
            db.session.commit()
            return new_user

        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_users(self):
        """
        :return: Liste aller Nutzer in der Datenbank
        """
        try:
            users = User.query.all()
            return users

        except SQLAlchemyError:
            db.session.rollback()
            return []

    def get_movies(self, user_id):
        """
        :param user_id: ID des Nutzers, dessen Filme aufgelistet werden sollen
        :return: eine Liste aller Filme eines bestimmten Nutzers
        """
        try:
            movies = Movie.query.filter_by(user_id=user_id).all()
            return movies

        except SQLAlchemyError:
            db.session.rollback()
            return []

    def add_movie(self, title, user_id, year=None):
        """
        Fügt einen neuen Film zu der Favoriten-Datenbank des Nutzers hinzu.
        :param:
            title: Titel des Films, der hinzugefügt werden soll
            user_id: die ID des Nutzers, zu dessen Favoriten der Film hinzugefügt wird
            year: Optionales Erscheinungsjahr zur genaueren Filmsuche
        :return: Filmobjekt bei Erfolg oder ein Fehlerstatus als String
        """
        params = {
            "apikey": OMDB_API_KEY,
            "t": title
        }

        if year:
            params["y"] = year

        try:
            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException:
            return "api_error"

        if data.get("Response") == "False":
            return "not_found"

        movie = Movie(
            name=data['Title'],
            director=data['Director'],
            year=data['Year'],
            poster_url=data['Poster'],
            user_id=user_id
        )

        try:
            db.session.add(movie)
            db.session.commit()
            return movie

        except SQLAlchemyError:
            db.session.rollback()
            return "database_error"

    def update_movie(self, movie_id, user_id, new_title):
        """
        Aktualisiere die Details eines bestimmten Films in der Datenbank.
        :param:
            movie_id: ID des bestehenden Films
            new_title: neuer Titel des Films
            user_id: ID des Nutzers, dem der Film zugeordnet ist
        :return: aktualisierter Film oder None, falls nicht gefunden
        """
        movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first()

        if movie is None:
            return None

        try:
            movie.name = new_title
            db.session.commit()
            return movie

        except SQLAlchemyError:
            db.session.rollback()
            return None

    def delete_movie(self, movie_id, user_id):
        """
        Entferne den Film aus der Favoritenliste des Nutzers.
        :param:
            movie_id: ID des Films
            user_id: ID des Nutzers, dem der Film zugeordnet ist
        :return: True bei Erfolg, False, falls nicht gefunden
        """
        movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first()

        if movie is None:
            return False

        try:
            db.session.delete(movie)
            db.session.commit()
            return True

        except SQLAlchemyError:
            db.session.rollback()
            return False
