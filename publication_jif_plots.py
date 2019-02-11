#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

# Plotting libs
import plotly
import plotly.graph_objs as go

# My own files
from colour_science import SCILIFE_COLOURS
from issn_files import ISSN_IMPACT_2017, ISSN_IMPACT_2016, ISSN_IMPACT_2015, ISSN_TO_ISSNL, ISSNL_TO_ISSN, issn_to_impact
from publications_api import Publications_api

print "PUBLICATION PLOTS..."
allyrs = ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018"]
years_1015 = ["2010", "2011", "2012", "2013", "2014", "2015"]
years_161718 = ["2016", "2017", "2018"]

pub_getter_1015 = Publications_api(years=years_1015)
pub_allyrs = pub_getter_1015.get_publications()
aff_allyrs = pub_getter_1015.get_publications_affiliated()
print "Sources:", pub_getter_1015.source_links


pub_getter_161718 = Publications_api(years=years_161718)
pub_161718 = pub_getter_161718.get_publications()
aff_161718 = pub_getter_161718.get_publications_affiliated()

pub_allyrs += pub_161718
aff_allyrs += aff_161718

print "Sources:", pub_getter_1015.source_links, pub_getter_161718.source_links

pub_aff_161718 = pub_161718 + aff_161718
pub_aff_allyrs = pub_allyrs + aff_allyrs

publication_dois = list()
publication_issns = list()
publication_impacts = {"2010": [], "2011": [], "2012": [], "2013": [], "2014": [], "2015": [], "2016": [], "2017": [], "2018": []}
for pub in pub_aff_allyrs:
	if pub["doi"] in publication_dois:
		continue
	publication_dois.append(pub["doi"])
	year = pub["published"].split("-")[0]
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

jif_data = {"2010": [0,0,0,0,0], "2011": [0,0,0,0,0], "2012": [0,0,0,0,0], "2013": [0,0,0,0,0], "2014": [0,0,0,0,0], "2015": [0,0,0,0,0], "2016": [0,0,0,0,0], "2017": [0,0,0,0,0], "2018": [0,0,0,0,0]}

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


jif_unknown = go.Bar(
	x=allyrs,
	y=[jif_data["2010"][4], jif_data["2011"][4], jif_data["2012"][4], jif_data["2013"][4], jif_data["2014"][4], jif_data["2015"][4], jif_data["2016"][4], jif_data["2017"][4], jif_data["2018"][4]],
	name="JIF unknown", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][0], jif_data["2011"][0], jif_data["2012"][0], jif_data["2013"][0], jif_data["2014"][0], jif_data["2015"][0], jif_data["2016"][0], jif_data["2017"][0], jif_data["2018"][0]],
	name="JIF < 6", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][1], jif_data["2011"][1], jif_data["2012"][1], jif_data["2013"][1], jif_data["2014"][1], jif_data["2015"][1], jif_data["2016"][1], jif_data["2017"][1], jif_data["2018"][1]],
	name="JIF = 6 - 9", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][2], jif_data["2011"][2], jif_data["2012"][2], jif_data["2013"][2], jif_data["2014"][2], jif_data["2015"][2], jif_data["2016"][2], jif_data["2017"][2], jif_data["2018"][2]],
	name="JIF = 9 - 25", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][3], jif_data["2011"][3], jif_data["2012"][3], jif_data["2013"][3], jif_data["2014"][3], jif_data["2015"][3], jif_data["2016"][3], jif_data["2017"][3], jif_data["2018"][3]],
	name="JIF > 25", 
	textfont=dict(
        family='Arial',
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
    width=1200, 
    height=600,
    margin=go.layout.Margin(
		l=100,
		r=100,
		b=100,
		t=30,
		pad=4
	),
	xaxis=dict(
		showticklabels=True, 
		dtick=1,
		zeroline=True,
		tickfont=dict(
        	family='Arial',
   			size=28,
        	color='#000000'
    	)
	),
	yaxis=dict(
		showticklabels=True,
		tickfont=dict(
        	family='Arial',
   			size=28,
        	color='#000000'
    	)
	),
	legend=dict(
		traceorder='normal',
		font=dict(
			family='Arial',
			size=20,
			color='#000'
		)
	)
)
data = [jif_unknown, jif_low, jif_mediocre, jif_good, jif_high]

	
fig = go.Figure(data=data, layout=layout)		
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.png'.format(label["value"].lower().replace(" ", "_")))
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.pdf'.format(label["value"].lower().replace(" ", "_")))
plotly.io.write_image(fig, 'jif_fac_and_aff_allyrs.svg')



publication_dois = list()
publication_issns = list()
publication_impacts = {"2010": [], "2011": [], "2012": [], "2013": [], "2014": [], "2015": [], "2016": [], "2017": [], "2018": []}
for pub in pub_allyrs:
	if pub["doi"] in publication_dois:
		continue
	publication_dois.append(pub["doi"])
	year = pub["published"].split("-")[0]
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

jif_data = {"2010": [0,0,0,0,0], "2011": [0,0,0,0,0], "2012": [0,0,0,0,0], "2013": [0,0,0,0,0], "2014": [0,0,0,0,0], "2015": [0,0,0,0,0], "2016": [0,0,0,0,0], "2017": [0,0,0,0,0], "2018": [0,0,0,0,0]}

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


jif_unknown = go.Bar(
	x=allyrs,
	y=[jif_data["2010"][4], jif_data["2011"][4], jif_data["2012"][4], jif_data["2013"][4], jif_data["2014"][4], jif_data["2015"][4], jif_data["2016"][4], jif_data["2017"][4], jif_data["2018"][4]],
	name="JIF unknown", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][0], jif_data["2011"][0], jif_data["2012"][0], jif_data["2013"][0], jif_data["2014"][0], jif_data["2015"][0], jif_data["2016"][0], jif_data["2017"][0], jif_data["2018"][0]],
	name="JIF < 6", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][1], jif_data["2011"][1], jif_data["2012"][1], jif_data["2013"][1], jif_data["2014"][1], jif_data["2015"][1], jif_data["2016"][1], jif_data["2017"][1], jif_data["2018"][1]],
	name="JIF = 6 - 9", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][2], jif_data["2011"][2], jif_data["2012"][2], jif_data["2013"][2], jif_data["2014"][2], jif_data["2015"][2], jif_data["2016"][2], jif_data["2017"][2], jif_data["2018"][2]],
	name="JIF = 9 - 25", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][3], jif_data["2011"][3], jif_data["2012"][3], jif_data["2013"][3], jif_data["2014"][3], jif_data["2015"][3], jif_data["2016"][3], jif_data["2017"][3], jif_data["2018"][3]],
	name="JIF > 25", 
	textfont=dict(
        family='Arial',
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
    width=1200, 
    height=600,
    margin=go.layout.Margin(
		l=100,
		r=100,
		b=100,
		t=30,
		pad=4
	),
	xaxis=dict(
		showticklabels=True, 
		dtick=1,
		zeroline=True,
		tickfont=dict(
        	family='Arial',
   			size=28,
        	color='#000000'
    	)
	),
	yaxis=dict(
		showticklabels=True,
		tickfont=dict(
        	family='Arial',
   			size=28,
        	color='#000000'
    	)
	),
	legend=dict(
		traceorder='normal',
		font=dict(
			family='Arial',
			size=20,
			color='#000'
		)
	)
)
data = [jif_unknown, jif_low, jif_mediocre, jif_good, jif_high]

fig = go.Figure(data=data, layout=layout)
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.png'.format(label["value"].lower().replace(" ", "_")))
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.pdf'.format(label["value"].lower().replace(" ", "_")))
plotly.io.write_image(fig, 'jif_fac_allyrs.svg')




publication_dois = list()
publication_issns = list()
publication_impacts = {"2010": [], "2011": [], "2012": [], "2013": [], "2014": [], "2015": [], "2016": [], "2017": [], "2018": []}
for pub in aff_allyrs:
	if pub["doi"] in publication_dois:
		continue
	publication_dois.append(pub["doi"])
	year = pub["published"].split("-")[0]
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

jif_data = {"2010": [0,0,0,0,0], "2011": [0,0,0,0,0], "2012": [0,0,0,0,0], "2013": [0,0,0,0,0], "2014": [0,0,0,0,0], "2015": [0,0,0,0,0], "2016": [0,0,0,0,0], "2017": [0,0,0,0,0], "2018": [0,0,0,0,0]}

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


jif_unknown = go.Bar(
	x=allyrs,
	y=[jif_data["2010"][4], jif_data["2011"][4], jif_data["2012"][4], jif_data["2013"][4], jif_data["2014"][4], jif_data["2015"][4], jif_data["2016"][4], jif_data["2017"][4], jif_data["2018"][4]],
	name="JIF unknown", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][0], jif_data["2011"][0], jif_data["2012"][0], jif_data["2013"][0], jif_data["2014"][0], jif_data["2015"][0], jif_data["2016"][0], jif_data["2017"][0], jif_data["2018"][0]],
	name="JIF < 6", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][1], jif_data["2011"][1], jif_data["2012"][1], jif_data["2013"][1], jif_data["2014"][1], jif_data["2015"][1], jif_data["2016"][1], jif_data["2017"][1], jif_data["2018"][1]],
	name="JIF = 6 - 9", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][2], jif_data["2011"][2], jif_data["2012"][2], jif_data["2013"][2], jif_data["2014"][2], jif_data["2015"][2], jif_data["2016"][2], jif_data["2017"][2], jif_data["2018"][2]],
	name="JIF = 9 - 25", 
	textfont=dict(
        family='Arial',
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
	x=allyrs,
	y=[jif_data["2010"][3], jif_data["2011"][3], jif_data["2012"][3], jif_data["2013"][3], jif_data["2014"][3], jif_data["2015"][3], jif_data["2016"][3], jif_data["2017"][3], jif_data["2018"][3]],
	name="JIF > 25", 
	textfont=dict(
        family='Arial',
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
    width=1200, 
    height=600,
    margin=go.layout.Margin(
		l=100,
		r=100,
		b=100,
		t=30,
		pad=4
	),
	xaxis=dict(
		showticklabels=True, 
		dtick=1,
		zeroline=True,
		tickfont=dict(
        	family='Arial',
   			size=28,
        	color='#000000'
    	)
	),
	yaxis=dict(
		showticklabels=True,
		tickfont=dict(
        	family='Arial',
   			size=28,
        	color='#000000'
    	)
	),
	legend=dict(
		traceorder='normal',
		font=dict(
			family='Arial',
			size=20,
			color='#000'
		)
	)
)
data = [jif_unknown, jif_low, jif_mediocre, jif_good, jif_high]

	
fig = go.Figure(data=data, layout=layout)		
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.png'.format(label["value"].lower().replace(" ", "_")))
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.pdf'.format(label["value"].lower().replace(" ", "_")))
plotly.io.write_image(fig, 'jif_aff_allyrs.svg')
