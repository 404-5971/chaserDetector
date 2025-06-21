from flask import Flask, render_template
import os
import dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import re
import urllib.parse
import urllib.request

dotenv.load_dotenv()

CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET))

app: Flask = Flask(__name__)

def generate_chaser_cache() -> dict:
    """Generate a cache of femtanyl tracks and albums."""
    # Search for femtanyl tracks
    track_results = sp.search(q='artist:femtanyl', type='track', limit=50)
    tracks = track_results['tracks']['items']
    track_list: list[str] = []
    
    # Search for femtanyl albums
    album_results = sp.search(q='artist:femtanyl', type='album', limit=50)
    albums = album_results['albums']['items']
    
    # Write tracks and albums to cache file
    with open('chaser.cache', 'w') as f:
        # Write tracks
        for track in tracks:
            if track['artists'][0]['name'] == 'femtanyl':
                track_list.append(f"{track['name']}")
                f.write(f"{track['name']}\n")
        
        # Write albums
        for album in albums:
            if album['name'] not in track_list:
                f.write(f"{album['name']}\n")

        f.write("femtanyl")
    
    print(f"Generated chaser cache with {len(tracks)} tracks and {len(albums)} albums")
    return tracks

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
    
    # if anything in the chaser.cache is in the song name, album name, or any artist's name, return 'Chaser Adjacent'
    with open('chaser.cache', 'r') as f:
        for line in f:
            if line.strip() in song_name or line.strip() in all_artists or line.strip() in song['album']['name']:
                return 'Chaser Adjacent'
    
    return 'NO'

def get_youtube_video(song_name: str, artist_name: str) -> tuple[str | None, bool]:
    """Search for a song on YouTube and return the first video ID and availability status."""
    try:
        search_query = f"{song_name} {artist_name} audio"
        encoded_query = urllib.parse.quote(search_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Get the search results page
        req = urllib.request.Request(search_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        response = urllib.request.urlopen(req)
        html = response.read().decode()
        
        # Look for video IDs in the search results
        video_id_matches = re.findall(r'"videoId":"([^"]+)"', html)
        
        if not video_id_matches:
            return None, False
        
        # Take the first video ID
        video_id = video_id_matches[0]
        
        # Conservative approach: only mark as available for:
        # 1. femtanyl tracks (which are more likely to have audio)
        # 2. Popular artists in the breakcore/speedcore/hyperpop scene
        # 3. Songs with clear artist names that match the search
        
        # Check if it's a femtanyl track
        if artist_name.lower() == 'femtanyl':
            return video_id, True
        
        # Check for other popular artists in the scene
        popular_artists = [
            'bungex', 'goreshit', 'machine girl', 'death grips', '100 gecs', 
            'charli xcx', 'sophie', 'arca', 'aphex twin', 'venetian snares'
        ]
        
        if any(artist in artist_name.lower() for artist in popular_artists):
            return video_id, True
        
        # For other artists, be more conservative - only mark as available if the search seems very specific
        # Check if the song name and artist appear together in the search results
        song_artist_combined = f"{song_name.lower()} {artist_name.lower()}"
        if song_artist_combined in html.lower():
            return video_id, True
        
        # Default to not available for unknown artists
        return video_id, False
        
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return None, False

@app.route('/')
def index():
    song = get_random_song()
    album_cover_url = song['album']['images'][0]['url'] if song['album']['images'] else None
    # Get all artist names as a list
    all_artists = [artist['name'] for artist in song['artists']]
    chaser_status = get_chaser_status(song)
    
    # Get YouTube video ID for audio playback
    youtube_video_id, is_available = get_youtube_video(song['name'], song['artists'][0]['name'])
    
    return render_template('index.html', 
                         song_name=song['name'], 
                         artist_name=song['artists'][0]['name'],
                         all_artists=all_artists,
                         album_cover_url=album_cover_url,
                         chaser_status=chaser_status,
                         youtube_video_id=youtube_video_id,
                         audio_available=is_available)

if __name__ == '__main__':
    if not os.path.exists('chaser.cache'):
        generate_chaser_cache()
    app.run(debug=True)