import requests
api_url = 'https://quoteapi.pythonanywhere.com/quotes'
movie_title="The Fast and the Furious: Tokyo Drift"
response = requests.get(api_url)
if response.status_code == 200:
    data = response.json().get("Quotes", [[]])
    if data:
        quotes = data[0]
        quotes = [q for q in quotes if q["movie_title"].lower() == movie_title.lower()]
        print(quotes)
else:
    print('Failed to fetch data from API:', response.status_code)
