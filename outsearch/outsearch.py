import urllib
import urlparse
from binascii import unhexlify
import re
import time
import libtorrent as lt
from medialib import Torrent
from medialib import MedialibDb

class OutSearch(object):
    """Class intended for coarse ang grain search over TPB (maybe more trackers in future)"""

    def __init__(self):
        pass

    def searchCoarse(self, query):
        """Coarse search, takes first result. Returns MediaLibItem """
        print "Searching "+query;

        db = MedialibDb()
        result = db.get_torrent_by_query(query)
        if (result):
            print "Found on database"
            return result
        else:
            print "Searching online"
            torrent = self.searchCoarsePB(query)
            db.add_torrent(torrent)
            return torrent

    def searchCoarsePB(self, query):
        """returns torrent file instance by given query by coarse online search"""
        pb_url = 'http://thepiratebay.sx/search/%s/0/7/100' #Ordered by seeders, audio
        
        f = urllib.urlopen(pb_url % urllib.quote_plus(query))
        page = f.read()
        res = re.search('href="(magnet:[^"]+)', page)
        
        if (res==None): raise Exception("No results were found for "+query)
        magnet = res.group(1)

        magnet_info = self.getMagnetInfo(magnet)
        t = Torrent()
        t.search_query = query
        t.title = magnet_info['name']
        t.magnet_link = magnet

        #Getting torrent file info
        print "Searching seeds & getting files list"
        self.loadFilesList(t)

        return t


    def getMagnetInfo(self, magnet):

        schema, netloc, path, query, fragment = urlparse.urlsplit(magnet)
        if "?" in path:
            pre, post = path.split("?", 1)
            if query:
                query = "&".join((post, query))
            else:
                query = post

        data = {}
        name = None
        xt = None
        trs = []

        for k,v in self.parse_qsl(query):
            if k == "dn":
                name = v.decode()

            elif k == "xt" and v.startswith("urn:btih:"):
                encoded_infohash = v[9:49]
                if len(encoded_infohash) == 32:
                    xt = b32decode(encoded_infohash)
                else:
                    xt = unhexlify(encoded_infohash)

            elif k == "tr":
                if not v.startswith('udp:'):                    
                    trs.append(v)

        return {'name':name, 'xt':xt, 'trs':trs}

    def loadFilesList(self, torrent_item):
        ses = lt.session()
        ses.listen_on(6881, 6891)

        h = lt.add_magnet_uri(ses, torrent_item.magnet_link, {'save_path': './data'})
        while (not h.has_metadata()): 
            time.sleep(1)
        info = h.get_torrent_info();

        torrent_item.set_files(info.files());


    def parse_qsl(self, query):
        """
        'foo=bar&moo=milk' --> [('foo', 'bar'), ('moo', 'milk')]
        """
        query = urllib.unquote_plus(query)
        for part in query.split("&"):
            if "=" in part:
                yield part.split("=", 1)