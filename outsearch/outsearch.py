import urllib
import urlparse
from binascii import unhexlify
import re
from medialib import MediaLibItem


class OutSearch(object):
    """Class intended for coarse ang grain search over TPB (maybe more trackers in future)"""

    def __init__(self):
        pass

    def searchCoarse(self, query):
        """Coarse search, takes first result. Returns MediaLibItem """
        pb_url = 'http://thepiratebay.sx/search/%s/0/7/100' #Ordered by seeders, audio
        
        f = urllib.urlopen(pb_url % urllib.quote_plus(query))
        page = f.read()
        res = re.search('href="(magnet:[^"]+)', page)
        
        if (res==None): raise Exception("No results were found for "+query)
        magnet = res.group(1)
        magnet_info = self.getMagnetInfo(magnet)

        mli = MediaLibItem(query, magnet_info['name'], '', magnet)
        return mli

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

    def parse_qsl(self, query):
        """
        'foo=bar&moo=milk' --> [('foo', 'bar'), ('moo', 'milk')]
        """
        query = urllib.unquote_plus(query)
        for part in query.split("&"):
            if "=" in part:
                yield part.split("=", 1)