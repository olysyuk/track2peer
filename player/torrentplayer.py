import libtorrent as lt
import logging
import time
import os
import sys
import pprint
from subprocess import *
import thread
from Queue import Queue
from player import Player
import tempfile

""" from torrentplayer import *

    tp = new TorrentPlayer()
    tp.load_torrent('example.torrent')
    tp.get_files_list() #returns list of get_files
    tp.select_file(i) #set file that would be played
    tp.play()
"""
class TorrentPlayer(Player):
    def __init__(self):
        pass

    def __del__(self):
        self._playQ.put(TorrentPlayerBackgroundStream.MESSAGE_DIE)
        self._downloadQ.put(TorrentPlayerDownloadManager.MESSAGE_DIE)
        self._player.destroy()
        del self._download_manager

    _downloadQ = Queue() #Queue that forwards control messages to download process
    _playQ = Queue() #Queue that forwards controll messages for play process
    _download_manager = None #Object that processes download
    _player = None #Object that processes background stream


    _torrentFile = None
    _info = None
    _selectedFile = None
    _ses = None #torrent session
    _session_started = False

    _h = None #torrent file handler

    def load_mli(self, mli):
        if (mli.magnet):
            self.start_session()
            self._h = lt.add_magnet_uri(self._ses, mli.magnet, {'save_path':self.get_save_path()})

            print 'downloading metadata...'
            while (not self._h.has_metadata()): time.sleep(1)
            self._info = self._h.get_torrent_info();
            print 'metadata done...'
        else:
            self.log_filepath(mli.torrent)

    def load_filepath(self, filepath):
        try:
            filepath = os.getcwd()+"/"+filepath
            with open(filepath): pass
            self._torrentFile = filepath
            self._info = lt.torrent_info(self._torrentFile)
            logger.debug('Loaded torrent file: '+filepath);
        except IOError:
            raise Exception(filepath + " file doesn't exist")

    def get_files_list(self):
        names = []
        for f in self._info.files():
            names.append(f.path)
        return names

    def select_file(self, i):
        """Select file number to download in future """
        files = self._info.files()
        f = files[i]
        logger.debug('Selected file: "%s" with size %d MB',f.path, f.size/1024/1024)
        self._selectedFile = f

    def play(self):
        """Starts file download and playback"""
        if (self._player): #We are allready playing
            self._playQ.put(TorrentPlayerBackgroundStream.MESSAGE_PLAY)
            return

        self.start_session()
        if (not self._h): #If we added torrent by magnet it's allready here. Should do it more gently in future
            self._h = self._ses.add_torrent({'ti': self._info, 'save_path': self.get_save_path() })

        #Enabling download manager
        self._download_manager = TorrentPlayerDownloadManager(self._downloadQ, self._ses, self._h, self.get_file_piece_range())
        self._download_manager.init_piece_priority()

        self.start_play_thread()
        self.start_download_thread()

    def pause(self):
        self._playQ.put(TorrentPlayerBackgroundStream.MESSAGE_PAUSE)

    def stop(self):
        self._playQ.put(TorrentPlayerBackgroundStream.MESSAGE_STOP)

    def get_download_progress(self):
        return self._download_manager.download_progress if self._download_manager else -1

    def get_play_progress(self):
        return self._player.play_progress

    def start_play_thread(self):
        self._player = TorrentPlayerBackgroundStream(self._playQ, self._ses, self._h, self.get_file_piece_range(), self.get_file_piece_offset())
        thread.start_new_thread(self._player.run,())

        self._playQ.put(TorrentPlayerBackgroundStream.MESSAGE_PLAY)

    def start_download_thread(self):
        thread.start_new_thread(self._download_manager.run,())

    def start_session(self):
        if (self._session_started): return
        self._ses = lt.session()
        self._ses.listen_on(6881, 6891)
        self._session_started = True

    def get_save_path(self):
        return './data'

    def get_file_piece_range(self):
        """Returns start and end pieces of file that is selected to play"""
        file = self._selectedFile
        piece_length = self._info.piece_length()
        return (file.offset/piece_length, (file.offset+file.size)/piece_length+1)

    def get_file_piece_offset(self):
        """Returns offset on start piece and offset on end piece"""
        file = self._selectedFile
        piece_length = self._info.piece_length()
        return (file.offset%piece_length, (file.offset+file.size)%piece_length)




class TorrentPlayerDownloadManager:
    """Class that does background download management."""
    MESSAGE_DIE = 1

    _mq = None #Message queue
    _h = None #Torrent handle
    _ses = None #Torrent session
    _pieces = None #Selected file pieces
    _parent = None #Parent object, on this object status will be updated
    max_download_pieces=10
    download_progress = -1

    def __init__(self, message_queue, torrent_session, torrent_handle, pieces):
        self._mq = message_queue
        self._h = torrent_handle
        self._ses = torrent_session
        self._pieces = pieces
    
    def run(self):
        while (not self._h.status().is_finished):
            time.sleep(1)
            try:
                m = self._mq.get(False)
                if (m==self.MESSAGE_DIE): break
            except: pass

            self.update_piece_priority()

            self.update_progress()
            if (self.download_progress==1): break
            
        self.update_progress()

    def init_piece_priority(self): 
        """Defines initial piece priority to star download selected file"""
        info = self._h.get_torrent_info()

        #all pieces download is disabled
        for i in range(info.num_pieces()):
            self._h.piece_priority(i,0)

        #enabling only first iteration pieces for selected file
        pieces = self._pieces
        pieces = (pieces[0], min(pieces[0]+self.max_download_pieces, pieces[1]))
        for i in range(*pieces):
            self._h.piece_priority(i,1)
        #logger.debug('Starging download of pieces %d..%d',pieces[0],pieces[1])

    def update_piece_priority(self):
        """Updates downloading queue accordingly to selected file """
        h = self._h
        file_pieces = self._pieces

        prio = h.piece_priorities()
        s = h.status()
        downloading = 0
        if len(s.pieces) == 0: return
        starting_pieces = []
        high_prio = -1

        #count pieces that are downloading  
        for piece in range(*file_pieces):
            if prio[piece] != 0 and s.pieces[piece]==False:
                downloading = downloading+1
        

        #pieceperite - pieces per iteration
        for piece in range(*file_pieces):
            if prio[piece] == 0 and downloading < self.max_download_pieces:
                starting_pieces.append(piece)
                h.piece_priority(piece,1)
                downloading = downloading+1

        #hight priority piece
        for piece in range(*file_pieces):
            if prio[piece] != 0 and s.pieces[piece]==False:
                high_prio = piece
                h.piece_priority(piece,7)
                break

        #other pieces
        if (high_prio==-1): #we have downloaded selected file 
            for piece in range(len(s.pieces)):
                h.piece_priority(piece, 1)

        #logger.debug('Download: %d active pieces, (%s) added, #%d is high prio', 
        #    downloading, ','.join(str(x) for x in starting_pieces), high_prio)

    def update_progress(self):
        """Updates track download progress, currently only ready pieces are counted"""
        s = self._h.status()
        file_pieces = self._pieces
        ready = 0
        for i in range(*file_pieces):
            if (s.pieces[i]):
                ready = ready + 1
        self.download_progress = 1.0 if (s.is_finished or s.is_seeding) else ready * 1.0 / (file_pieces[1] - 1 - file_pieces[0])




class TorrentPlayerBackgroundStream:
    """Class that does background playback management."""
    MESSAGE_PLAY = 1
    MESSAGE_PAUSE = 2
    MESSAGE_STOP = 3
    MESSAGE_DIE = 4

    _h = None
    _ses = None
    _pieces = None #tuple start,end piece
    _offsets = None #tuple offset on start and end piece

    _outputcmd = 'mplayer -slave -really-quiet -noconsolecontrols -nolirc -cache 1024 %s' #Mplayer cmd
    _stream = None #Mplayer media stream
    _media_file = None  #Media fifo file
    _command_stream=None #Commands stream for mplayer
    
    
    _mq = None
    

    _current_piece = None
    _is_playing = 0 # 1 playing , 0 -stopped
    play_progress = 0
 
    def __init__(self, message_queue, torrent_session, torrent_handle, pieces, offsets):
        self._mq = message_queue
        self._ses = torrent_session
        self._h = torrent_handle

        self._pieces = pieces
        self._offsets = offsets
        

        #Initing command fifo
        self._media_file = tempfile.mktemp()
        os.mkfifo(self._media_file)

        #executing mplayer
        outputcmd = self._outputcmd % self._media_file
        self._command_stream = Popen(outputcmd.split(' '), stdin=PIPE, stdout=None, stderr=None) #--not sure why this is not always working
        
        #attaching to media stream
        self._stream = open(self._media_file, "w", 0)
        
        #logger.debug('Player started receiving data')
        self.rewind()


    def __del__(self):
        self.destroy()

    def destroy(self):
        self._command_stream.kill()
        self._stream.close()
        
    def rewind(self,i=0):
        i = min(i, self._pieces[1]-self._pieces[0])
        self._current_piece = self._pieces[0+i]

    def get_next_piece(self):
        offsets = self._offsets
        pieces = self._pieces

        piece = self._current_piece
        if piece > self._pieces[1]: return False #We reached the end
        
        buf=self.get_piece(piece)
        
        if piece==pieces[0]:
            buf = buf[offsets[0]:]
        if piece==pieces[1]-1:
            buf = buf[:offsets[1]]
        self._current_piece = self._current_piece + 1 

        self.play_progress = (self._current_piece - self._pieces[0]) * 1.0 / (self._pieces[1] - self._pieces[0])

        return buf

    def run(self):
        thread.start_new_thread(self.player_control,())

        while True:
            if (self._is_playing):
                buf = self.get_next_piece()
                
                if buf:
                    try:
                        #logger.debug('Writing %d of %d',self._current_piece-pieces[0], pieces[1]-pieces[0])
                        self._stream.write(buf) 
                    except Exception, err:
                        exit(0)
                else:
                    break 

            time.sleep(0.1)

        self.destroy()

    def player_control(self):
        while True:
            try:
                m = self._mq.get(False)
                if (m==self.MESSAGE_DIE): break
                
                if (m==self.MESSAGE_PLAY): 
                    self._is_playing = 1
                    self._command_stream.stdin.write("pause \n")

                if (m==self.MESSAGE_PAUSE): 
                    self._is_playing = 0 if self._is_playing else 1
                    self._command_stream.stdin.write("pause \n")

                if (m==self.MESSAGE_STOP): 
                    self._is_playing = 0
                    self._command_stream.stdin.write("pause \n")
                    self.rewind()
            except: pass


    cache = {}
    def get_piece(self,i):
        """Listends while peace is ready and outputs it"""
        h = self._h
        ses = self._ses
        cache = self.cache
        if i in cache:
            ret = cache[i]
            cache[i] = 0
            return ret
        while True:
            s = h.status()
            if len(s.pieces)==0:
                break
            if s.pieces[i]==True:
                break
            time.sleep(.1)

        h.read_piece(i)
        while True:
            piece = ses.pop_alert()
            if isinstance(piece, lt.read_piece_alert):
                if piece.piece == i:
                    return piece.buffer
                else: #storing it for futher reads
                    cache[piece.piece] = piece.buffer
                break
            time.sleep(.1)



logger = logging.getLogger('TorrentPlayer')
logger.setLevel(logging.DEBUG)
if (len(logger.handlers)==0):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)