#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>
import plotly
import plotly.graph_objs as go

# My own files
from colour_science import SCILIFE_COLOURS

labels = ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018"]
values = [32, 300, 1539, 3580, 6817, 10800, 14791, 19256, 15998]
citations = go.Bar(
	x=labels,
	y=values,
	name="Articles",
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

layout = go.Layout(
    width=600, 
    height=400,
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
		title="Citation frequency", 
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
data = [citations]
fig = go.Figure(data=data, layout=layout)		
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.png'.format(label["value"].lower().replace(" ", "_")))
# plotly.io.write_image(fig, 'facility_onepagers_figures/{}_jif.pdf'.format(label["value"].lower().replace(" ", "_")))
plotly.io.write_image(fig, 'citation_frequency_nolegend.svg')