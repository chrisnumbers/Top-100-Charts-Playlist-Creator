#This program will find the top 100 billboard chart songs for a certain date
#and add the songs to a playlist on Spotify.

from bs4 import BeautifulSoup
import requests, spotipy, os
from spotipy.oauth2 import SpotifyOAuth

#Gather Spotify keys from Environment Variables
spotify_client_id = os.environ["SPOTIFY_CLIENT_ID"]
spotify_client_secret = os.environ["SPOTIFY_CLIENT_SECRET"]

#Select a date and set the URL for the Top 100 Billboard specific date
date = input("Input a date in this format: YYYY-MM-DD\n")
website = f"https://www.billboard.com/charts/hot-100/{date}/"

#Gather HTML data to scrape
request = requests.get(url=website)
data = BeautifulSoup(request.text, "html.parser")

#Scrapes the full song track names list
songs = [song.text.strip() for song in data.select(selector=".o-chart-results-list__item h3")]

#Scrapes the full info (Song + artist name)
song_full_list = data.select(selector="ul .lrv-u-width-100p .lrv-a-unstyle-list")

#Gets artist names and removes unwanted info
artist_with_scores = [song_info.find("span", class_="c-label").get_text(strip=True) for song_info in song_full_list]
artists_no_numbers =  [item for item in artist_with_scores if not item.isdigit()]
artists = [item for item in artists_no_numbers if item != "-"]

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id,
                                               client_secret=spotify_client_secret,
                                               redirect_uri="https://localhost:8888/callback",
                                               scope="playlist-modify-private"))



song_ids = []
#Gets the Song ID for each song
for x in range(100):
    #Spotify gives bad results if it has featured artists in the query, so we remove them first.
    pos = artists[x].find('Featuring')
    if pos != -1:
        artists[x] = artists[x][:pos].strip()

    #Tries the search with song + artist name
    full_query = f"track:{songs[x]} artist:{artists[x]}"
    search_result = sp.search(q=full_query, limit=1)
    try:

        song_ids.append(search_result["tracks"]["items"][0]["id"])
    #If there happens to be an issue where the query doesn't find a song with artist + track,
    #it will search with only the track name.
    except IndexError:
        print(f"There were no search results for this song: {full_query}. Trying search with just song name.")
        full_query = f"tracks:{songs[x]}"
        search_result = sp.search(q=full_query, limit=1)
        try:
            song_ids.append(search_result["tracks"]["items"][0]["id"])
        except IndexError:
            print("Still getting an error. Not adding to playlist.")

    
   
print(song_ids)
print("Number of Song IDs: " + str(len(song_ids)))

#Creates playlist for the Spotify User
user_id = sp.current_user()["id"]
playlist_name = f"Billboard Top 100 for {date}"
playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=False, collaborative=False, description=f"The Top 100 Songs on the Radio for {date}")

#Gather playlist ID and adds all songs to the created playlist
id = playlist["id"]
sp.playlist_add_items(playlist_id=id, items=song_ids)

print("Added all songs to playlist.")
