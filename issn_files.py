#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import os

# ISSN files, to find JIFs for articles. Impact files are from webofscience and ISSN conversion tables from issn.org
ISSN_IMPACT_2017 = dict()
ISSN_IMPACT_2016 = dict()
ISSN_IMPACT_2015 = dict()

# There are two types of ISSNs - these tables convert between them 
ISSNL_TO_ISSN = dict()
ISSN_TO_ISSNL = dict()

issn_f = open(os.path.dirname(os.path.realpath(__file__))+"/assets/ISSN_impact_2017.tsv", "r")
for journal in issn_f:
	j = journal.strip().split("\t")
	#print j
	try:
		ISSN_IMPACT_2017[j[0]]=int(j[1])
	except ValueError as e:
		ISSN_IMPACT_2017[j[0]]=0
issn_f.close()

issn_f = open(os.path.dirname(os.path.realpath(__file__))+"/assets/ISSN_impact_2016.tsv", "r")
for journal in issn_f:
	j = journal.strip().split("\t")
	#print j
	try:
		ISSN_IMPACT_2016[j[0]]=int(j[1])
	except ValueError as e:
		ISSN_IMPACT_2016[j[0]]=0
issn_f.close()

issn_f = open(os.path.dirname(os.path.realpath(__file__))+"/assets/ISSN_impact_2015.tsv", "r")
for journal in issn_f:
	j = journal.strip().split("\t")
	#print j
	try:
		ISSN_IMPACT_2015[j[0]]=int(j[1])
	except ValueError as e:
		ISSN_IMPACT_2015[j[0]]=0
issn_f.close()

issn_to_l = open(os.path.dirname(os.path.realpath(__file__))+"/assets/ISSN-to-ISSN-L.tsv.relevant", "r")
for entry in issn_to_l:
	e = entry.strip().split("\t")
	ISSN_TO_ISSNL[e[0]] = e[1]
issn_to_l.close()

issn_l = open(os.path.dirname(os.path.realpath(__file__))+"/assets/ISSN-L-to-ISSN.tsv.relevant", "r")
for entry in issn_l:
	e = entry.strip().split("\t")
	ISSNL_TO_ISSN[e[0]] = e[1:]
issn_l.close()

def issn_to_impact(issn):
	impact = None

	# We check 2017 first in case they have the info more updated is better
	try:
		impact = ISSN_IMPACT_2017[issn]
		#print "YES1 2017"
	except KeyError as e:
		pass

	if not impact:
		try:
			impact = ISSN_IMPACT_2017[ISSN_TO_ISSNL[issn]]
			#print "YES2 2017"
		except KeyError as e:
			pass
	
	if not impact:
		try:
			for issnl_entry in ISSNL_TO_ISSN[ISSN_TO_ISSNL[issn]]:
				try:
					impact = ISSN_IMPACT_2017[issnl_entry]
					#print "YES3 2017"
				except KeyError as e:
					pass
		except KeyError as e:
			pass

	# We still check 2016 and 2015 in case they have the info
	if not impact:
		try:
			impact = ISSN_IMPACT_2016[issn]
			#print "YES1 2016!!"
		except KeyError as e:
			pass
	if not impact:
		try:
			impact = ISSN_IMPACT_2016[ISSN_TO_ISSNL[issn]]
			#print "YES2 2016!!"
		except KeyError as e:
			pass
	if not impact:
		try:
			for issnl_entry in ISSNL_TO_ISSN[ISSN_TO_ISSNL[issn]]:
				try:
					impact = ISSN_IMPACT_2016[issnl_entry]
					#print "YES3 2016!!"
				except KeyError as e:
					pass
		except KeyError as e:
			pass

	# We still check 2015 in case they have the info
	if not impact:
		try:
			impact = ISSN_IMPACT_2015[issn]
			#print "YES1 2015!!"
		except KeyError as e:
			pass
	if not impact:
		try:
			impact = ISSN_IMPACT_2015[ISSN_TO_ISSNL[issn]]
			#print "YES2 2015!!"
		except KeyError as e:
			pass
	if not impact:
		try:
			for issnl_entry in ISSNL_TO_ISSN[ISSN_TO_ISSNL[issn]]:
				try:	
					impact = ISSN_IMPACT_2015[issnl_entry]
					#print "YES3 2015!!"
				except KeyError as e:
					pass
		except KeyError as e:
			pass

	# No more options for finding the impact factor
	return impact
