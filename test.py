from track2peer import Track2Peer

tp = Track2Peer()
query = raw_input("Please enter song or artist name: ")
tp.search_n_play(query)

raw_input('Enter something to stop playback')