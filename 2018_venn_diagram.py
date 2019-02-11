#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

from matplotlib_venn import venn2, venn2_circles
import matplotlib.pyplot as plt
import plotly

#My own files
from publications_api import Publications_api

years = ["2017", "2018"]
input_filename = "-".join(years)

pub_getter = Publications_api(years=years)

pubs = pub_getter.get_publications()
affs = pub_getter.get_publications_affiliated()

pub_count = len(pubs)+len(affs)

print "Sources:", pub_getter.source_links

fac_dois = list()
aff_dois = list()
fellows_dois = list()
service_dois = list()
techdev_dois = list()
collab_dois = list()
none_dois = list()

for pub in pubs:
	doi = pub["doi"]
	if not doi: 
		continue
	fac_dois.append(doi)
	for label_type in pub["labels"].values():
		if label_type == None:
			none_dois.append(doi)
		elif label_type == 'Service':
			service_dois.append(doi)
		elif label_type == 'Technology development':
			techdev_dois.append(doi)
		elif label_type == 'Collaborative':
			collab_dois.append(doi)

for pub in affs:
	doi = pub["doi"]
	if not doi: 
		continue
	if "Affiliated researcher" in pub["labels"]:
		aff_dois.append(doi)
	elif "Fellow" in pub["labels"]:
		fellows_dois.append(doi)

aff_intersect_fac = list()
aff_service = 0
aff_collab = 0
aff_tech = 0

for doi in aff_dois:
	if doi in fac_dois:
		if doi in service_dois:
			aff_service+=1
		if doi in collab_dois:
			aff_collab+=1
		if doi in techdev_dois:
			aff_tech+=1
		aff_intersect_fac.append(doi)

fac_service = 0
fac_collab = 0
fac_tech = 0
for doi in fac_dois:
	if doi in aff_intersect_fac:
		pass
	else:
		if doi in service_dois:
			fac_service+=1
		if doi in collab_dois:
			fac_collab+=1
		if doi in techdev_dois:
			fac_tech+=1

# print aff_service, aff_collab, aff_tech, len(aff_intersect_fac)
# print fac_service, fac_collab, fac_tech, len(fac_dois)-len(aff_intersect_fac)

labels_aff = ["Service", "Technology development", "Collaborative"]
values_aff = [aff_service, aff_collab, aff_tech]

labels_fac = labels_aff # same labels
values_fac = [fac_service, fac_collab, fac_tech]

fig = {
	'data': [
		{
			'labels': labels_aff,
			'values': values_aff,
			'type': 'pie',
			'name': 'Affiliated',
			'marker': {'colors': ['#80C41C','#AEC69C', '#378CAF'], 'line':dict(color='#000000', width=1)},
			'domain': {'x': [0, .48],
				'y': [0, 1]},
		},
		{
			'labels': labels_fac,
			'values': values_fac,
			'type': 'pie',
			'name': 'Facility Users',
			'marker': {'colors': ['#80C41C','#AEC69C', '#378CAF'], 'line':dict(color='#000000', width=1)},
			'domain': {'x': [0.52, 1],
				'y': [0, 1]},
		}
	]
}
plotly.io.write_image(fig, 'pie_chart_for_venn.svg')

# The venn diagram as a pie chart, hard coded values... 
labels = ["A", "B"]
values = [760, 370]
fig = {
	'data': [
		{
			'labels': labels,
			'values': values,
			'type': 'pie',
			'name': 'Affiliated',
			'marker': {'colors': ['#87B0AB','#468365'], 'line':dict(color='#000000', width=1)},
			'domain': {'x': [0, .48],
				'y': [0, 1]},
		}
	]
}
plotly.io.write_image(fig, 'venn_as_pie.svg')

venn_two = venn2((len(aff_dois)-len(aff_intersect_fac),len(fac_dois)-len(aff_intersect_fac), len(aff_intersect_fac)), set_labels = ('Affiliated', 'Facility Users'), set_colors=("#80C41C", "#378CAF"))
venn_two_c = venn2_circles(((len(aff_dois)-len(aff_intersect_fac),len(fac_dois)-len(aff_intersect_fac), len(aff_intersect_fac))),  linestyle='solid', linewidth=2, color="black")

plt.savefig("venn1718.svg", format="svg")
plt.savefig("venn1718.png", dpi=1000, format="png")
plt.gcf().clear()

# Run on all publications
pub_getter_all = Publications_api()
pub_json = pub_getter_all.get_publications()
aff_json = pub_getter_all.get_publications_affiliated()

print "Sources : {}".format(pub_getter_all.source_links)

fac_dois = list()
aff_dois = list()
# Following not actually used for anything, just in case
fellows_dois = list()
service_dois = list()
techdev_dois = list()
collab_dois = list()
none_dois = list()

for pub in pub_json:
	doi = pub["doi"]
	if not doi: 
		continue
	fac_dois.append(doi)
	#print pub["labels"]
	for label_type in pub["labels"].values():
		if label_type == None:
			none_dois.append(doi)
		elif label_type == 'Service':
			service_dois.append(doi)
		elif label_type == 'Technology development':
			techdev_dois.append(doi)
		elif label_type == 'Collaborative':
			collab_dois.append(doi)

for pub in aff_json:
	doi = pub["doi"]
	if not doi: 
		continue
	if "Affiliated researcher" in pub["labels"]:
		aff_dois.append(doi)
	elif "Fellow" in pub["labels"]:
		fellows_dois.append(doi)


venn_two = venn2([set(aff_dois), set(fac_dois)], set_labels = ('Affiliated', 'Facility Users'), set_colors=("#80C41C", "#378CAF"))
venn_two_c = venn2_circles([set(aff_dois), set(fac_dois)],  linestyle='solid', linewidth=2, color="black")
plt.savefig("venn_allyrs.svg", format="svg")
plt.savefig("venn_allyrs.png", dpi=1000, format="png")
plt.gcf().clear()


