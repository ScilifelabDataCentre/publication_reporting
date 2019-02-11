#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import json, urllib

class Publications_api(object):
	'''
	Class to handle publication database API calls
	'''
	def __init__(self, years=None):
		'''
		Sets up the standard URLs
		'''
		self.years = years
		self.timestamp = None
		self.source_links = []
		self.collection_timestamp = None

		if self.years:
			self.publications_url = ["https://publications.scilifelab.se/publications/{}.json".format(year) for year in years]
			self.publications_affiliated_url = ["https://publications-affiliated.scilifelab.se/publications/{}.json".format(year) for year in years]
		else:
			self.publications_url = "https://publications.scilifelab.se/publications.json"
			self.publications_affiliated_url = "https://publications-affiliated.scilifelab.se/publications.json"
	
	def api_call(self, url):
		'''
		Make an API call and return the publications
		Before returning set source links and timestamp
		'''
		tmp_json = json.loads(urllib.urlopen(url).read())

		self.source_links.append(tmp_json["links"]["self"]["href"])
		self.collection_timestamp =	tmp_json["timestamp"]

		return tmp_json["publications"]

	def get_publications(self):
		'''
		Retrieves publications from Facility publications DB
		'''
		publications = []
		if self.years:
			for url in self.publications_url:
				publications += self.api_call(url)

		else:
			publications += self.api_call(self.publications_url)

		return publications

	def get_publications_affiliated(self):
		'''
		Retrieves publications from Affiliated publications DB
		'''
		publications = []
		if self.years:
			for url in self.publications_affiliated_url:
				publications += self.api_call(url)

		else:
			publications += self.api_call(self.publications_affiliated_url)

		return publications