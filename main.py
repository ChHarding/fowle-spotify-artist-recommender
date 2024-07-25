import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, render_template, flash
from flask_session import Session
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import helper_functions as helpers

# To get CLIENT_ID and CLIENT_SECRET from .env file
load_dotenv()






# [---------------------------------------------------------------]
# [-------------------------AUTHORIZATION-------------------------]
# [---------------------------------------------------------------]






# Instantiate Flask application
app = Flask(__name__)

app.secret_key = "lk3j24h25iojflasdjk9fjio"
app.config['SESSION_COOKIE_NAME'] = "Playlist Maker Cookie"
app.config['SESSION_TYPE'] = 'filesystem' # for flask_session
app.config['SECRET_KEY'] = 'asdflksdfljkwefhbn2354g'
TOKEN_INFO = "token_info"

# Instantiate flask_session library
Session(app)




def create_spotify_oauth():
    '''
    Authorizes to Spotify using the SpotifyOAuth class.

    Args:
        None

    Returns:
        The Spotify authorization object.
    '''
    return SpotifyOAuth(
        client_id = os.getenv('CLIENT_ID'),
        client_secret = os.getenv('CLIENT_SECRET'),
        redirect_uri = url_for('redirect_page', _external=True),
        # Uncomment the below line to force reauthorization
        # show_dialog = True,
        scope = "user-top-read playlist-modify-public"
    )




def get_token():
    '''
    Gets the Spotify authorization token, or refreshes an existing token.

    Args:
        None

    Returns:
        The Spotify authorization token information.
    '''
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
    '''
    Routes to the landing page, then authorizes with Spotify and redirects to the redirect page to complete the 
    authorization flow.

    Args:
        None

    Returns:
        Redirect to the authorize URL (e.g., localhost:5000/redirect).
    '''
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)




@app.route("/redirect")
def redirect_page():
    '''
    Routes to the redirect page. This passes the authorization code back to Spotify to complete the authorization flow.

    Args:
        None

    Returns:
        Redirect to /newOrFamiliar.
    '''
    sp_oauth = create_spotify_oauth()

    # Clears out session data from a previous use of the app
    session.clear()

    # Gets the authorization code from the redirect URL
    code = request.args.get('code')

    # Completes authorization by supplying the auth code to get the access token
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for("new_or_familiar_page", _external=True))




@app.route("/new-or-familiar", methods=["POST", "GET"])
def new_or_familiar_page():
    '''
    GET: Renders newOrFamiliar.html. 
    POST: Redirects to genres_page and supplies the user selection (i.e., new or familiar music)

    Args:
        None

    Returns:
        GET: Renders newOrFamiliar.html.
        POST: Redirects to genres_page and supplies the user selection.
    '''

    # Try to validate or refresh the access token
    try:
        token_info = get_token()
    except:
        redirect(url_for('home_page', _external=False))

    if request.method == "POST":

        # Get the value of the button selected
        new_or_familiar = request.form["NoFButton"]
        return redirect(url_for('genres_page', new_or_familiar = new_or_familiar))

    # GET
    # Create a reference to the Spotipy library with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    session['sp'] = sp

    # Instantiate track_list to later build and save in session
    track_list = []

    # Looper offset for iterating over user's top tracks
    looper_offset = 0

    # Get top 500 tracks
    for i in range(10):
        new_tracks = helpers.get_top_tracks(looper_offset, sp)
        track_list.extend(new_tracks)
        looper_offset += 50

    # Save track_list to session
    session['track_list'] = track_list
    return render_template("newOrFamiliar.html")




@app.route("/genres/<new_or_familiar>", methods=["POST", "GET"])
def genres_page(new_or_familiar):
    '''
    GET: Creates a list of all available genres and renders genres.html.
    POST: Adjust scores on tracks in track_list based on user input and redirects to features_page.

    Args:
        new_or_familiar: A string containing the choice (new or familiar) the user selected from the new_or_familiar page.

    Returns:
        GET: Renders genres.html.
        POST: Redirects to features_page.
    '''

    if request.method == "POST":
        user_input = request.form.getlist('genres')

        # Invokes genre_score_deduction to deduct points from each track object's "score" property
        track_list_updated_score_genres = helpers.genre_score_deduction(user_input, session.get('track_list'))

        # Update session's track_list
        session.update({'track_list': track_list_updated_score_genres})
        return redirect(url_for("features_page"))
     
    # GET
    if new_or_familiar == 'new':

        # Reset track_list to new tracks, store in session's track_list
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
    return render_template("genres.html", genres_list=genres_list)

    
   

@app.route("/features", methods=["POST", "GET"])
def features_page():
    '''
    GET: Sets the audio features (e.g., danceability, energy) on all tracks and renders features.html.
    POST: Adjust scores on tracks in track_list based on user input and redirects to playlist_page.

    Args:
        None

    Returns:
        GET: Renders features.html.
        POST: Redirects to playlist_page.
    '''

    if request.method == "POST":

        # Instantiate user_features dict to supply to feature_score_deduction
        user_features = {}

        # Get all user input and save to user_features dict
        user_features['acousticness'] = request.form.get('acousticness')
        user_features['danceability'] = request.form.get('danceability')
        user_features['energy'] = request.form.get('energy')
        user_features['instrumentalness'] = request.form.get('instrumentalness')
        user_features['liveness'] = request.form.get('liveness')
        user_features['speechiness'] = request.form.get('speechiness')
        user_features['valence'] = request.form.get('valence')

        # Deduce each track's "score" based on user input using feature_score_deduction
        track_list_features_deduced = helpers.feature_score_deduction(user_features, session.get("track_list"))

        # Update track_list in session
        session.update({'track_list': track_list_features_deduced})
        return redirect(url_for("playlist_page"))
    
    # GET
    # Set the audio features of each track
    track_list_with_audio_features = helpers.get_audio_features(session.get("track_list"), session.get("sp"))
    session.update({'track_list': track_list_with_audio_features})
    return render_template("features.html")




@app.route("/playlist", methods=["POST", "GET"])
def playlist_page():
    '''
    GET: Creates the final playlist and presents to the user.
    POST: Redirects to create_playlist_page.

    Args:
        None

    Returns:
        GET: Renders finalPlaylist.html.
        POST: Redirects to create_playlist_page.
    '''

    if request.method == "POST":

        # Get the cover art for the first 4 tracks for rendering in next page
        top_4_tracks_images = []
        top_30 = session.get("top_30_tracks")
        for track in range(4):
            cover_art = top_30[track]["album_art"]
            top_4_tracks_images.append(cover_art)

        # Saves top_4_tracks_images to the session for use in next page
        session["top_4_tracks_images"] = top_4_tracks_images

        # Render create playlist template and pass the final playlist
        return redirect(url_for("create_playlist_page"))
    
    # GET
    # Returns the top 30 tracks, randomized for a more engaging listening experience
    top_30_tracks = helpers.get_final_playlist(session.get("track_list"), session.get("sp"))
    session["top_30_tracks"] = top_30_tracks
    return render_template("finalPlaylist.html", top_30_tracks=top_30_tracks)




@app.route("/create-playlist", methods=["POST", "GET"])
def create_playlist_page():
    '''
    GET: Creates a simple page for naming and saving the playlist to Spotify.
    POST: Invokes create_new_playlist to save the playlist to Spotify, then sends the user to result_page for confirmation.

    Args:
        None

    Returns:
        GET: Renders saveToSpotify.html.
        POST: Redirects to result_page, supplying the result of the attempt to save the playlist to Spotify.
    '''

    if request.method == "POST":
        playlist_name = request.form.get('playlist_name')

        # Attempts to save to Spotify using create_new_playlist and saves the result to var success
        success = helpers.create_new_playlist(session.get("top_30_tracks"), session.get("sp"), playlist_name)
        result = ""

        # If successful, send to result_page for success message rendering
        if success == True:
            result = "success"
        else:
            result = "error"
        return redirect(url_for("result_page", result=result))

    # GET 
    # Use today's date as the default name for the playlist
    today = datetime.today()
    formatted_date = today.strftime('%m-%d-%Y')
    return render_template("saveToSpotify.html", top_4_tracks_images=session.get("top_4_tracks_images"), today=formatted_date)




@app.route("/result/<result>", methods=["POST", "GET"])
def result_page(result):
    '''
    GET: Sends the user to the result/<result>.html, which displays a message on whether the operation was successful.
    POST: If the user got a success message, the button on this page redirects to new_or_familiar_page. If the user
    got an error message, the button redirects to create_playlist_page for them to try again.

    Args:
        None

    Returns:
        GET: Renders resultsPage.html.
        POST: Redirects to new_or_familiar_page OR create_playlist_page depending on the result of the save operation 
        (success or error).
    '''

    if request.method == "POST":

        # Start over if the save took succesfully; go back to the last screen to attempt the save again if there was 
        # an error
        if result == "success":
            return redirect(url_for("new_or_familiar_page"))
        else:
            return redirect(url_for("create_playlist_page"))

    # GET 
    message = ""
    button_message = ""

    # Save the success message and button message for rendering in resultsPage.html depending on save 
    # operation success
    if result == "success":
        message = "Your playlist was successfully added to Spotify!"
        button_message = "I want another playlist!"
    else:
        message = "Something went wrong. Please try again."
        button_message = "Try again"
    return render_template("resultsPage.html", message=message, again=button_message)




# Start application
if __name__ == "__main__":
    app.run()