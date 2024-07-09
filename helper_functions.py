import spotipy
import random

# [---------------------------------------------------------------]
# [-----------------------PROGRAM FUNCTIONS-----------------------]
# [---------------------------------------------------------------]


def get_top_tracks(offset, sp):
    '''Gets the current signed in users' top tracks. Fires after the user signs in.
    Parameters: offset - the starting value for getting top tracks. E.g, an offset of 50 gets the 50th-100th top tracks.'''
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term', offset=offset)
    # Loop parses all track data needed for the program from the response into a track object
    # Each object is stored in new_tracks, which is returned and .extended() into track_list
    new_tracks = []
    for track in top_tracks['items']:
        track_object = {
            'track_id': track['id'],
            'track_uri': track['uri'],
            'artists': [artist['name'] for artist in track['artists']],
            'artist_uris': [artist['uri'] for artist in track['artists']],
            'track_name': track['name'],
            'album_name': track['album']['name'],
            'genres': [],
            'acousticness': 1.0,
            'danceability': 1.0,
            'energy': 1.0,
            'instrumentalness': 1.0,
            'liveness': 1.0,
            'speechiness': 1.0,
            'valence': 1.0,
            'score': 100.00,
            'missing_audio_features': False
        }
        new_tracks.append(track_object)
    return new_tracks




def get_audio_features(track_list, sp):
    '''Gets the audio features of each track in track_list.
    Modifies missing_audio_features flag to True if any or all audio features are missing on the track.
    Parameters: track_list - the current list of all tracks.
    Returns: an updated track_list'''

    # Get track_ids for all tracks in track_list for easier lookup
    track_ids = []
    for track in track_list:
        track_ids.append(track['track_id'])
    iterations = len(track_list) // 100 # sp.audio_features has an upper limit of 100 track ids
    remainder = len(track_list) % 100
    # Adds 1 to the number of iterations if the length of track_list is not perfectly divisible by 100
    if remainder > 0:
        iterations += 1
    offset = 0
    for i in range(iterations):
        audio_features_list = [] # Instantiate the list of audio features for the current group of tracks
        try: # For when there are exactly 100 available before the end of the list is reached
            audio_features_list = sp.audio_features(tracks=track_ids[offset:offset+100])
        except: # For the end of the list if it is not divisible by 100
            audio_features_list = sp.audio_features(tracks=track_ids[offset:])
        for track_audio in audio_features_list:
            # If there are any audio features available for this track...
            if track_audio != None:
                # Look for a match in the current track_list
                for main_track in track_list:
                    if track_audio['id'] == main_track['track_id']:
                        # For each audio feature, set the value. If it does not exist (None), change the missing features flag to True for later handling
                        if track_audio['acousticness'] != None:
                            main_track['acousticness'] = track_audio['acousticness']
                        else:
                            main_track['missing_audio_features'] = True
                        if track_audio['danceability'] != None:
                            main_track['danceability'] = track_audio['danceability']
                        else:
                            main_track['missing_audio_features'] = True
                        if track_audio['energy'] != None:
                            main_track['energy'] = track_audio['energy']
                        else:
                            main_track['missing_audio_features'] = True
                        if track_audio['instrumentalness'] != None:
                            main_track['instrumentalness'] = track_audio['instrumentalness']
                        else:
                            main_track['missing_audio_features'] = True
                        if track_audio['liveness'] != None:
                            main_track['liveness'] = track_audio['liveness']
                        else:
                            main_track['missing_audio_features'] = True
                        if track_audio['speechiness'] != None:
                            main_track['speechiness'] = track_audio['speechiness']
                        else:
                            main_track['missing_audio_features'] = True
                        if track_audio['valence'] != None:
                            main_track['valence'] = track_audio['valence']
                        else:
                            main_track['missing_audio_features'] = True
        offset += 100
    return track_list




def set_novel_track_list(ids, sp):
    '''Gets tracks details from get_new_tracks and returns a list of new track objects.
    Parameters: ids - a list of track IDs.
    Returns: a list of new track objects to .extend() into track_list'''

    # sp.tracks only accepts up to 50 track IDs, so this needs to loop in get_new_tracks if there are more than 50 available tracks
    tracks_results = sp.tracks(ids)
    new_tracks = []
    for track in tracks_results['tracks']:
        track_object = {
            'track_id': track['id'],
            'track_uri': track['uri'],
            'artists': [artist['name'] for artist in track['artists']],
            'artist_uris': [artist['uri'] for artist in track['artists']],
            'track_name': track['name'],
            'album_name': track['album']['name'],
            'genres': [],
            'acousticness': 1.0,
            'danceability': 1.0,
            'energy': 1.0,
            'instrumentalness': 1.0,
            'liveness': 1.0,
            'speechiness': 1.0,
            'valence': 1.0,
            'score': 100.00,
            'missing_audio_features': False
        }
        # Writes each new track object to the newly scrubbed track_list
        new_tracks.append(track_object)
    return new_tracks




def get_new_tracks(track_list, sp):
    '''Get unfamiliar (new, novel) track IDs using the sp.recommendations() method on the current track_list of a user's top tracks.
    Calls set_novel_track_list() to get track details from track IDs.
    Parameters: track_list
    Returns: track_list => updated with new tracks'''

    # Get IDs for all familiar tracks from initial values of track_list for later comparison
    familiar_track_ids = []
    for track in track_list:
        familiar_track_ids.append(track['track_id']) # Creates a lightweight list of just the track_ids

    # Instantiate list to collect track ids of recommended tracks
    new_track_ids = []

    familiar_track_counter = 0

    # Loops over top 100 tracks 20 times in 5-item increments. This is so that each track in the top 100 is fed to sp.recommendations
    for familiar_track_group in range(50):
        # Gets sp.recommendations for familiar tracks in track_list n through n+5
        recommended_tracks = sp.recommendations(seed_tracks=familiar_track_ids[familiar_track_counter:familiar_track_counter+5], limit=5)

        for recommended_track in recommended_tracks['tracks']:
            # Adds the track ID to the new list
            new_track_ids.append(recommended_track['id'])

        # Increments so that the loop uses the next 5 familiar tracks in track_list for new recommendations
        familiar_track_counter += 5

    # Checks if new_track_ids exist in familiar_track_ids; removes duplicates and builds a new list of ids
    # This is so that the user truly finds new music using the app. The sp.recommendations method doesn't necessarily return new music.
    actually_new_track_ids = [id for id in new_track_ids if id not in familiar_track_ids]
    cleaned_new_track_ids = list(set(actually_new_track_ids)) # Converts to a set, then back to a list to remove duplicates within itself, incase recommendations overlapped

    # Delete contents of track_list to make room for novel track objects
    track_list = []

    # Get the number of times the length of cleaned_new_track_ids can be iterated over in blocks of 50
    iterations = len(cleaned_new_track_ids) // 50 # sp.tracks has an upper limit of 50 track ids
    remainder = len(cleaned_new_track_ids) % 50
    # Adds 1 to the number of iterations if the length of track_list is not perfectly divisible by 50
    if remainder > 0:
        iterations += 1
    offset = 0
    # For each group of 50 tracks, get the track details and .extend() into track_list
    for i in range(iterations):
        try:
            new_tracks = set_novel_track_list(cleaned_new_track_ids[offset:offset+50])
            track_list.extend(new_tracks)
        except:
            new_tracks = set_novel_track_list(cleaned_new_track_ids[offset:])
            track_list.extend(new_tracks)
        offset += 50
    return track_list
    

    

def set_artist_genres(track_list, sp):
    '''Sets the genres for each track.
    Genres are properties of artists, not tracks. 
    Thus, this pulls the genres of the artists of each track and appends those genres to the genres property of each track object.
    Parameters: track_list
    Returns: track_list, updated with genres'''

    # Get a list of all artist uris
    artist_uris = []
    for track in track_list:
        for artist_uri in track['artist_uris']:
            artist_uris.append(artist_uri)
    
    # Calculate number of loops
    iterations = len(artist_uris) // 50 # sp.artists has an upper limit of 50 track ids
    remainder = len(artist_uris) % 50
    # Adds 1 to the number of iterations if the length of track_list is not perfectly divisible by 50
    if remainder > 0:
        iterations += 1
    offset = 0
    for i in range(iterations):

        # Instantiate dictionary of artists, returned from sp.artists()
        artists_list = {}

        # Get results for 50 at a time, or the remainder if the length of artist URIs is not perfectly divisible by 50
        try:
            artists_list = sp.artists(artist_uris[offset:offset+50])
        except:
            artists_list = sp.artists(artist_uris[offset:])

        # For each artist...
        for artist in artists_list['artists']:
            # Compare to each track object in track_list...
            for track_object in track_list:
                # Then further look for a match in the list of artist_uris...
                for track_object_uri in track_object['artist_uris']:
                    if artist['uri'] == track_object_uri:
                        # Add the genres from sp.artists() artist data to the track_list object genres property
                        track_object['genres'].extend(artist['genres'])
                        # Remove duplicate genres, for if one artist appears in multiple tracks in track_list
                        track_object_genres_set = set(track_object['genres'])
                        track_object['genres'] = list(track_object_genres_set)
        
        # Increment the loop
        offset += 50

    return track_list




def create_genres_dict(track_list):
    '''Creates a dictionary containing all genres. Each genre is paired with an indexed key for user entry.
    Parameters: track_list
    Returns: temp_genres_dict (List)'''
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




def genre_score_deduction(genre_input, genres_dict):
    '''Deduces each track object's score if the user's genre input does not match any genre of each track.
    Parameters: genre_input => the genres the user selected in the main application
    Returns: None => score adjustments happen in-place'''

    input_list = genre_input.split(' ') # Turns user string input of genre keys into a list
    # This compares the user input to the KEYS of genres_dict to retrieve the values. 
    # I opted to use this method so that the user simply needed to enter the numeric key instead of type out the 
    # genre name, which can get long and complicated and introduce more room for error.
    input_genres_list = [genres_dict[int(key)] for key in input_list] 
    # For each track...
    for track in track_list:
        # If any genre of that track matches what the user put in...
        if any(genre in track['genres'] for genre in input_genres_list):
            continue # ...do nothing (retain a higher score)
        else:
            track['score'] -= 20 # ...if there is NOT a match, deduce 20 points from the score




def feature_score_deduction(input_value, feature):
    '''Deduce each track's score based on the difference between each audio_feature and the audio_feature score provided by the user.
    Parameters: input_value => the value the user provided for the audio_feature. feature => the name of the feature, e.g., 'acousticness'.
    Returns: None => score adjustments happen in-place'''

    for track in track_list:
        track_feature_value = track[feature]
        # This gets a positive value for the difference between what the user submitted and the value of the feature on the track
        value_difference = abs(track_feature_value - input_value)
        if value_difference == 0: # If there is a perfect match...
            continue # ...do nothing (deduce 0 points)
        else: # If there is a difference in score and user input
            dissimilarity_percentage = value_difference / 100 # Get a "dissimilarity percentage"...
            track['score'] -= 12 * dissimilarity_percentage # Normalize the dissimilarity to a maximum value of 12 points to deduce, then subtract those points from the track's score
        



def get_final_playlist(track_list):
    '''Gets the final playlist displays it in the UI.
    Parameters: track_list
    Returns: top_30_tracks => List of tracks with the highest scores'''

    # Use sorted() with a lambda function to sort all list objects based on the track's score, starting with the highest score
    sorted_track_list = sorted(track_list, key=lambda track: track['score'], reverse=True)

    # Instantiate list for top 30
    top_30_tracks = []

    top_30_tracks = sorted_track_list[:30] # Returns the first 30 in the list, i.e., the 30 tracks with the highest scores

    # I'm shuffling the top 30 here to make the playlist more engaging to listen to. 
    # If the playlist was put in order from best to worst, it would get less enjoyable to listen to as the user progresses through it.
    random.shuffle(top_30_tracks)

    # Playlist output
    for idx, track in enumerate(top_30_tracks):
        print(f"{idx + 1}: {track['track_name']} - {', '.join(track['artists'])}\t Match: {round(track['score'], 2)}%")
    return top_30_tracks




def create_new_playlist(playlist, sp):
    '''Attempts to create a new public user playlist in Spotify with the 30 tracks recommended in this program.
    Parameter: playlist => List of the top 30 tracks
    Returns: None, end of the process'''

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





