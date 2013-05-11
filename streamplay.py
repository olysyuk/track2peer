import libtorrent as lt
import logging
import time
import os
from subprocess import *

class StreamPlay(object):
    """Class that is responsible for playing stream mp3, and storing it """
    def __init__(self):
        pass
    _torrentFile = None
    _info = None
    _selectedFile = None
    _ses = None #torrent session
    _h = None #torrent file handler

    def load_torrent_file(self, filepath):
        try:
            with open(filepath): pass
            self._torrentFile = filepath
            self._info = lt.torrent_info(self._torrentFile)
            logger.debug('Loaded torrent file: '+filepath);
            logger.debug('Count of subfiles: %d', len(self._info.files()));

            self.select_file()
        except IOError:
            raise Exception(filepath + " file doesn't exist")

    def select_file(self):
        """Currently this selects first file, of list, it should be more smarter in future """
        files = self._info.files()
        f = files[0]
        logger.debug('Selected file: "%s" with size %d MB',f.path, f.size/1024/1024)
        self._selectedFile = f
        return f

    def start_download(self):
        self._ses = lt.session()
        self._ses.listen_on(6881, 6891)

        self._h = self._ses.add_torrent({'ti': self._info, 'save_path': './data'})

        #altering piece priorities for better performance
        for i in range(self._info.num_pieces()):
            self._h.piece_priority(i,1)
        
        pi = self.get_file_piece_info()
        for i in range(pi[0], pi[1]):
            self._h.piece_priority(i,7)

        while (not self._h.status().is_finished):
            print self._h.status().progress
            time.sleep(1)

        self.play_file()
        return h

    def get_file_piece_info(self):
        file = self._selectedFile
        piece_length = self._info.piece_length()
        return (file.offset/piece_length, (file.offset+file.size)/piece_length, 
            file.offset%piece_length, (file.offset+file.size)%piece_length)

    def play_file(self):
        outputcmd = 'mplayer -'
        stream = Popen(outputcmd.split(' '), stdin=PIPE).stdin

        pi = self.get_file_piece_info()
        
        #outputting piece stream to mplayer
        for piece in range(pi[0],pi[1]+1):
            buf=self.get_piece(piece)
            if piece==pi[0]:
                buf = buf[pi[2]:]
            if piece==pi[1]:
                buf = buf[:pi[3]]
       
            try:
                stream.write(buf)
            except Exception, err:
                exit(0)

    cache = {}
    def get_piece(self,i):
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
                    #sys.stdout.write(piece.buffer)
                    return piece.buffer
                else:
                    print >> sys.stderr,'store somewhere'
                    cache[piece.piece] = piece.buffer
                break
            time.sleep(.1)

logger = logging.getLogger('StreamPlay')
logger.setLevel(logging.DEBUG)
if (len(logger.handlers)==0):
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

testplay = StreamPlay()
testplay.load_torrent_file('sample/torrent1.torrent');