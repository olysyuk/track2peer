import libtorrent as lt
import logging
import time
import os
import sys
import pprint
from subprocess import *
import thread
from player import Player

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
    _torrentFile = None
    _info = None
    _selectedFile = None
    _ses = None #torrent session
    _h = None #torrent file handler
    _play_thread = None
    _download_progress = -1

    max_download_pieces=10

    def load_torrent(self, filepath):
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
        self._ses = lt.session()
        self._ses.listen_on(6881, 6891)
        self._h = self._ses.add_torrent({'ti': self._info, 'save_path': './data'})
        self.init_piece_priority()
        
        outputcmd = 'mplayer -really-quiet -nolirc -cache 1024 -'   
        stream_writer = TorrentPlayerBackgroundStream(outputcmd, self._ses, self._h, self.get_file_piece_range(), self.get_file_piece_offset())
        thread.start_new_thread(stream_writer.write_stream,())

        while (not self._h.status().is_finished):
            self.update_progress()
            self.update_piece_priority()
            time.sleep(1)
        self.update_progress()

    def init_piece_priority(self): 
        """Defines initial piece priority to star download selected file"""
        #all pieces download is disabled
        for i in range(self._info.num_pieces()):
            self._h.piece_priority(i,0)

        #enabling only first iteration pieces for selected file
        pieces = self.get_file_piece_range()
        pieces = (pieces[0], min(pieces[0]+self.max_download_pieces, pieces[1]))
        for i in range(*pieces):
            self._h.piece_priority(i,1)
        #logger.debug('Starging download of pieces %d..%d',pieces[0],pieces[1])

    def update_piece_priority(self):
        """Updates downloading queue accordingly to selected file """
        h = self._h
        file_pieces = self.get_file_piece_range()

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
        file_pieces = self.get_file_piece_range()
        ready = 0
        for i in range(*file_pieces):
            if (s.pieces[i]):
                ready = ready + 1
        self._download_progress = 1.0 if (s.is_finished or s.is_seeding) else ready * 1.0 / (file_pieces[1] - 1 - file_pieces[0])

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


class TorrentPlayerBackgroundStream:
    _h = None
    _ses = None
    _outputcmd = None
    _pieces = None #tuple start,end piece
    _offsets = None #tuple offset on start and end piece
 
    def __init__(self, outputcmd, torrent_session, torrent_handle, pieces, offsets):
        self._outputcmd = outputcmd
        self._ses = torrent_session
        self._h = torrent_handle

        self._pieces = pieces
        self._offsets = offsets

    def write_stream(self):
        stream = Popen(self._outputcmd.split(' '), stdin=PIPE, stdout=None, stderr=None).stdin #--not sure why this is not always working
        
        #logger.debug('Player started receiving data')
        pieces = self._pieces
        offsets = self._offsets

        #outputting piece stream to mplayer
        for piece in range(*pieces):
            #logger.debug('Writing %d of %d',piece, pieces[1]-pieces[0])
            buf=self.get_piece(piece)
            if piece==pieces[0]:
                buf = buf[offsets[0]:]
            if piece==pieces[1]:
                buf = buf[:offsets[1]]
       
            try:
                stream.write(buf)
            except Exception, err:
                exit(0)

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