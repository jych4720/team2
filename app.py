from flask import Flask, request, render_template
import requests
import os
from groq import Groq


app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
TMDB_API_KEY = "45f3b72c432ea9374c433274557cb55f"
BASE_URL = "https://api.themoviedb.org/3"

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
    movies = []
    if request.method == "POST":
        query = request.form["query"]
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        response = requests.get(url).json()
        movies = response.get("results", [])
    return render_template("search.html", movies=movies)

@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):
    # Get movie details
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
    movie = requests.get(movie_url).json()

    # Get cast details (credits)
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
    return render_template("movie_detail.html", movie=movie, cast=cast, director=director, director_id=director_id)

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

    return render_template("director_detail.html", director=director,director_id=director_id)
    
@app.route("/director/<int:director_id>/description")
def director_description(director_id):
    director_url = f"{BASE_URL}/person/{director_id}?api_key={TMDB_API_KEY}&language=en-US"
    director_response = requests.get(director_url).json()
    director_name = director_response.get("name", "Unknown")

    description = get_director_description(director_name)
    return render_template("director_description.html", director_name=director_name, description=description,director_id=director_id)
    
    
@app.route("/movie/<int:movie_id>/description")
def movie_description(movie_id):
    # Get movie details
    movie_url = f"{BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
    movie_response = requests.get(movie_url).json()

    movie_title = movie_response.get("title", "Unknown")


    # Generate AI description
    ai_description = get_movie_description(movie_title)

    return render_template("movie_description.html", movie_title=movie_title, ai_description=ai_description, movie_id=movie_id)
    
    
if __name__ == "__main__":
    app.run(debug=True)
