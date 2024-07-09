import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template
import time
import os
from dotenv import load_dotenv
import helper_functions as helpers

load_dotenv()






# [---------------------------------------------------------------]
# [--------------------------FLASK PAGES--------------------------]
# [---------------------------------------------------------------]






app = Flask(__name__)

app.secret_key = "lk3j24h25iojflasdjk9fjio"
app.config['SESSION_COOKIE_NAME'] = "Playlist Maker Cookie"
TOKEN_INFO = "token_info"




def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for('redirect_page', _external=True),
        scope = "user-top-read playlist-modify-public"
    )




@app.route("/")
def home_page():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)




@app.route("/redirect")
def redirect_page():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("new_or_familiar_page", _external=True))




@app.route("/new-or-familiar")
def new_or_familiar_page():

    # Try to validate or refresh the access token
    try:
        token_info = get_token()
    except:
        redirect(url_for('home_page', _external=False))

    # Create a reference to the Spotipy library with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Instantiante initial track_list
    track_list = []

    # Looper offset for iterating over user's top tracks
    looper_offset = 0

    # Get top 500 tracks
    for i in range(10):
        new_tracks = helpers.get_top_tracks(looper_offset, sp)
        track_list.extend(new_tracks)
        looper_offset += 50

    return render_template("base.html")




def get_token():
    '''Gets token information or refreshes the token if it has expired.'''
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise "exception"
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info




@app.route("/genres")
def genres_page():
    return "Genres!"




@app.route("/features")
def features_page():
    return "Features!"




@app.route("/playlist")
def playlist_page():
    return "Playlist!"




@app.route("/create-playlist")
def create_playlist_page():
    return "Creating playlist!"





if __name__ == "__main__":
    app.run(debug=True)






# [--------------------------MAIN FLOW--------------------------]






# print("**********************************************************")
# print("*                                                        *")
# print("*       Welcome to the Spotify playlist generator!       *")
# print("*                                                        *")
# print("**********************************************************\n")

# # Set track_list to user's top 100 songs of the last year
# looper_offset = 0
# for i in range(10): # This fires only twice to mitigate rate limiting. The real application will fire get_top_tracks 
#     new_tracks = get_top_tracks(looper_offset)
#     track_list.extend(new_tracks)
#     looper_offset += 50

# # The user interface of the final product will make use of buttons and multi-select boxes, 
# # so I am choosing to not spend time working on input validation for this version since it won't be engaged in the final product.
# new_or_familiar = input('Would you like to listen to familiar music or new music? Enter 1 for familiar and 2 for new: ') 
# if new_or_familiar == '1':
#     # Retains the original top tracks, then gets the track's audio features to complete each track object for later calculations
#     track_list = get_audio_features(track_list)
# if new_or_familiar == '2':
#     # Fires get_new_tracks to rewrite top_tracks, using the current top tracks for its operations
#     track_list = get_new_tracks(track_list)
#     track_list = get_audio_features(track_list)

# # Genres are properties of artists, not tracks. 
# # This function pulls genres from artists and parses the genres to each track, which isn't 
# # logically perfect, but is a feature I think will be useful to users
# track_list = set_artist_genres(track_list)
# genres_dict = create_genres_dict(track_list) # Creates a dictionary of genres for below...

# print('Here is a list of available genres. Enter the numbers of the genres you want to listen to, separated by a space (e.g., 1 43 5 24 8)')
# # For each genre in the list, display the genre with a key index. Users enter the index number to indicate what sounds good to them right now. This will be replaced with a multi-select interface in the final version.
# for idx, genre in genres_dict.items():
#     print(f'{idx}: {genre}')
# genre_input = input('Genres I want to listen to: ')
# genre_score_deduction(genre_input)

# # Scores for each of the features. The UI in the final product will explain what each feature is. Rather than text entry, each question will have a slider ranging from 0 to 100 with a default value to prevent any errors.
# acousticness_input_value = float(input('Enter an acousticness score between 0 and 100: '))
# danceability_input_value = float(input('Enter a danceability score between 0 and 100: '))
# energy_input_value = float(input('Enter an energy score between 0 and 100: '))
# instrumentalness_input_value = float(input('Enter an instrumentalness score between 0 and 100: '))
# liveness_input_value = float(input('Enter a liveness score between 0 and 100: '))
# speechiness_input_value = float(input('Enter a speechiness score between 0 and 100: '))
# valence_input_value = float(input('Enter a valence score between 0 and 100: '))

# # Deduces the score of each track for each value entered by the user. 
# feature_score_deduction(acousticness_input_value, feature='acousticness')
# feature_score_deduction(danceability_input_value, feature='danceability')
# feature_score_deduction(energy_input_value, feature='energy')
# feature_score_deduction(instrumentalness_input_value, feature='instrumentalness')
# feature_score_deduction(liveness_input_value, feature='liveness')
# feature_score_deduction(speechiness_input_value, feature='speechiness')
# feature_score_deduction(valence_input_value, feature='valence')

# print("Here is your final playlist!")
# playlist = get_final_playlist(track_list) # Calculates and displays the final playlist, and saves to a variable for if the user wants to save the playlist to Spotify

# print()
# # Option for exporting the playlist to Spotify
# create_new_playlist_input = input("Would you like to save this playlist to Spotify? Enter y for yes and n for no: ")
# if create_new_playlist_input == 'y':
#     create_new_playlist(playlist) # Create a new playlist with the top 30 displayed in this app
# else:
#     print("Thanks for using the Spotify playlist generator!")