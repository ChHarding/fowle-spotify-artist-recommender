import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template, flash
from flask_session import Session
import time
import os
from dotenv import load_dotenv
import helper_functions as helpers

load_dotenv()






# [---------------------------------------------------------------]
# [-------------------------AUTHORIZATION-------------------------]
# [---------------------------------------------------------------]






app = Flask(__name__)

app.secret_key = "lk3j24h25iojflasdjk9fjio"
app.config['SESSION_COOKIE_NAME'] = "Playlist Maker Cookie"
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'asdflksdfljkwefhbn2354g'
TOKEN_INFO = "token_info"

Session(app)



def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for('redirect_page', _external=True),
        scope = "user-top-read playlist-modify-public"
    )




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





# [---------------------------------------------------------------]
# [--------------------------FLASK PAGES--------------------------]
# [---------------------------------------------------------------]






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




@app.route("/new-or-familiar", methods=["POST", "GET"])
def new_or_familiar_page():

    # Try to validate or refresh the access token
    try:
        token_info = get_token()
    except:
        redirect(url_for('home_page', _external=False))

    if request.method == "POST":
        # Get the value of the button selected
        new_or_familiar = request.form["NoFButton"]
        return redirect(url_for('genres_page', new_or_familiar = new_or_familiar))

    # Create a reference to the Spotipy library with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    session['sp'] = sp

    track_list = []

    # Looper offset for iterating over user's top tracks
    looper_offset = 0

    # Get top 500 tracks
    for i in range(10):
        new_tracks = helpers.get_top_tracks(looper_offset, sp)
        track_list.extend(new_tracks)
        looper_offset += 50

    session['track_list'] = track_list
    return render_template("newOrFamiliar.html")






@app.route("/genres/<new_or_familiar>", methods=["POST", "GET"])
def genres_page(new_or_familiar):
    if request.method == "POST":
        user_input = request.form.getlist('genres')
        track_list_updated_score_genres = helpers.genre_score_deduction(user_input, session.get('track_list'))
        session.update({'track_list': track_list_updated_score_genres})
        return redirect(url_for("features_page"))
     
    if new_or_familiar == 'new':
        # Reset track_list to new tracks, store in global track_list
        novel_track_list = helpers.get_new_tracks(session.get("track_list"), session.get("sp"))
        session.update({'track_list': novel_track_list})
        # Set artist genres in track_list
        track_list_with_genres = helpers.set_artist_genres(session.get("track_list"), session.get("sp"))
        session.update({"track_list": track_list_with_genres})

    if new_or_familiar == 'familiar':
        # Retain original track_list and set artist genres
        track_list_with_genres = helpers.set_artist_genres(session.get("track_list"), session.get("sp"))
        session.update({"track_list": track_list_with_genres})

    # Create genres list for genres_page rendering    
    genres_list = helpers.create_genres_list(track_list_with_genres)
    return render_template("genres.html", new_or_familiar=new_or_familiar, genres_list=genres_list)

    
   




@app.route("/features", methods=["POST", "GET"])
def features_page():
    if request.method == "POST":
        user_features = {}

        user_features['acousticness'] = request.form.get('acousticness')
        user_features['danceability'] = request.form.get('danceability')
        user_features['energy'] = request.form.get('energy')
        user_features['instrumentalness'] = request.form.get('instrumentalness')
        user_features['liveness'] = request.form.get('liveness')
        user_features['speechiness'] = request.form.get('speechiness')
        user_features['valence'] = request.form.get('valence')

        track_list_features_deduced = helpers.feature_score_deduction(user_features, session.get("track_list"))
        session.update({'track_list': track_list_features_deduced})
        return redirect(url_for("playlist_page"))
    
    track_list_with_audio_features = helpers.get_audio_features(session.get("track_list"), session.get("sp"))
    session.update({'track_list': track_list_with_audio_features})
    return render_template("features.html")




@app.route("/playlist", methods=["POST", "GET"])
def playlist_page():
    if request.method == "POST":
        # Render create playlist template and pass the final playlist
        return redirect(url_for("create_playlist_page"))
    
    top_30_tracks = helpers.get_final_playlist(session.get("track_list"), session.get("sp"))
    session["top_30_tracks"] = top_30_tracks # Save here for passing to /create_playlist
    return render_template("finalPlaylist.html", top_30_tracks=top_30_tracks)




@app.route("/create-playlist", methods=["POST", "GET"])
def create_playlist_page():
    if request.method == "POST":
        playlist_name = request.form.get('playlist_name')
        success = helpers.create_new_playlist(session.get("top_30_tracks"), session.get("sp"), playlist_name)
        if success == True:
            flash('Playlist created successfully!')
        else:
            flash('Playlist creation failed, please try again')
            return render_template("saveToSpotify.html", playlist=session.get("top_30_tracks"))
        
    return render_template("saveToSpotify.html", playlist=session.get("top_30_tracks"))





if __name__ == "__main__":
    app.run(debug=True)