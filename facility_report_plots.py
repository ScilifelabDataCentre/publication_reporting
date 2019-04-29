#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import json, time, urllib

#Plotting libs
import plotly
import plotly.graph_objs as go
from colour_science import SCILIFE_COLOURS, FACILITY_USER_AFFILIATION_COLOUR_OFFICIAL
from issn_files import ISSN_IMPACT_2017, ISSN_IMPACT_2016, ISSN_IMPACT_2015, ISSN_TO_ISSNL, ISSNL_TO_ISSN, issn_to_impact
from publications_api import Publications_api

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

	user_fig_name = 'facility_onepagers_figures/{}_user.svg'.format(fac.lower().replace(" ", "_"))
	values = []
	labels = []

	for institution in user_affiliation_data.keys():
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

	for i in range(len(labels)):
		print isinstance(labels[i], str)
		print aff_map_abbr[str(labels[i])]

	print ["{} ({}%)".format(aff_map_abbr.get(labels[i], labels[i]), round(float(values[i])/float(sum(values))*float(100), 1)) for i in range(len(labels))]

	fig.add_pie(labels=labels,
		values=values,
		text=["{} ({}%)".format(aff_map_abbr.get(labels[i], labels[i]), round(float(values[i])/float(sum(values))*float(100), 1)) for i in range(len(labels))],
		marker=dict(colors=[FACILITY_USER_AFFILIATION_COLOUR_OFFICIAL.get(labels[i], "#000000") for i in range(len(labels))]),
		hole=0.6,
		textinfo="text",
		textposition="outside",
		textfont=dict(size=24, color="#000000"),
		showlegend=False)
	plotly.io.write_image(fig, user_fig_name, width=800, height=600)

def build_plots():
	### GLOBALS ### 
	T_ZERO = time.time()
	# aff_map_abbr = {
	# 	"Chalmers University of Technology": "Chalmers",
	# 	"KTH Royal Institute of Technology": "KTH",
	# 	"Swedish University of Agricultural Sciences": "SLU",
	# 	"Karolinska Institutet": "KI",
	# 	"Linköping University": "LiU",
	# 	"Lund University": "LU",
	# 	"Naturhistoriska Riksmuséet": "NRM",
	# 	"Stockholm University": "SU",
	# 	"Umeå University": "UmU",
	# 	"University of Gothenburg": "GU",
	# 	"Uppsala University": "UU",
	# 	"International University": "International<br>University",
	# 	"Other Swedish University" : "Other Swedish<br>University",
	# 	"Other Swedish organization" : "Other Swedish<br>organization",
	# 	"Other international organization" : "Other international<br>organization"
	# }
	
	# print "USER PLOTS..."

	# user_dict = dict()
	# user_data_file = open("excel_data_sheets/user_data_for_facility_report_2018.tsv", "r").readlines()
	
	# for line in user_data_file:
	# 	l_split = line.split("\t")
	# 	fac = l_split[0].strip()

	# 	institute = l_split[4].strip()
	# 	if fac in user_dict.keys():
	# 		if institute in user_dict[fac].keys():
	# 			user_dict[fac][institute] += 1
	# 		else:
	# 			user_dict[fac][institute] = 1
	# 	else:
	# 		user_dict[fac] = {institute:1}

	# for fac in user_dict.keys():
	# 	user_fig_name = 'facility_onepagers_figures/{}_user.svg'.format(fac.lower().replace(" ", "_"))
	# 	values = []
	# 	labels = []
	# 	for inst in user_dict[fac].keys():
	# 		values.append(user_dict[fac][inst])
	# 		labels.append(inst)
	# 	if sum(values) < 2:
	# 		pi_plural = "PI"
	# 	else:
	# 		pi_plural = "PIs"
	# 	fig = go.Figure(layout={
	# 		"margin":go.layout.Margin(
	# 			l=50,
	# 			r=50,
	# 			b=80,
	# 			t=30,
	# 			pad=4
	# 		),
	# 		"annotations": [{"font": {"size": 26},
	# 			"showarrow": False,
	# 			"text": "{} Individual {}".format(sum(values), pi_plural),
	# 			"x": 0.483,
	# 			"y": 0.5}]
	# 		}
	# 	)
	# 	fig.add_pie(labels=labels,
	# 		values=values,
	# 		text=["{} ({}%)".format(aff_map_abbr.get(labels[i], labels[i]), round(float(values[i])/float(sum(values))*float(100), 1)) for i in range(len(labels))],
	# 		marker=dict(colors=[FACILITY_USER_AFFILIATION_COLOUR_OFFICIAL.get(labels[i], "#000000") for i in range(len(labels))]),
	# 		hole=0.6,
	# 		textinfo="text",
	# 		textposition="outside",
	# 		textfont=dict(size=24, color="#000000"),
	# 		showlegend=False)
	# 	plotly.io.write_image(fig, user_fig_name, width=800, height=600)

	print "PUBLICATION PLOTS..."

	url = "https://publications.scilifelab.se/labels.json"
	response = urllib.urlopen(url)
	labels = json.loads(response.read())

	for label in labels["labels"]:
		print label["value"]

		url = label["links"]["self"]["href"]
		response = urllib.urlopen(url)
		publications = json.loads(response.read())
		years = {
			"2018":{"Service":0, "Collaborative":0, "Technology development":0, "None":0}, 
			"2017":{"Service":0, "Collaborative":0, "Technology development":0, "None":0}, 
			"2016":{"Service":0, "Collaborative":0, "Technology development":0, "None":0}
		}

		if not len(publications["publications"]):
			print "NO PUBLICATIONS TO GATHER:", label["value"]
			continue

		publication_issns = list()
		publication_impacts = {"2016": [], "2017": [], "2018": []}
		for pub in publications["publications"]:
			year = pub["published"].split("-")[0]
			if year in years.keys():
				catflag = False
				jifflag = False
				if label["value"] not in pub["labels"].keys():
					exit("ERROR: Somehow the label is not in the publication labels") 
					# Dont know why I added this, I probably just wanted to check
				for key in pub["labels"].keys():
					if key == label["value"]:
						try:
							years[year][pub["labels"][key]] += 1
							catflag = True
						except KeyError as e:
							years[year]["None"] += 1
							catflag = True

				if pub["journal"]["issn"]:
					issn = pub["journal"]["issn"]
					publication_issns.append(issn)
					impact = issn_to_impact(issn)

					if impact is None:
						print "NO IMPACT FACTOR FOUND FOR:", issn, pub["journal"]
					# At the end, add the impact to the list
					publication_impacts[year].append(impact)
					jifflag = True
				else: 
					# NO ISSN
					publication_impacts[year].append(None)
					jifflag = True
					print "NO ISSN FOUND FOR:", issn, pub["journal"]
				if catflag ^ jifflag:
					print "\n\nWHYYYY\n\n" # This should never happen, ie having only one of the flags

		jif_data = {"2016": [0,0,0,0,0], "2017": [0,0,0,0,0], "2018": [0,0,0,0,0]}

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

		print years["2018"]["None"]+years["2018"]["Technology development"]+years["2018"]["Collaborative"]+years["2018"]["Service"]
		trace_service = go.Bar(
			x=["2016", "2017", "2018"],
			y=[years["2016"]["Service"], years["2017"]["Service"], years["2018"]["Service"]],
			name="Service", 			
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[0],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		trace_collaborative = go.Bar(
			x=["2016", "2017", "2018"],
			y=[years["2016"]["Collaborative"], years["2017"]["Collaborative"], years["2018"]["Collaborative"]],
			name="Collaborative", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[7],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		trace_tech_dev = go.Bar(
			x=["2016", "2017", "2018"],
			y=[years["2016"]["Technology development"], years["2017"]["Technology development"], years["2018"]["Technology development"]],
			name="Technology<br>development", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[9],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		trace_none = go.Bar(
			x=["2016", "2017", "2018"],
			y=[years["2016"]["None"], years["2017"]["None"], years["2018"]["None"]],
			name="No category", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
	    	marker=dict(
		    	color=SCILIFE_COLOURS[5],
		    	line=dict(
                color='#000000',
                width=1.5)
         	)
		)
		if (years["2016"]["None"] or years["2017"]["None"] or years["2018"]["None"]):
			data = [trace_none, trace_service, trace_collaborative, trace_tech_dev]
		else:
			data = [trace_service, trace_collaborative, trace_tech_dev]

		highest_y_value = max(
			years["2016"]["None"]+years["2016"]["Technology development"]+years["2016"]["Collaborative"]+years["2016"]["Service"],
			years["2017"]["None"]+years["2017"]["Technology development"]+years["2017"]["Collaborative"]+years["2017"]["Service"],
			years["2018"]["None"]+years["2018"]["Technology development"]+years["2018"]["Collaborative"]+years["2018"]["Service"]
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
		# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_publications_by_category.png'.format(label["value"].lower().replace(" ", "_")))
		# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_publications_by_category.pdf'.format(label["value"].lower().replace(" ", "_")))
		plotly.io.write_image(fig, 'facility_onepagers_figures/{}_publications_by_category.svg'.format(label["value"].lower().replace(" ", "_")))

		total_2016 = years["2016"]["None"]+years["2016"]["Technology development"]+years["2016"]["Collaborative"]+years["2016"]["Service"]
		total_2017 = years["2017"]["None"]+years["2017"]["Technology development"]+years["2017"]["Collaborative"]+years["2017"]["Service"]
		total_2018 = years["2018"]["None"]+years["2018"]["Technology development"]+years["2018"]["Collaborative"]+years["2018"]["Service"]

		# This text file is used by the facility pdf creator script, skips having to download the entire database again
		txtfile = open('facility_onepagers_figures/{}_pub_count.txt'.format(label["value"].lower().replace(" ", "_")), "w")
		txtfile.write("{}\t{}\t{}".format(total_2016, total_2017, total_2018))
		
		jif_unknown = go.Bar(
			x=["2016", "2017", "2018"],
			y=[jif_data["2016"][4], jif_data["2017"][4], jif_data["2018"][4]],
			name="JIF unknown", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[5],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		jif_low = go.Bar(
			x=["2016", "2017", "2018"],
			y=[jif_data["2016"][0], jif_data["2017"][0], jif_data["2018"][0]],
			name="JIF < 6", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[0],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		jif_mediocre = go.Bar(
			x=["2016", "2017", "2018"],
			y=[jif_data["2016"][1], jif_data["2017"][1], jif_data["2018"][1]],
			name="JIF = 6 - 9", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[7],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		jif_good = go.Bar(
			x=["2016", "2017", "2018"],
			y=[jif_data["2016"][2], jif_data["2017"][2], jif_data["2018"][2]],
			name="JIF = 9 - 25", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[9],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)
		jif_high = go.Bar(
			x=["2016", "2017", "2018"],
			y=[jif_data["2016"][3], jif_data["2017"][3], jif_data["2018"][3]],
			name="JIF > 25", 
			textfont=dict(
		        family='sans-serif',
		        size=28,
		        color='#000000'
		    ),
		    marker=dict(
		    	color=SCILIFE_COLOURS[1],
		    	line=dict(
                color='#000000',
                width=1.5)
            )
		)

		layout = go.Layout(
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
		if (jif_data["2016"][4] or jif_data["2017"][4] or jif_data["2018"][4]):
			data = [jif_unknown, jif_low, jif_mediocre, jif_good, jif_high]
		else:
			data = [jif_low, jif_mediocre, jif_good, jif_high]
			
		fig = go.Figure(data=data, layout=layout)		
		# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.png'.format(label["value"].lower().replace(" ", "_")))
		# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.pdf'.format(label["value"].lower().replace(" ", "_")))
		plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.svg'.format(label["value"].lower().replace(" ", "_")))

	print time.time()-T_ZERO

if __name__ == "__main__":
	build_plots()