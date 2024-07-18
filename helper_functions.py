import random






# [---------------------------------------------------------------]
# [-----------------------PROGRAM FUNCTIONS-----------------------]
# [---------------------------------------------------------------]






def get_top_tracks(offset, sp):
    '''
    Gets the current user's top tracks. Each track is a dictionary object with several parameters
    for later use in the program, such as track_name and artists. 

    Args:
        offset: The value to specify the offset for the current_user_top_tracks Spotipy method.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        A list of 50 track objects.
    '''

    # Saves the response from current_user_top_tracks
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='long_term', offset=offset)

    # Loop parses all track data needed for the program from the response into a track object
    # Each object is stored in new_tracks, which is returned and .extended() into track_list 
    # in main.py new_or_familiar_page()
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
    '''
    Gets and sets the audio features for each track in track_list using Spotipy's 
    audio_features method.

    Args:
        track_list: The track_list object from the Flask session.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        track_list, updated with the audio features set on each track.
    '''

    # Get track_ids for all tracks in track_list for easier lookup
    track_ids = []
    for track in track_list:
        track_ids.append(track['track_id'])

    # sp.audio_features has an upper limit of 100 track ids it can accept. This block uses an iterator, 
    # remainder, and offset to loop through all tracks in track_list (which can have up to 500 tracks)
    iterations = len(track_list) // 100
    remainder = len(track_list) % 100
    if remainder > 0:
        iterations += 1
    offset = 0
    for i in range(iterations):

        # Instantiate audio_features_list to get all audio features for the current group of 100 or
        # less tracks
        audio_features_list = []

        # Try/except block needed for the final iteration in this loop, which can have a variable
        # number. Needed to do this to prevent an error when getting the final index of track_ids
        try:
            audio_features_list = sp.audio_features(tracks=track_ids[offset:offset+100])
        except:
            audio_features_list = sp.audio_features(tracks=track_ids[offset:])
        
        # Loop to set the audio features for each value if the feature exists, else None
        for track_audio in audio_features_list:
            if track_audio != None:

                # Look for a match in the current track_list
                for main_track in track_list:

                    # For each audio feature, set the value. If it does not exist (None), change the missing 
                    # features flag to True for later handling (not currently used in the program)
                    if track_audio['id'] == main_track['track_id']:
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
    '''
    Gets track objects from 50 supplied track_ids (parameter = ids). Parses all track information
    into new track objects, similar to get_top_tracks.

    Args:
        ids: The Spotify IDs of 50 songs.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        A list of 50 track objects to be extended into a new track_list.
    '''


    # sp.tracks only accepts up to 50 track IDs, so this needs to loop in get_new_tracks if there are 
    # more than 50 available tracks
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
        new_tracks.append(track_object)

    return new_tracks




def get_new_tracks(track_list, sp):
    '''
    Gets new tracks to replace track_list in the Flask session. This is invoked when users select
    the "New" button on newOrFamiliar.html. 

    Args:
        track_list: The track_list object from the Flask session.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        track_list, updated with all new tracks.
    '''

    # Get IDs for all familiar tracks from initial values of track_list for later comparison
    familiar_track_ids = []
    for track in track_list:

        # Create a lightweight list of just the track_ids
        familiar_track_ids.append(track['track_id']) 

    # Instantiate list to collect track ids of recommended tracks
    new_track_ids = []

    familiar_track_counter = 0

    # Loops over the entire track_list (500 tracks) 50 times in 5-item increments. This is so that 
    # each track in the top 100 is fed to sp.recommendations to get new tracks. This results in a list 
    # of 500 new tracks to replace the "familiar" track_list.
    for familiar_track_group in range(100):

        # Gets sp.recommendations for familiar tracks in track_list n through n+5
        recommended_tracks = sp.recommendations(seed_tracks=familiar_track_ids[familiar_track_counter:familiar_track_counter+5], limit=5)

        for recommended_track in recommended_tracks['tracks']:
            
            # Adds the track ID to the new list
            new_track_ids.append(recommended_track['id'])

        # Increments so that the loop uses the next 5 familiar tracks in track_list for new recommendations
        familiar_track_counter += 5

    # Checks if new_track_ids exist in familiar_track_ids; removes duplicates and builds a new list of ids
    # This is so that the user truly finds new music using the app. The sp.recommendations method doesn't 
    # necessarily return new music.
    actually_new_track_ids = [id for id in new_track_ids if id not in familiar_track_ids]
    
    # Converts to a set, then back to a list to remove duplicates within itself, incase recommendations overlapped
    cleaned_new_track_ids = list(set(actually_new_track_ids)) 

    # Delete contents of track_list to make room for novel track objects
    track_list = []

    # sp.audio_features (invoked in set_novel_track_list) has an upper limit of 50 track ids it can 
    # accept. This block uses an iterator, remainder, and offset to loop through all tracks in track_list 
    # (which can have up to 500 tracks)
    iterations = len(cleaned_new_track_ids) // 50
    remainder = len(cleaned_new_track_ids) % 50
    if remainder > 0:
        iterations += 1
    offset = 0

    # For each group of 50 tracks, get the track details and .extend() into track_list
    for i in range(iterations):
        try:
            new_tracks = set_novel_track_list(cleaned_new_track_ids[offset:offset+50], sp)
            track_list.extend(new_tracks)
        except:
            new_tracks = set_novel_track_list(cleaned_new_track_ids[offset:], sp)
            track_list.extend(new_tracks)
        offset += 50

    return track_list
    

    

def set_artist_genres(track_list, sp):
    '''
    Gets and sets the genres of each track. Genres are properties of artists, not tracks. This function gets the 
    genre(s) of the artist(s) for each track and set it to track["genres"].

    Args:
        track_list: The track_list object from the Flask session.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        track_list, updated with genres.
    '''

    # Get a list of all artist uris
    artist_uris = []
    for track in track_list:
        for artist_uri in track['artist_uris']:
            artist_uris.append(artist_uri)
    
    # sp.artists has an upper limit of 50 artist_uris it can accept. This block uses an iterator, remainder, and 
    # offset to loop through all artists in artist_uris. 
    iterations = len(artist_uris) // 50
    remainder = len(artist_uris) % 50
    if remainder > 0:
        iterations += 1
    offset = 0


    for i in range(iterations):

        # Instantiate dictionary of artists, returned from sp.artists()
        artists_list = {}

        # Try/except block needed for the final iteration in this loop, which can have a variable
        # number. Needed to do this to prevent an error when getting the final index of artist_uris.
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
        offset += 50

    return track_list




def create_genres_list(track_list):
    '''
    Gets a complete list of all genres that appear in track_list.

    Args:
        track_list: The track_list object from the Flask session.

    Returns:
        genres_list: A list of all genres across all tracks in track_list.
    '''

    # Instantiate a temporary list, which is returned and saved to the global genres_dict list
    temp_genres_list = []

    # For loop saves all genres from all tracks into temp_genres_list
    for track in track_list:
        for genre in track['genres']:
            temp_genres_list.append(genre)

    # Use set() to remove duplicates
    temp_genres_set = set(temp_genres_list)

    # Convert back to a list
    genres_list = list(temp_genres_set)

    return genres_list




def genre_score_deduction(genre_input, track_list):
    '''
    Deduces the value of the "score" property on each track based on whether any of the user's requested genres 
    are in each track's "genres" list.

    Args:
        genre_input: A list of genres the user selected on genres.html
        track_list: The track_list object from the Flask session.

    Returns:
        track_list, updated with the "score" property adjusted.
    '''

    for track in track_list:

        # If any genre(s) of that track match what what the user requested, saved in genre_input, do nothing
        if any(genre in track['genres'] for genre in genre_input):
            continue

        # If there is not a match, deduce 20 points from the score
        else:
            track['score'] -= 20

    return track_list




def feature_score_deduction(input_values, track_list):
    '''
    Deduces the value of the "score" property on each track based on the delta between the rating of each feature
    on each track and the value the user submitted in features.html. For example, if a track's "danceability" rating
    is 0.023 (normalized to 23), and the user entered 87, the difference (87-23) comes to 64. Then, 64% of 10 (being
    the most points that a track could lose per feature) results in 6.4 points that are deduced from the track's
    "score" property (track["score"] -= 64*0.1).

    Args:
        input_values: The int values pulled from each range element on features.html. 
        track_list: The track_list object from the Flask session.

    Returns:
        track_list, updated with the "score" property adjusted.
    '''

    # For each track...
    for track in track_list:

        # Get one feature and user input value from input values...
        for feature_name, user_score in input_values.items():

            # Then find a match in the track properties...
            for track_property_name, track_feature_value in track.items():

                # When the match is found...
                if feature_name == track_property_name:

                    # Validate that the track feature has a value...
                    if track_feature_value != None:

                        # Then convert the user score to a float and deduce points from the track['score'] as necessary
                        user_score_float = float(user_score)
                        track_feature_value_normalized = track_feature_value * 100
                        value_difference = abs(track_feature_value_normalized - user_score_float)
                        if value_difference == 0:
                            continue
                        else:
                            dissimilarity_percentage = value_difference / 100
                            track['score'] -= 10 * dissimilarity_percentage

    return track_list




def get_album_art(top_30_tracks, sp):
    '''
    Gets and sets the album art for each track.

    Args:
        top_30_tracks: A list containing 30 track objects.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        top_30_tracks, updated with album art URLs.
    '''

    for track in top_30_tracks:
        album = sp.track(track["track_id"])
        track["album_art"] = album['album']['images'][0]['url']

    return top_30_tracks




def get_final_playlist(track_list, sp):
    '''
    Gets the final playlist of 30 tracks.

    Args:
        track_list: The track_list object from the Flask session.
        sp: The Spotipy object used for accessing Spotipy methods.

    Returns:
        top_30_tracks_with_album_art
    '''

    # Use sorted() with a lambda function to sort all list objects based on the track's score, starting
    # with the highest score
    sorted_track_list = sorted(track_list, key=lambda track: track['score'], reverse=True)

    # Instantiate list for top 30
    top_30_tracks = []

    # Returns the first 30 in the list, i.e., the 30 tracks with the highest scores
    top_30_tracks = sorted_track_list[:30] 

    # Invoke get_album_art to get and set album art on the top 30 tracks for rendering in playlist.html
    top_30_tracks_with_album_art = get_album_art(top_30_tracks, sp)

    # I'm shuffling the top 30 here to make the playlist more engaging to listen to. 
    # If the playlist was put in order from best to worst, it would get less enjoyable to listen to as the 
    # user progresses through it.
    random.shuffle(top_30_tracks)

    return top_30_tracks_with_album_art




def create_new_playlist(playlist, sp, playlist_name):
    '''
    Creates the new playlist in Spotify. Spotipy does this with the user_playlist_create() method to create
    the playlist, and user_playlist_add_tracks to populate it. 

    Args:
        playlist: The top_30_tracks dictionary from the Flask session.
        sp: The Spotipy object used for accessing Spotipy methods.
        playlist_name: A string containing the name the user wants for their new Spotify playlist.

    Returns:
        True: if the playlist creation worked successfully.
        False: if the playlist creation didn't work.
    '''

    # Get the current user so Spotify knows who created the new playlist
    current_user = sp.current_user()
    user_id = current_user['id']

    # Try to create a new playlist with the given name
    try:

        # Create a new playlist with the given name
        new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name)

         # Get the new playlist's ID for populating it with the tracks in var playlist
        new_playlist_id = new_playlist['id']

        # Create a new simple list for collecting track URIs, which are needed to populate the playlist
        playlist_uris = [] 

        for track in playlist:
            playlist_uris.append(track['track_uri'])

        # Add the top tracks to the new playlist
        sp.user_playlist_add_tracks(user=user_id, playlist_id=new_playlist_id, tracks=playlist_uris)
        
        return True
    
    # If anything went wrong while creating the playlist
    # Future drafts of this app will offer more explicit error messaging
    except: 

        return False