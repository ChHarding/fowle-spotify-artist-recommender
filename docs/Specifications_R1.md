NOTE: Changes from the original document are either ~~crossed out~~ for deletions or <span style="color:green">green</span> for insertions.

# General description of the project

The purpose of this application will be to help users build a playlist on Spotify based on listening habits and responses to a series of questions asked in a user interface. This project is inspired by work I’ve done in a previous semester researching Spotify’s personalization algorithm. I discovered that Spotify users are unclear on how the algorithm works and wish to exert more control over it to narrow in on certain genres, themes, etc. This project will use the Spotify API and Spotipy Python library to get a user’s listening preferences, then will refine and augment the list progressively using responses to a series of questions. The “flow” of the application will resemble something like a Buzzfeed quiz, where all the heavy computation happens on the backend, and the user simply needs to answer a series of questions in a clean and simple interface. The final result will be a playlist of 30 songs, which the user can save as a new playlist in Spotify.

This project will utilize the following APIs, libraries, and modules:

- The **[Spotipy](https://spotipy.readthedocs.io/en/2.24.0/)** library. The methods within this library will provide quick and easy access to users’ listening habits including top artists and genres. I might use the **recommendations()** method to stem out to recommended artists if the user wants to discover new music, though that might undermine the purpose of this project (making recommendations understandable and manipulatable).
- The **[Spotify Web API](https://developer.spotify.com/documentation/web-api)**, accessed through the **requests** module in Python. ~~There are certain properties in the API that don’t have corresponding methods in the Spotipy library, such as **accousticness** or **dancability**, which would nicely map to questions in the interface to filter the list of tracks.~~ <span style="color:green">Spotipy handles all interactions with the web API, including audio features.</span>
- **[Flask](https://flask.palletsprojects.com/en/3.0.x/)** for the user interface. I plan to build this as a web application. I still need to investigate which Flask frontends will work best for my purposes. Version 1 will be a CLI application to prove the concept and focus on getting the backend working properly.
- ~~I am on the lookout for a math library that will help me compute normalized scores for tracks (more on that below).~~

# Task vignettes

1. **Sam wants to use the program to help him decide what familiar music he wants to listen to**. Sam opens the application in a browser and authenticates with Spotify. The first question asks whether Sam wants to listen to familiar or new (novel, for Sam) music. Sam selects the option to listen to familiar music. Next, he is asked to select which genre(s) he is in the mood for, based on genres he frequently listens to. Sam is then asked a few questions on song qualities such as whether he is seeking music with high or low danceability, whether he is looking for instrumental or vocalized music, etc. Finally, Sam is presented with a generated playlist that includes 30 songs that he’s familiar with. Sam can then give the playlist a name and export it to Spotify for later listening.
2. **Jessica wants to use the program to help her find new artists to listen to**. Jessica opens the application in a browser and authenticates with Spotify. The first question asks whether Jessica wants to listen to familiar or new (novel, for Jessica) music. Jessica selects the option to listen to new music. Next, she is asked to select which genre(s) she is in the mood for, which includes a list of genres she already likes along with genres she doesn’t listen to often. Jessica is then asked a few questions on song qualities such as whether she is seeking music with high or low danceability, whether she is looking for instrumental or vocalized music, etc. Jessica is presented with a generated playlist that includes 30 songs that are new to her. Jessica can then give the playlist a name and export it to Spotify for later listening.

# Technical flow

### Authentication and general information

- Authentication will be done using the Authorization Code Flow, available **[here](https://spotipy.readthedocs.io/en/2.24.0/#authorization-code-flow)**.
- In the user’s default browser <span style="color:green">on localhost port 4000</span>, they will authenticate with Spotify using their ID and password. They will be sent to a redirect URI, which will feed back to the application to verify the user’s authorization.
- Most of the app will use the “**user-top-read**” scope, which will prevent any accidental changes, insertions, or deletions. If the user chooses to save their recommendations to a new playlist in Spotify, the scope will expand to include “**playlist-modify-public**”, which will allow the backend to utilize the **user_playlist_create** method to create a new playlist and populate it with the **playlist_add_items** method from Spotipy.

### Initial dataset

- **def ~~masterlist = get_top_500_tracks():~~ <span style="color:green">track_list = get_top_tracks(offset)</span>**
  - This function would fire after authentication and create a massive list of the users’ top 500 tracks of all time. It would use the **current_user_top_tracks** method to get 50 top tracks at a time, firing 10 times <span style="color:green">controlled by the **offset** argument</span>. This is necessary because the **current_user_top_tracks** method has a limit of only 50 tracks. Thus, using the **offset** flag, it will need to be done 10 times to construct the full list of 500. <span style="color:green">This also assigns an initial track score of 100 to each track for later calculations.</span> If there is not enough data for 500 tracks (for example, if it’s a new Spotify user without enough historical listening data), ~~the loop will break at that point~~ <span style="color:green">the program will present a friendly error that the user should try again after a few weeks of using Spotify. Returns the initial **track_list**.</span>
- <span style="color:green">**def get_new_tracks(track_list)**</span>
  - <span style="color:green">This uses the **sp.recommendations()** Spotipy method to get a new list of 250 songs to replace **track_list**. Returns the modified **track_list**.</span>
- <span style="color:green">**def set_novel_track_list(ids)**</span>
  - <span style="color:green">This is invoked in get_audio_features() and accepts a list of new track IDs. It uses these IDs to return 50 new tracks at a time in a new list called **new_tracks**, which **get_audio_features() .extends**() into the updated **track_list**.</span>
- <span style="color:green">**def get_audio_features(track_list)**</span>
  - <span style="color:green">This will get and set the audio features for each track. It includes error handling for if one or all audio features are missing, and will flag a track as missing audio features if so. Returns an updated **track_list**.</span>

### Do you want to listen to familiar music or new music?

- The user will be prompted with this question first in the interface. If the user selects “Familiar music”, **track_list** will be retained.
- If the user selects “New music”, a series of actions will occur behind the scenes:
  - **track_list** will be iterated over with the **sp.recommendations()** method. This method only accepts 5 “seed” values, which will be used as arguments for the **sp.recommendations()** method. For this, I will take the top 250 of **track_list** and iterate over it ~~20~~ <span style="color:green">50</span> times with **recommendations(seed_tracks=\[5 tracks at a time, paginated from the top 250 tracks on masterlist\], limit=5)**. ~~Each iteration will return 5 tracks, add them to a **novel_masterlist**, resulting in 500 new tracks (5 tracks of the top 100 turn into 25 recommended tracks, done 20 times). A function will then loop over **novel_masterlist** to remove duplicates. This function will also compare **novel_masterlist** with **masterlist** and remove any duplicates there, as well. Finally, all tracks in **novel_masterlist** will be assigned an initial score of 100, using a function similar to **tracklist_with_scores()**.~~ <span style="color:green">An updated **track_list** with new tracks will be used for the remainder of the program runtime.</span>
- If the user selected “Familiar music,” the original **track_list** will be retained for the remainder of the program. ~~If the user selected “New music,” **novel_masterlist_scored** will be used for the remainder of the program.~~
- <span style="color:green">**get_audio_features()** fires to set the audio features for each track for later calculations.**</span>

### Selecting genres

- <span style="color:green">**def set_artist_genres(track_list):**</span>
  - <span style="color:green">This function gets the genre(s) of the artists that produced each track as a list and set this list to the value of each track object's **genres** property. Returns an updated **track_list**.</span>
- <span style="color:green">**def create_genres_dict(track_list):**</span>
  - <span style="color:green">This function takes the track_list and extracts all genres from all tracks as unique values in a dictionary. For each item in the dictionary, the key is an index value from 0 to X, and the value is a unique genre. NOTE: The dictionary is a temporary solution for the CLI version of the app, so that the user only needs to enter a number associated with the genre rather than the name of the genre itself, which can be long and introduce error. The function returns the genres dictionary.</span>
- <span style="color:green">**def genre_score_deduction(genre_input):**</span>
  - <span style="color:green">After the user inputs what genre(s) they want to listen to, this function accepts that input, turns it into a list (if there were multiple entries), and deduces 20 points from the **score** property of each track if the genre(s) of that track do not match what the user requested. This function currently returns nothing, since modifications to **track_list** happen in-place.</span>

### Setting desired track features

- Each track in Spotify has a set of audio features to describe the type of music: **acousticness**, **danceability**, **energy**, **instrumentalness**, **liveness**, **speechiness**, and **valence**. Additional information about each of these can be found **[here](https://developer.spotify.com/documentation/web-api/reference/get-audio-features)**. Each value is a floating point number between 0.0 and 1.0, where higher values indicate a greater match (e.g., track A is more “danceable” than track B if track A’s danceability value is 0.0075 and B’s danceability value is 0.0005).
- Using a UI slider component for each track feature (i.e., 7 sliders), the user will select a value between 0 and 100. <span style="color:green">Version 1, as a CLI, does not support sliders, and instead asks for manual user entry.</span>
- <span style="color:green">**def feature_score_deduction(input_value, feature):**</span>
  - <span style="color:green">This function fires for each of the 7 features, and accepts the numeric user input and the name of the feature as arguments. Each time it runs, it performs a calculation that determines how many points from the track's **score** property need to be deduced based on the delta between that track's audio feature score and the user's **input_value**. This function currently returns nothing, since modifications to **track_list** happen in-place.</span>

### Finalizing the list

- **def get_final_playlist(track_list)**
  - This final function will sort the list of tracks along the score value, high to low. It will then pull the top 30 tracks, randomize the order, ~~push to final_playlist~~ <span style="color:green">present the final playlist, and return the **top_30_tracks**.</span>
  - I think it would be smart to randomize the order because, if the best songs were always at the top, the user might get tired of the playlist when listening through it and might notice the diminishing quality.
- ~~A function will be used to render the tracks into the UI, displaying details such as the track name, artist, album, album art, and track length. It will look something like Spotify’s playlists in the interface.~~
- A button will be available for the user to export the playlist to Spotify. When clicked, the interface will prompt for a playlist name. Then, a function will fire that makes use of the **user_playlist_create** method to create the playlist with the provided name, and the **playlist_add_items** method to populate the playlist with the 30 tracks, in the same order.

This completes the workflow. 🤘

# Self assessment - Retained from first version of this document

The most unexpected change I made was shifting from providing artist recommendations to track recommendations. I really wanted to use the track features (e.g., danceability), but those features only exist at the track level, not the artist level. Thus, I would have needed to get the top tracks for each artist and perform calculations on those tracks for each artist to come up with a score for the artist, which felt unfair since many artists span many genres and styles of music. Also, the amount of additional effort to do that would be a bit insane for the amount of time I have to work on this project. Ultimately, I like the idea of creating a playlist more, since the individual songs are more likely to be a closer fit to the user input, and the user could always explore artists on the playlist if they’re feeling adventurous.

I also realized halfway through writing this that it might be worth retaining masterlist as is, but extract just the song ID for masterlist_scored. That way, I’m only working with a simple (but long) dictionary rather than a not-quite JSON object with a lot more data than I need for this application. Ultimately, I’m wondering if I should skip using Spotipy altogether, since it doesn’t have the song features and I’ll need to query each track ID against Spotify’s vanilla API anyway to perform those calculations.

I feel medium confident that I’ll be able to do all this. Conceptually, it seems doable, but I know I’ll hit roadblocks and unforeseen issues that will take up most of my time as I work on this project. I’m also concerned about using Flask; I’ve never made a front-end Python application and know nothing about the toolkit. Luckily, the front end is going to be pretty simple, so I can spend more time focusing on passing data between it and my backend code.

I’ve found Microsoft’s Copilot to be incredibly helpful in generating code blocks and explaining how they work. I feel comfortable using the debugger. I can’t think of anything that seems impossible at this point, but I plan to reach out to the instructor for advise on cleaning up/simplifying code (and, of course, for help when Copilot, Google, and the debugger fail me).