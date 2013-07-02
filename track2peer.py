from outsearch import OutSearch
from player import TorrentPlayer
import sys,time
import thread

class Track2Peer(object):
    
    _tp = None
    _os = None
    def search_n_play(self, query):
        self._os = OutSearch()
        torrent = self._os.searchCoarse(query) #torrent item instance
        self._tp = TorrentPlayer()
        self._tp.load_torrent_item(torrent)
        
        subfiles = torrent.files
        for v in subfiles:
            print v.subfile_no, ' ', v.title

        sf = int(raw_input("Please enter subfile number: "))

        self._tp.select_file(sf)
        thread.start_new_thread(self._tp.play,())
        self.display_play_progress()

    def display_play_progress(self):
        while True:
            print repr(round(self._tp.get_download_progress()*100)).rjust(6),"% is ready ",
            sys.stdout.flush()
            time.sleep(1)
            print "\r",
            if (self._tp.get_download_progress()>=1): 
                print "File is ready               "
                break
            pass

def run():
    track2peer.Track2Peer().search_n_play("Track name")