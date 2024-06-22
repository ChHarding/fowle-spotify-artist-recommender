import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import os
from dotenv import load_dotenv

load_dotenv()






# [------------------------------------------------------------]
# [-----------------------AUTHENTICATION-----------------------]
# [------------------------------------------------------------]






# Environment variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:4000'

# Access scope: user-top-read allows the app to pull the current authenticated user's top tracks; plyalist-modify-public allows for the creation and population of a new playlist in Spotify using data from this program
SCOPE = 'user-top-read playlist-modify-public'

# Set up the Spotify OAuth handler
sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE
)

# Creates the Spotify client, which enables me to use Spotipy methods
sp = spotipy.Spotify(auth_manager=sp_oauth)






# [---------------------------------------------------------------]
# [-----------------------PROGRAM FUNCTIONS-----------------------]
# [---------------------------------------------------------------]






# Main track list for the program
track_list = []



# Get current user's top 100 tracks on program startup
def get_top_tracks(offset):
    # current_user_top_tracks gets the user's top tracks of 'long_term' (i.e., the last year). It can only produce 50 tracks at a time, so it needs to fire multiple times to get a larger list. It uses the offset flag to paginate through current results.
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term', offset=offset)
    # Loop parses all track data needed for the program from the response into a track object, all of which are stored in track_list
    for track in top_tracks['items']:
        track_object = {
            'track_id': track['id'],
            'track_uri': track['uri'],
            'artists': [artist['name'] for artist in track['artists']],
            'artist_uris': [artist['uri'] for artist in track['artists']],
            'track_name': track['name'],
            'album_name': track['album']['name'],
            'genres': [],
            'artist_image': track['album']['images'][0]['url'] if track['album']['images'] else None, # Grabs first image if there is one available, otherwise saves nothing
            'acousticness': 1.0,
            'danceability': 1.0,
            'energy': 1.0,
            'instrumentalness': 1.0,
            'liveness': 1.0,
            'speechiness': 1.0,
            'valence': 1.0,
            'score': 100.00
        }
        track_list.append(track_object)
    return track_list




# Get audio features for all tracks in track_list
def get_audio_features():
    for track in track_list:
        # Needed to put the try/except block here since not all tracks have audio features, especially more obscure or underground tracks. Need to figure out how this plays into the score deduction still, since this doesn't change the initial value from 100 at all, which would give preference to tracks that don't have audio features available, or only have values associated with some features.


        # TO DO: Update so that it tries each feature separately, otherwise it might bail out at any point if it doesn't find a value


        try:
            track_audio_features = sp.audio_features(tracks=track['track_id'])[0]
            track['acousticness'] = track_audio_features['acousticness']
            track['danceability'] = track_audio_features['danceability']
            track['energy'] = track_audio_features['energy']
            track['instrumentalness'] = track_audio_features['instrumentalness']
            track['liveness'] = track_audio_features['liveness']
            track['speechiness'] = track_audio_features['speechiness']
            track['valence'] = track_audio_features['valence']
        except:
            continue




# Set track ids from get_new_tracks as new track objects in track_list
def set_novel_track_list(ids):
    # sp.tracks only accepts up to 50 track IDs, so this needs to loop in get_new_tracks if there are more than 50 available tracks
    tracks_results = sp.tracks(ids)
    for track in tracks_results['tracks']:
        track_object = {
            'track_id': track['id'],
            'track_uri': track['uri'],
            'artists': [artist['name'] for artist in track['artists']],
            'artist_uris': [artist['uri'] for artist in track['artists']],
            'track_name': track['name'],
            'album_name': track['album']['name'],
            'genres': [],
            'artist_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'acousticness': 1.0,
            'danceability': 1.0,
            'energy': 1.0,
            'instrumentalness': 1.0,
            'liveness': 1.0,
            'speechiness': 1.0,
            'valence': 1.0,
            'score': 100.00
        }
        # Writes each new track object to the newly scrubbed track_list
        track_list.append(track_object)




# Get unfamiliar (new) track IDs, and triggers set_novel_track_list to construct a new list of track_list of new and unfamiliar music
def get_new_tracks(track_list):
    # Get IDs for all familiar tracks from initial values of track_list for later comparison
    familiar_track_ids = []
    for track in track_list:
        familiar_track_ids.append(track['track_id']) # Creates a lightweight list of just the track_ids

    # Instantiate list to collect track ids of recommended tracks
    new_track_ids = []

    # Counter used to loop over top 100 tracks in track_list (REMINDER: ORDER LIST AT START OF PROCESS, NOT END??? - no score available yet...hmm)
    familiar_track_counter = 0

    # Loops over top 100 tracks 20 times in 5-item increments. This is so that each track in the top 100 is fed to sp.recommendations
    for familiar_track_group in range(20):
        # Gets sp.recommendations for familiar tracks in track_list n through n+5
        recommended_tracks = sp.recommendations(seed_tracks=familiar_track_ids[familiar_track_counter:familiar_track_counter+5], limit=5)

        for recommended_track in recommended_tracks['tracks']:
            # Adds the track ID to the new list
            new_track_ids.append(recommended_track['id'])

        # Increments so that the loop looks at the next 5 familiar tracks
        familiar_track_counter += 5
    
    # Checks if new_track_ids exist in familiar_track_ids; removes duplicates and builds a new list of ids
    # This is so that the user truly finds new music using the app. The sp.recommendations method doesn't necessarily return new music.
    actually_new_track_ids = [id for id in new_track_ids if id not in familiar_track_ids]
    cleaned_new_track_ids = list(set(actually_new_track_ids)) # Converts to a set, then back to a list to remove duplicates within itself, incase recommendations overlapped

    # Delete contents of track_list to make room for novel track objects
    track_list = []

    if len(cleaned_new_track_ids) > 50:
        set_novel_track_list(cleaned_new_track_ids[:50]) # Trigger once for the first 50
        set_novel_track_list(cleaned_new_track_ids[50:]) # Trigger again for everything after the first 50. Because the limit of 100 tracks is hard coded, only these two function calls are necessary. The 50 limit is a constraint of the sp.tracks method
    else:
        set_novel_track_list(cleaned_new_track_ids)

    


# Set the genres for each tracks. Genres are properties of artists, not tracks, so this function extracts artist info from tracks and pushes the genre information to the track object in track_list
def set_artist_genres():
    for track in track_list:
        # for if there are multiple artists on one track
        for uri in track['artist_uris']:
            genres = sp.artist(uri)['genres']
            # deconstruct nested lists for each track object
            for genre in genres:
                track['genres'].append(genre)




# Creates a dictionary of all genres for later reference
def create_genres_dict():
    # Instantiate temporary list, which is returned and saved to the global genres_dict list
    temp_genres_list = []
    # For loop saves all genres from all tracks into temp_genres_list
    for track in track_list:
        for genre in track['genres']:
            temp_genres_list.append(genre)
    temp_genres_set = set(temp_genres_list) # set() to remove duplicates
    # Turn the genres list into a dictionary where the key for each value is its index. This is necessary for the user input (see genre_score_deduction)
    temp_genres_dict = {index: item for index, item in enumerate(temp_genres_set)}
    return temp_genres_dict




# Deduce scores for tracks that don't contain any of the selected genres
def genre_score_deduction(genre_input):
    input_list = genre_input.split(' ') # Turns user string input of genre keys into a list
    # This compares the user input to the KEYS of genres_dict to retrieve the values. I opted to use this method so that the user simply needed to enter the numeric key instead of type out the genre name, which can get long and complicated and introduce more room for error.
    input_genres_list = [genres_dict[int(key)] for key in input_list] 
    # For each track...
    for track in track_list:
        # If any genre of that track matches what the user put in...
        if any(genre in track['genres'] for genre in input_genres_list):
            continue # ...do nothing (retain a higher score)
        else:
            track['score'] -= 30 # ...if there is NOT a match, deduce 30 points from the score, which deprioritizes the track




# Deduce the track score based on feature input
def feature_score_deduction(input_value, feature): # I am passing the feature name as an argument so I don't need to construct 7 functions for each audio feature
    for track in track_list:
        track_feature_value = track[feature]
        # This gets a positive value for the difference between what the user submitted and the value of the feature on the track
        value_difference = abs(track_feature_value - input_value)
        if value_difference == 0: # If there is a perfect match...
            continue # ...do nothing (deduce 0 points)
        else: # If there is a difference in score and user input
            dissimilarity_percentage = value_difference / 100 # Get a "dissimilarity percentage"...
            track['score'] -= 10 * dissimilarity_percentage # Normalize the dissimilarity to a maximum value of 10 points to deduce, then subtract those points from the track's score
        



# Get top tracks for list
def get_final_playlist():
    # Use sorted() with a lambda function to sort all list objects based on the track's score, starting with the highest score
    sorted_track_list = sorted(track_list, key=lambda track: track['score'], reverse=True)
    # Instantiate list for top 30
    top_30_tracks = []
    # Try/except block used for testing smaller batches to avoid rate limiting
    try:
        top_30_tracks = sorted_track_list[:30] # Returns the first 30 in the list, i.e., the 30 tracks with the highest scores
    except:
        top_30_tracks = sorted_track_list # If there are less than 30 tracks (from smaller requests done during testing), do nothing
    # I'm shuffling the top 30 here to make the playlist more engaging to listen to. If the playlist was put in order from best to worst, it would get less enjoyable to listen to as the user progresses through it.
    random.shuffle(top_30_tracks)
    # Final output
    for idx, track in enumerate(top_30_tracks):
        print(f"{idx + 1}: {track['track_name']} - {', '.join(track['artists'])}\t Match: {round(track['score'], 2)}%")
    return top_30_tracks




# Create a new playlist on Spotify
def create_new_playlist(playlist):
    # Get authenticated user information, then save the user's ID
    current_user = sp.current_user()
    user_id = current_user['id']
    # Get a name for the new playlist
    playlist_name_input = input("What would you like to name your new playlist?: ")
    # Try to create a new playlist with the given name
    try:
        new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name_input) # Create the new empty playlist
        new_playlist_id = new_playlist['id'] # Get the new playlist's ID for later populating it
        # Create a new simple list for collecting track URIs, which are needed to populate the playlist
        playlist_uris = [] 
        for track in playlist:
            playlist_uris.append(track['track_uri'])
        # Add the top tracks to the new playlist
        sp.user_playlist_add_tracks(user=user_id, playlist_id=new_playlist_id, tracks=playlist_uris)
        print('All done! Enjoy your new playlist in Spotify!') # Complete!
    except: 
        print('There was an error creating the new playlist in Spotify!') # Catch-all if there are any errors in the playlist create/populate process






# [--------------------------MAIN FLOW--------------------------]






print("**********************************************************")
print("*                                                        *")
print("*       Welcome to the Spotify playlist generator!       *")
print("*                                                        *")
print("**********************************************************\n")

# Set track_list to user's top 100 songs of the last year
looper_offset = 0
for i in range(2): # This fires only twice to mitigate rate limiting. The real application will fire get_top_tracks 
    get_top_tracks(looper_offset)
    looper_offset += 50

# The user interface of the final product will make use of buttons and multi-select boxes, so I am choosing to not spend time working on input validation for this version since it won't be engaged in the final product.
new_or_familiar = input('Would you like to listen to familiar music or new music? Enter 1 for familiar and 2 for new: ') 
if new_or_familiar == '1':
    # Retains the original top tracks, then gets the track's audio features to complete each track object for later calculations
    get_audio_features()
if new_or_familiar == '2':
    # Fires get_new_tracks to rewrite top_tracks, using the current top tracks for its operations
    get_new_tracks(track_list)
    get_audio_features()

set_artist_genres() # Genres are properties of artists, not tracks. This function pulls genres from artists and parses the genres to each track, which isn't logically perfect, but is a feature I think will be useful to users.
genres_dict = create_genres_dict() # Creates a dictionary of genres for below...

print('Here is a list of available genres. Enter the numbers of the genres you want to listen to, separated by a space (e.g., 1 4 5 24 8)')
# For each genre in the list, display the genre with a key index. Users enter the index number to indicate what sounds good to them right now. This will be replaced with a multi-select interface in the final version.
for idx, genre in genres_dict.items():
    print(f'{idx}: {genre}')
genre_input = input('Genres I want to listen to: ')
genre_score_deduction(genre_input)

# Scores for each of the features. The UI in the final product will explain what each feature is. Rather than text entry, each question will have a slider ranging from 0 to 100 with a default value to prevent any errors.
acousticness_input_value = float(input('Enter an acousticness score between 0 and 100: '))
danceability_input_value = float(input('Enter a danceability score between 0 and 100: '))
energy_input_value = float(input('Enter an energy score between 0 and 100: '))
instrumentalness_input_value = float(input('Enter an instrumentalness score between 0 and 100: '))
liveness_input_value = float(input('Enter a liveness score between 0 and 100: '))
speechiness_input_value = float(input('Enter a speechiness score between 0 and 100: '))
valence_input_value = float(input('Enter a valence score between 0 and 100: '))

# Deduces the score of each track for each value entered by the user. 
feature_score_deduction(acousticness_input_value, feature='acousticness')
feature_score_deduction(danceability_input_value, feature='danceability')
feature_score_deduction(energy_input_value, feature='energy')
feature_score_deduction(instrumentalness_input_value, feature='instrumentalness')
feature_score_deduction(liveness_input_value, feature='liveness')
feature_score_deduction(speechiness_input_value, feature='speechiness')
feature_score_deduction(valence_input_value, feature='valence')

print("Here is your final playlist!")
playlist = get_final_playlist() # Calculates and displays the final playlist, and saves to a variable for if the user wants to save the playlist to Spotify

print()
# Option for exporting the playlist to Spotify
create_new_playlist_input = input("Would you like to save this playlist to Spotify? Enter y for yes and n for no: ")
if create_new_playlist_input == 'y':
    create_new_playlist(playlist) # Create a new playlist with the top 30 displayed in this app
else:
    print("Thanks for using the Spotify playlist generator!")