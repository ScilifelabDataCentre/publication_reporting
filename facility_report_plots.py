#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

# This is used in facility_report_pdf.py to generate the plots that are to be in the PDF.

import json, time, urllib, os

#Plotting libs
import plotly
import plotly.graph_objs as go
from colour_science import SCILIFE_COLOURS, FACILITY_USER_AFFILIATION_COLOUR_OFFICIAL
from issn_files import ISSN_IMPACT_2017, ISSN_IMPACT_2016, ISSN_IMPACT_2015, ISSN_TO_ISSNL, ISSNL_TO_ISSN, issn_to_impact
from publications_api import Publications_api

def publication_plot(label_list, year):
	url = "https://publications.scilifelab.se/labels.json"
	response = urllib.urlopen(url)
	labels = json.loads(response.read())

	labels_check_dict = dict()

	for label in labels["labels"]:
		labels_check_dict[label["value"]] = label["links"]["self"]["href"]

	all_publications = list()

	for label in label_list:
		if label not in labels_check_dict.keys():
			exit("ERROR: Wrong label, does not exist in database {}".format(label))

		url = labels_check_dict[label]
		response = urllib.urlopen(url)
		publications = json.loads(response.read())
		for pub in publications["publications"]:
			if pub not in all_publications:
				all_publications.append(pub)

	years = {
		year:{"Service":0, "Collaborative":0, "Technology development":0, "None":0}, 
		year-1:{"Service":0, "Collaborative":0, "Technology development":0, "None":0}, 
		year-2:{"Service":0, "Collaborative":0, "Technology development":0, "None":0}
	}
	publication_issns = list()
	publication_impacts = {year: [], year-1: [], year-2: []}

	for pub in all_publications:
		pub_year = int(pub["published"].split("-")[0])
		if pub_year in years.keys():
			catflag = False
			jifflag = False
			for key in pub["labels"].keys():
				if key in label_list: 
					# Need to use the right label for the category
					# This WILL break for several labels, categories will be counted several times
					try:
						years[pub_year][pub["labels"][key]] += 1
						catflag = True
					except KeyError as e:
						years[pub_year]["None"] += 1
						catflag = True

			if pub["journal"]["issn"]:
				issn = pub["journal"]["issn"]
				publication_issns.append(issn)
				impact = issn_to_impact(issn)

				# if impact is None:
				# 	print "NO IMPACT FACTOR FOUND FOR:", issn, pub["journal"]
				# At the end, add the impact to the list
				publication_impacts[pub_year].append(impact)
				jifflag = True
			else: 
				# NO ISSN
				publication_impacts[pub_year].append(None)
				jifflag = True
				# print "NO ISSN FOUND FOR:", pub["journal"]
			if catflag ^ jifflag:
				print "\n\nERROR THIS SHOULD NEVER HAPPEN. PUBLICATION ADDED TO CATEGORY PLOT BUT NOT JIF PLOT\n\n", pub
				# This should never happen, ie having only one of the flags
				# I added this to make sure all publications are always visible in BOTH graphs

	jif_data = {year-2: [0,0,0,0,0], year-1: [0,0,0,0,0], year: [0,0,0,0,0]}

	for year in publication_impacts.keys():
		for impact in publication_impacts[year]:
			if impact is not None:
				real_impact = float(impact)/1000
				#print real_impact
				if real_impact>25.0:
					jif_data[year][3] += 1
					continue
				if real_impact>9.0:
					jif_data[year][2] += 1
					continue
				if real_impact>6.0:
					jif_data[year][1] += 1
					continue					
				jif_data[year][0] += 1
			else:
				jif_data[year][4] += 1

	trace_service = go.Bar(
		x=[year-2, year-1, year],
		y=[years[year-2]["Service"], years[year-1]["Service"], years[year]["Service"]],
		name="Service",			
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[0],
			line=dict(color='#000000', width=1.5)
		)
	)
	trace_collaborative = go.Bar(
		x=[year-2, year-1, year],
		y=[years[year-2]["Collaborative"], years[year-1]["Collaborative"], years[year]["Collaborative"]],
		name="Collaborative", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[7],
			line=dict(color='#000000', width=1.5)
		)
	)
	trace_tech_dev = go.Bar(
		x=[year-2, year-1, year],
		y=[years[year-2]["Technology development"], years[year-1]["Technology development"], years[year]["Technology development"]],
		name="Technology<br>development", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[9],
			line=dict(color='#000000', width=1.5)
		)
	)
	trace_none = go.Bar(
		x=[year-2, year-1, year],
		y=[years[year-2]["None"], years[year-1]["None"], years[year]["None"]],
		name="No category", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[5],
			line=dict(color='#000000', width=1.5)
		)
	)
	if (years[year-2]["None"] or years[year-1]["None"] or years[year]["None"]):
		data = [trace_none, trace_service, trace_collaborative, trace_tech_dev]
	else:
		data = [trace_service, trace_collaborative, trace_tech_dev]

	highest_y_value = max(
		years[year-2]["None"]+years[year-2]["Technology development"]+years[year-2]["Collaborative"]+years[year-2]["Service"],
		years[year-1]["None"]+years[year-1]["Technology development"]+years[year-1]["Collaborative"]+years[year-1]["Service"],
		years[year]["None"]+years[year]["Technology development"]+years[year]["Collaborative"]+years[year]["Service"]
	)
	yaxis_tick = 1
	if highest_y_value>10:
		yaxis_tick = 2
	if highest_y_value>20:
		yaxis_tick = 5
	if highest_y_value>50:
		yaxis_tick = 10
	if highest_y_value>100:
		yaxis_tick = 20
	if highest_y_value>150:
		yaxis_tick = 40
	if highest_y_value>200:
		yaxis_tick = 50
	if highest_y_value>1000:
		yaxis_tick = 100

	layout = go.Layout(
		barmode='stack',
		margin=go.layout.Margin(
			l=60,
			r=50,
			b=50,
			t=30,
			pad=4
		),
		xaxis=dict(
			showticklabels=True, 
			dtick=1,
			zeroline=True,
			tickfont=dict(
				family='sans-serif',
				size=28,
				color='#000000'
			)
		),
		yaxis=dict(
			showticklabels=True,
			dtick=yaxis_tick,
			tickfont=dict(
				family='sans-serif',
				size=28,
				color='#000000'
			),
			range=[0, int(highest_y_value*1.15)] # Set the ylim slightly higher than the max value for a prettier graph
		),
		legend=dict(
			traceorder='normal',
			font=dict(
				family='sans-serif',
				size=20,
				color='#000'
			)
		)
	)

	fig = go.Figure(data=data, layout=layout)
	# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_publications_by_category.png'.format(label_list[0].lower().replace(" ", "_")))
	# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_publications_by_category.pdf'.format(label_list[0].lower().replace(" ", "_")))
	plotly.io.write_image(fig, 'facility_onepagers_figures/{}_publications_by_category.svg'.format(label_list[0].lower().replace(" ", "_")))

	total_pubs_lastlast_year = years[year-2]["None"]+years[year-2]["Technology development"]+years[year-2]["Collaborative"]+years[year-2]["Service"]
	total_pubs_last_year = years[year-1]["None"]+years[year-1]["Technology development"]+years[year-1]["Collaborative"]+years[year-1]["Service"]
	total_pubs_current_year = years[year]["None"]+years[year]["Technology development"]+years[year]["Collaborative"]+years[year]["Service"]

	jif_unknown = go.Bar(
		x=[year-2, year-1, year],
		y=[jif_data[year-2][4], jif_data[year-1][4], jif_data[year][4]],
		name="JIF unknown", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[5],
			line=dict(color='#000000', width=1.5)
		)
	)
	jif_low = go.Bar(
		x=[year-2, year-1, year],
		y=[jif_data[year-2][0], jif_data[year-1][0], jif_data[year][0]],
		name="JIF < 6", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[0],
			line=dict(color='#000000', width=1.5)
		)
	)
	jif_mediocre = go.Bar(
		x=[year-2, year-1, year],
		y=[jif_data[year-2][1], jif_data[year-1][1], jif_data[year][1]],
		name="JIF = 6 - 9", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[7],
			line=dict(color='#000000', width=1.5)
		)
	)
	jif_good = go.Bar(
		x=[year-2, year-1, year],
		y=[jif_data[year-2][2], jif_data[year-1][2], jif_data[year][2]],
		name="JIF = 9 - 25", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[9],
			line=dict(color='#000000', width=1.5)
		)
	)
	jif_high = go.Bar(
		x=[year-2, year-1, year],
		y=[jif_data[year-2][3], jif_data[year-1][3], jif_data[year][3]],
		name="JIF > 25", 
		textfont=dict(
			family='sans-serif',
			size=28,
			color='#000000'
		),
		marker=dict(
			color=SCILIFE_COLOURS[1],
			line=dict(color='#000000', width=1.5)
		)
	)

	jif_layout = go.Layout(
		barmode="stack",
		margin=go.layout.Margin(
			l=60,
			r=50,
			b=50,
			t=30,
			pad=4
		),
		xaxis=dict(
			showticklabels=True, 
			dtick=1,
			zeroline=True,
			tickfont=dict(
				family='sans-serif',
				size=28,
				color='#000000'
			)
		),
		yaxis=dict(
			showticklabels=True,
			dtick=yaxis_tick,
			tickfont=dict(
				family='sans-serif',
				size=28,
				color='#000000'
			),
			range=[0, int(highest_y_value*1.15)]
		),
		legend=dict(
			traceorder='normal',
			font=dict(
				family='sans-serif',
				size=20,
				color='#000'
			)
		)
	)
	if (jif_data[year-2][4] or jif_data[year-1][4] or jif_data[year][4]):
		jif_fig_data = [jif_unknown, jif_low, jif_mediocre, jif_good, jif_high]
	else:
		jif_fig_data = [jif_low, jif_mediocre, jif_good, jif_high]
		
	jif_fig = go.Figure(data=jif_fig_data, layout=jif_layout)		
	# plotly.io.write_image(jif_fig, 'facility_onepagers_figures/{}_jif.png'.format(label_list[0].lower().replace(" ", "_")))
	# plotly.io.write_image(jif_fig, 'facility_onepagers_figures/{}_jif.pdf'.format(label_list[0].lower().replace(" ", "_")))
	plotly.io.write_image(jif_fig, 'facility_onepagers_figures/{}_jif.svg'.format(label_list[0].lower().replace(" ", "_")))

	return (
		'facility_onepagers_figures/{}_publications_by_category.svg'.format(label_list[0].lower().replace(" ", "_")),
		'facility_onepagers_figures/{}_jif.svg'.format(label_list[0].lower().replace(" ", "_")),
		(total_pubs_current_year, total_pubs_last_year, total_pubs_lastlast_year)
	)
	

def user_plot(user_affiliation_data, fac):
	aff_map_abbr = {
		"Chalmers University of Technology": "Chalmers",
		"KTH Royal Institute of Technology": "KTH",
		"Swedish University of Agricultural Sciences": "SLU",
		"Karolinska Institutet": "KI",
		"Linköping University": "LiU",
		"Lund University": "LU",
		"Naturhistoriska Riksmuséet": "NRM",
		"Stockholm University": "SU",
		"Umeå University": "UmU",
		"University of Gothenburg": "GU",
		"Uppsala University": "UU",
		"International University": "International<br>University",
		"Other Swedish University" : "Other Swedish<br>University",
		"Other Swedish organization" : "Other Swedish<br>organization",
		"Other international organization" : "Other international<br>organization",
		"Industry": "Industry",
		"Healthcare": "Healthcare"
	}

	if not os.path.isdir("facility_onepagers_figures/"):
		os.mkdir("facility_onepagers_figures/")

	user_fig_name = 'facility_onepagers_figures/{}_user.svg'.format(fac.encode('utf-8').lower().replace(" ", "_"))
	values = []
	labels = []

	for institution in user_affiliation_data.keys():
		if user_affiliation_data[institution]:
			values.append(user_affiliation_data[institution])
			labels.append(institution)
	if sum(values) < 2:
		pi_plural = "PI"
	else:
		pi_plural = "PIs"
	fig = go.Figure(layout={
		"margin":go.layout.Margin(
			l=50,
			r=50,
			b=80,
			t=30,
			pad=4
		),
		"annotations": [{"font": {"size": 26},
			"showarrow": False,
			"text": "{} Individual {}".format(sum(values), pi_plural),
			"x": 0.483,
			"y": 0.5}]
		}
	)

	fig.add_pie(labels=labels,
		values=values,
		text=["{} ({}%)".format(aff_map_abbr.get(labels[i].encode('utf-8'), labels[i].encode('utf-8')), round(float(values[i])/float(sum(values))*float(100), 1)) for i in range(len(labels))],
		marker=dict(colors=[FACILITY_USER_AFFILIATION_COLOUR_OFFICIAL.get(labels[i], "#000000") for i in range(len(labels))]),
		hole=0.6,
		textinfo="text",
		textposition="outside",
		textfont=dict(size=24, color="#000000"),
		showlegend=False)
	plotly.io.write_image(fig, user_fig_name, width=800, height=600)

	return user_fig_name