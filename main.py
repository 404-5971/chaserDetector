from flask import Flask, render_template
import os
import dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random

dotenv.load_dotenv()

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

app: Flask = Flask(__name__)

def get_random_song() -> dict:
    randint: int = random.randint(1, 4)
    if randint == 1:
        # Get a random song by femtanyl
        results = sp.search(q=f'artist:femtanyl', type='track', limit=50)
        tracks = results['tracks']['items']
    else:
        # Create a list of genres to search from
        genres = ['breakcore', 'speedcore', 'hyperpop']
        # Randomly select a genre
        selected_genre = random.choice(genres)
        results = sp.search(q=f'genre:{selected_genre}', type='track', limit=50)
        tracks = results['tracks']['items']
        
        # results = sp.search(q=f'artist:bungex', type='track', limit=50)
        # tracks = results['tracks']['items']

    return random.choice(tracks)

def get_chaser_status(song: dict) -> str:
    """Determine if a song is chaser, chaser adjacent, or not chaser."""
    song_name = song['name'].lower()
    all_artists = [artist['name'].lower() for artist in song['artists']]
    
    # Check if primary artist is femtanyl
    if all_artists[0] == 'femtanyl':
        return 'YES'
    
    # Check if femtanyl appears anywhere (song name or any artist)
    if 'femtanyl' in song_name or 'femtanyl' in all_artists:
        return 'Chaser Adjacent'
    
    return 'NO'

@app.route('/')
def index():
    song = get_random_song()
    album_cover_url = song['album']['images'][0]['url'] if song['album']['images'] else None
    # Get all artist names as a list
    all_artists = [artist['name'] for artist in song['artists']]
    chaser_status = get_chaser_status(song)
    return render_template('index.html', 
                         song_name=song['name'], 
                         artist_name=song['artists'][0]['name'],
                         all_artists=all_artists,
                         album_cover_url=album_cover_url,
                         chaser_status=chaser_status)

if __name__ == '__main__':
    app.run(debug=True)