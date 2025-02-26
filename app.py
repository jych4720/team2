from flask import Flask, request, render_template,session,redirect,url_for
from flask_session import Session
import requests
import os
from groq import Groq
import random

app = Flask(__name__)
app.secret_key = os.urandom(24)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
TMDB_API_KEY = "45f3b72c432ea9374c433274557cb55f"
BASE_URL = "https://api.themoviedb.org/3"
quotes = []
quote_url = 'https://quoteapi.pythonanywhere.com/quotes'
response = requests.get(quote_url)
if response.status_code == 200:
    data = response.json().get("Quotes", [[]])

def get_director_description(director_name):
    """Fetches a GPT-generated description of the director."""
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Give a detailed description of features {director_name} as a film director."}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content
    
def get_movie_description(movie):
    """Fetches a GPT-generated description of the director."""
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Give a detailed description of overview for movie {movie}."}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content
    
@app.route("/", methods=["GET", "POST"])
def search():
    url="https://quoteapi.pythonanywhere.com/random"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json().get("Quotes", [[]])
        quote=data[0]
        
    movies = []
    directors = []
    search_type = "movie"

    if request.method == "POST":
        query = request.form["query"]
        search_type = request.form["search_type"]
        
        if search_type == "movie":
            url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
            response = requests.get(url).json()
            movies = response.get("results", [])
        elif search_type == "director":
            url = f"https://api.themoviedb.org/3/search/person?api_key={TMDB_API_KEY}&query={query}"
            response = requests.get(url).json()
            directors = response.get("results", [])

    return render_template("search.html", movies=movies, directors=directors,quote=quote)

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    # Get movie details
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    movie = requests.get(movie_url).json()

    credits_url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_API_KEY}"
    credits = requests.get(credits_url).json()
    cast = credits.get("cast", [])[:5]  
    crew = credits.get("crew", [])
    director_info = next((member for member in crew if member["job"] == "Director"), None)

    if director_info:
        director = director_info["name"]
        director_id = director_info["id"] 
    else:
        director= "Unknown"
        director_id = None 
    if data:
        all_quotes = data[0]
        quotes = [q for q in all_quotes if q["movie_title"].lower() == movie["title"].lower()]
        seen_quotes = set()
        unique_quotes = []
        
        for quote in quotes:
            if quote["quote"] not in seen_quotes:
                unique_quotes.append(quote)
                seen_quotes.add(quote["quote"])
    return render_template("movie_detail.html", movie=movie, cast=cast, director=director, director_id=director_id,quotes=unique_quotes)

@app.route("/director/<int:director_id>")
def director_detail(director_id):
    director_url = f"{BASE_URL}/person/{director_id}?api_key={TMDB_API_KEY}&language=en-US"
    director_movies_url = f"{BASE_URL}/person/{director_id}/movie_credits?api_key={TMDB_API_KEY}&language=en-US"

    director_response = requests.get(director_url).json()
    movies_response = requests.get(director_movies_url).json()

    director = {
        "name": director_response.get("name", "Unknown"),
        "profile_path": f"https://image.tmdb.org/t/p/w500{director_response.get('profile_path')}" if director_response.get("profile_path") else None,
        "biography": director_response.get("biography", "No biography available."),
        "movies": movies_response.get("crew", [])
    }
    unique_movies = []
    seen_movie_ids = set()

    for movie in director["movies"]:
        if movie["id"] not in seen_movie_ids:
            unique_movies.append(movie)
            seen_movie_ids.add(movie["id"])
    return render_template("director_detail.html", director=director,director_id=director_id, unique_movies=unique_movies)
    
@app.route("/director/<int:director_id>/description")
def director_description(director_id):
    director_url = f"{BASE_URL}/person/{director_id}?api_key={TMDB_API_KEY}&language=en-US"
    director_response = requests.get(director_url).json()
    director_name = director_response.get("name", "Unknown")

    description = get_director_description(director_name)
    return render_template("director_description.html", director_name=director_name, description=description,director_id=director_id)
    
    
@app.route("/movie/<int:movie_id>/description")
def movie_description(movie_id):
    movie_url = f"{BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    movie_response = requests.get(movie_url).json()

    movie_title = movie_response.get("title", "Unknown")


    # Generate AI description
    ai_description = get_movie_description(movie_title)

    return render_template("movie_description.html", movie_title=movie_title, ai_description=ai_description, movie_id=movie_id)
    
@app.route("/favorites")
def favorites():
    favorite_movies = session.get("favorites_movies", [])
    favorite_directors = session.get("favorites_directors", [])
    return render_template("favorites.html", favorite_movies=favorite_movies, favorite_directors=favorite_directors)

@app.route("/favorites/add/movie/<int:movie_id>/<string:movie_title>")
def add_favorite_movie(movie_id, movie_title):
    favorites_movies = session.get("favorites_movies", [])
    if movie_id not in [movie["id"] for movie in favorites_movies]:
        favorites_movies.append({"id": movie_id, "title": movie_title, "user_input": ""})
    session["favorites_movies"] = favorites_movies
    return redirect(url_for("favorites"))

@app.route("/favorites/remove/movie/<int:movie_id>")
def remove_favorite_movie(movie_id):
    favorites_movies = session.get("favorites_movies", [])
    favorites_movies = [movie for movie in favorites_movies if movie["id"] != movie_id]
    session["favorites_movies"] = favorites_movies
    return redirect(url_for("favorites"))

@app.route("/favorites/update/movie", methods=["POST"])
def update_favorites_movie():
    favorites_movies = session.get("favorites_movies", [])
    
    for movie in favorites_movies:
        movie_id = movie["id"]
        user_comment = request.form.get(f"comment_movie_{movie_id}")
        movie["user_input"] = user_comment
        
    session["favorites_movies"] = favorites_movies
    return redirect("/favorites")


@app.route("/favorites/add/director/<int:director_id>/<string:director_name>")
def add_favorite_director(director_id, director_name):
    favorites_directors = session.get("favorites_directors", [])
    if director_id not in [director["id"] for director in favorites_directors]:
        favorites_directors.append({"id": director_id, "name": director_name, "user_input": ""})
    session["favorites_directors"] = favorites_directors
    return redirect(url_for("favorites"))

@app.route("/favorites/remove/director/<int:director_id>")
def remove_favorite_director(director_id):
    favorites_directors = session.get("favorites_directors", [])
    favorites_directors = [director for director in favorites_directors if director["id"] != director_id]
    session["favorites_directors"] = favorites_directors
    return redirect(url_for("favorites"))

@app.route("/favorites/update/director", methods=["POST"])
def update_favorites_director():
    favorites_directors = session.get("favorites_directors", [])
    
    for director in favorites_directors:
        director_id = director["id"]
        user_comment = request.form.get(f"comment_director_{director_id}")
        director["user_input"] = user_comment
        
    session["favorites_directors"] = favorites_directors
    return redirect("/favorites")
    
@app.route("/random_movie", methods=["POST"])
def random_movie():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}"
    response = requests.get(url).json()
    popular_movies = response.get("results", [])
    random_movie = random.choice(popular_movies)
    random_movie_id = random_movie['id']
    return redirect(url_for('movie_detail', movie_id=random_movie_id))
    
if __name__ == "__main__":
    app.run(debug=True)
