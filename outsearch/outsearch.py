import urllib
import re


class OutSearch(object):
	"""Class intended for coarse ang grain search over TPB (maybe more trackers in future)"""

	def __init__(self):
		pass

	def search(query):
		pb_url = 'http://thepiratebay.sx/search/%s/0/99/100'

		f = urllib.urlopen(pb_url % urllib.urlencode(query))
		print f.read()