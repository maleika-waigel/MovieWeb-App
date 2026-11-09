import os
from flask import Flask, render_template, request, redirect, url_for

from data_manager import DataManager
from models import db, Movie, User


app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

data_manager = DataManager()


@app.route('/')
def index():
    """
    Die Startseite. Zeigt eine Liste aller registrierten Nutzer
    und ein Formular zum Hinzufügen neuer Nutzer.
    (Diese Route verwendet standardmäßig GET.)
    :return: Gerenderte HTML-Seite mit allen Nutzern
    """
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users', methods=['POST'])
def add_user():
    """
    Wenn der Nutzer das „Nutzer hinzufügen“-Formular abschickt, wird eine POST-Anfrage ausgelöst.
    Der Server erhält die neuen Nutzerdaten, fügt sie der Datenbank hinzu und leitet dann zurück zu /.
    :return: Weiterleitung zur Startseite
    """
    name = request.form.get('name', '').strip()
    if name:
        data_manager.create_user(name)

    return redirect(url_for('index'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def get_user_movies(user_id):
    """
    Ruft die Liste der Lieblingsfilme eines Nutzers ab und zeigt sie an.
    :param user_id: ID des Nutzers, dessen Filme angezeigt werden sollen
    :return: Gerenderte HTML-Seite mit den Lieblingsfilmen des Nutzers
    """
    user = db.session.get(User, user_id)

    if user is None:
        return redirect(url_for('index'))

    movies = data_manager.get_movies(user_id)
    return render_template('movies.html', movies=movies, user_id=user_id, user=user)


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
    Fügt einen neuen Film zur Favoritenliste eines Nutzers hinzu.
    :return: Weiterleitung zur Filmliste des Nutzers
    """
    user = db.session.get(User, user_id)

    if user is None:
        return redirect(url_for('index'))

    title = request.form.get('title', '').strip()
    year = request.form.get('year', '').strip()

    if not year:
        year = None

    message = None

    if title:
        result = data_manager.add_movie(title, user_id, year)

        if result == "not_found":
            message = "Movie not found. Please check the title."
        elif result == "api_error":
            message = "The movie database is currently unavailable."
        elif result == "database_error":
            message = "The movie could not be saved. Please try again."
        elif isinstance(result, Movie):
            message = "Movie successfully added."
        else:
            message = "An unexpected error occurred. Please try again."

    else:
        message = "Please enter a movie title."

    return render_template(
        'movies.html',
        movies=data_manager.get_movies(user_id),
        user_id=user_id,
        user=user,
        message=message
    )


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id, movie_id):
    """
    Den Titel eines bestimmten Films in der Liste eines Nutzers ändern.
    :param user_id: ID des Nutzers
    :param movie_id: ID des Films
    :return: Weiterleitung zur Filmliste des Nutzers
    """
    user = db.session.get(User, user_id)

    if user is None:
        return redirect(url_for('index'))

    new_title = request.form.get('new_title', '').strip()

    if new_title:
        data_manager.update_movie(movie_id, user_id, new_title)

    return redirect(url_for('get_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """
    Entfernt einen bestimmten Film aus der Liste der Lieblingsfilme eines Nutzers.
    :param:
        user_id: ID des Nutzers
        movie_id: ID des Films, der gelöscht werden soll
    :return: Weiterleitung zur Filmliste des Nutzers
    """
    user = db.session.get(User, user_id)

    if user is None:
        return redirect(url_for('index'))

    data_manager.delete_movie(movie_id, user_id)

    return redirect(url_for('get_user_movies', user_id=user_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run()
