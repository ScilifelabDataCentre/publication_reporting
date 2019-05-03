#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

#Plotting libs
import plotly
import plotly.graph_objs as go
import random

def mean(numbers):
	return float(sum(numbers)) / max(len(numbers), 1)

survey_data = dict()

all_service = list()
all_quality = list()
all_importance = list()
all_fee = list()
all_morethanone = list()
all_again = list()
all_impact = list()

affiliation_data = dict()

correlation_data = [[],[],[],[],[],[],[],[]]

with open("user_survey_data/user_survey_parsed.tsv", "r") as survey_file:
	first_line = survey_file.readline()
	for line in survey_file:
		# print line
		line_split = line.split("\t")
		# print line_split[3]
		survey_response = line_split[3].split(",")
		# print len(survey_response)

		affiliations = line_split[1].split(",")

		for response in survey_response:
			response_split = response.rsplit("-", 1)
			response_values = response_split[1].split(":")
			if response_split[0] not in survey_data.keys():
				survey_data[response_split[0]] = [[],[],[],[],[],[]]

			for affiliation in affiliations:
				if affiliation not in affiliation_data.keys():
					affiliation_data[affiliation] = [[],[],[],[],[],[],[]]
			# print response_values	
			for i, response_list in enumerate(survey_data[response_split[0]]):
				response_list.append(int(response_values[i]))
				for affiliation in affiliations:
					affiliation_data[affiliation][i].append(int(response_values[i]))

		for affiliation in affiliations:
			affiliation_data[affiliation][6].append(int(line_split[4]))
			
			all_service.append(int(response_values[0]))
			all_quality.append(int(response_values[1]))
			all_importance.append(int(response_values[2]))
			all_fee.append(int(response_values[3]))
			all_morethanone.append(int(response_values[4]))
			all_again.append(int(response_values[5]))

			all_impact.append(int(line_split[4]))

			correlation_data[0].append(int(response_values[0])+random.uniform(-0.25, 0.25))
			correlation_data[1].append(int(response_values[1])+random.uniform(-0.25, 0.25))
			correlation_data[2].append(int(response_values[2])+random.uniform(-0.25, 0.25))
			correlation_data[3].append(int(response_values[3])+random.uniform(-0.25, 0.25))
			correlation_data[4].append(int(response_values[4])+random.uniform(-0.25, 0.25))
			correlation_data[5].append(int(response_values[5])+random.uniform(-0.25, 0.25))
			correlation_data[6].append(int(line_split[4])+random.uniform(-0.25, 0.25))
			correlation_data[7].append(line_split[3])

			# print response_split[0], survey_data[response_split[0]]

print affiliation_data

aff_traces = list()

aff_names = list()
aff_0 = list()
aff_1 = list()
aff_2 = list()
aff_3 = list()
aff_4 = list()
aff_5 = list()
aff_6 = list()

aff_col = list()

for aff in sorted(affiliation_data.keys()):
	aff_names.append(aff)
	aff_0.append(mean(affiliation_data[aff][0]))
	aff_1.append(mean(affiliation_data[aff][1]))
	aff_2.append(mean(affiliation_data[aff][2]))
	aff_3.append(mean(affiliation_data[aff][3]))
	aff_4.append(mean(affiliation_data[aff][4]))
	aff_5.append(mean(affiliation_data[aff][5]))
	aff_6.append(mean(affiliation_data[aff][6]))
	print aff, len(affiliation_data[aff][6])
	if len(affiliation_data[aff][6])<5:
		aff_col.append(0.5)
	else:
		aff_col.append(1)


barnames = ["Service", "Quality", "Importance", "User fee", "Used for more than one project", "Would use again", "SciLifeLab Impact"]

for i, bar in enumerate([aff_0, aff_1, aff_2, aff_3, aff_4, aff_5, aff_6]):
	aff_traces.append(go.Bar(
		x=aff_names,
		y=bar,
		text=bar,
		name=barnames[i],
		textposition = 'auto',
		marker = dict(
			# color = 'rgb(17, 157, 255)',
			opacity = aff_col,
			line = dict(
				# color = 'rgb(231, 99, 250)',
				width = 2
			)
		),
	))
layout = go.Layout(
	xaxis=dict(tickangle=-45),
	barmode='group',
	margin=go.layout.Margin(
		l=150,
		r=150,
		b=200,
		t=100,
		pad=4
	),
)
config={'showLink': False, "displayModeBar":False}
fig = go.Figure(data=aff_traces, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/aff_bars.html", config=config)
exit()
global_means = [mean(all_service), mean(all_quality), mean(all_importance), mean(all_fee), mean(all_morethanone), mean(all_again)]


trace = go.Scatter(
	x= correlation_data[6],
	y= correlation_data[0],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[2]
)

layout = go.Layout(
	title = "scatter service",
	showlegend=False,
	margin=go.layout.Margin(
		l=100,
		r=100,
		b=200,
		t=100,
		pad=4
	),
	yaxis = dict(
		title = "Service score",
		dtick = 1,
	),
	xaxis = dict(
		title = "SciLifeLab impact score"
	),
	hovermode='closest',
)

data = [trace]
fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/scatter_service.html")

trace = go.Scatter(
	x= correlation_data[6],
	y= correlation_data[1],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[7]
)

layout = go.Layout(
	title = "scatter quality",
	showlegend=False,
	margin=go.layout.Margin(
		l=100,
		r=100,
		b=200,
		t=100,
		pad=4
	),
	yaxis = dict(
		title = "Quality score",
		dtick = 1,
	),
	xaxis = dict(
		title = "SciLifeLab impact score"
	),
	hovermode='closest',
)

data = [trace]
fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/scatter_quality.html")

trace = go.Scatter(
	x= correlation_data[6],
	y= correlation_data[2],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[7]
)

layout = go.Layout(
	title = "scatter importance",
	showlegend=False,
	margin=go.layout.Margin(
		l=100,
		r=100,
		b=200,
		t=100,
		pad=4
	),
	yaxis = dict(
		title = "Importance score",
		dtick = 1,
	),
	xaxis = dict(
		title = "SciLifeLab impact score"
	),
	hovermode='closest',
)

data = [trace]
fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/scatter_importance.html")

trace = go.Scatter(
	x= correlation_data[6],
	y= correlation_data[3],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[7]
)

layout = go.Layout(
	title = "scatter user fee",
	showlegend=False,
	margin=go.layout.Margin(
		l=100,
		r=100,
		b=200,
		t=100,
		pad=4
	),
	yaxis = dict(
		title = "user fee score",
		dtick = 1,
	),
	xaxis = dict(
		title = "SciLifeLab impact score"
	),
	hovermode='closest',
)

data = [trace]
fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/scatter_userfee.html")

trace = go.Scatter(
	x= correlation_data[6],
	y= correlation_data[4],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[7]
)

layout = go.Layout(
	title = "scatter more than one project?",
	showlegend=False,
	margin=go.layout.Margin(
		l=100,
		r=100,
		b=200,
		t=100,
		pad=4
	),
	yaxis = dict(
		title = "more than one project? score",
		dtick = 1,
	),
	xaxis = dict(
		title = "SciLifeLab impact score"
	),
	hovermode='closest',
)

data = [trace]
fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/scatter_morethanone.html")

trace = go.Scatter(
	x= correlation_data[6],
	y= correlation_data[5],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[7]
)

layout = go.Layout(
	title = "scatter use again?",
	showlegend=False,
	margin=go.layout.Margin(
		l=100,
		r=100,
		b=200,
		t=100,
		pad=4
	),
	yaxis = dict(
		title = "Use again? score",
		dtick = 1,
	),
	xaxis = dict(
		title = "SciLifeLab impact score"
	),
	hovermode='closest',
)

data = [trace]
fig = go.Figure(data=data, layout=layout)
plotly.offline.plot(fig, filename="user_survey_plots/scatter_useagain.html")

for i, plot_name in enumerate(["Service", "Quality", "Importance", "User fee", "Used for more than one project", "Would use again"]):

	data = list()
	data_pre = list()
	data_means = list()
	data_means_pre = list()

	list_of_means = list()

	for key in survey_data.keys():
		if len(survey_data[key][i])>=5:
			colour = 'rgb(8,81,156)'
		else:
			colour = 'rgb(255,81,56)'
		data_pre.append([go.Box(
			y = survey_data[key][i],
			name = key,
			boxpoints = 'outliers',
			jitter = 1,
			marker = dict(
				color = colour,
				outliercolor = 'rgba(219, 64, 82, 0.6)',
				line = dict(
					outliercolor = 'rgba(219, 64, 82, 0.6)',
					outlierwidth = 2)),
			line = dict(
				color = colour)
		),mean(survey_data[key][i])])

		list_of_means.append(mean(survey_data[key][i]))

		data_means_pre.append([mean(survey_data[key][i]),key,mean(survey_data[key][i]), colour])

	mean_of_means = mean(list_of_means)

	data_pre = sorted(data_pre, key = lambda x: x[1])
	data_means_pre = sorted(data_means_pre, key = lambda x: x[2])

	data_means_values = list()
	data_means_labels = list()
	data_means_colours = list()
	data_means_values_mean_of_means = list()

	for trace in data_pre:
		data.append(trace[0])
	for trace in data_means_pre:
		data_means_values.append(trace[0] - global_means[i])
		data_means_values_mean_of_means.append(trace[0] - mean_of_means)
		data_means_labels.append(trace[1])
		data_means_colours.append(trace[3])

	data_means = [go.Bar(
		x = data_means_labels,
		y = data_means_values,
		marker = dict(
			color = data_means_colours
		)
	)]
	data_mean_of_means = [go.Bar(
		x = data_means_labels,
		y = data_means_values_mean_of_means,
		marker = dict(
			color = data_means_colours
		)
	)]

	layout = go.Layout(
		title = plot_name,
		showlegend=False,
		margin=go.layout.Margin(
			l=100,
			r=100,
			b=200,
			t=100,
			pad=4
		),
		yaxis = dict(
			dtick = 1,
		)
	)
	layout_means = go.Layout(
		title = plot_name,
		showlegend=False,
		margin=go.layout.Margin(
			l=100,
			r=100,
			b=200,
			t=100,
			pad=4
		),
		yaxis = dict(
			range=[-1,1]
		)
	)

	fig = go.Figure(data=data, layout=layout)

	config={'showLink': False, "displayModeBar":False}
	# plotly.offline.plot(fig, filename="user_survey_plots/"+plot_name.replace(" ", "_")+".html", config=config)

	fig_means = go.Figure(data=data_means, layout=layout_means)

	# plotly.offline.plot(fig_means, filename="user_survey_plots/"+plot_name.replace(" ", "_")+"_means.html", config=config)

	fig_mean_of_means = go.Figure(data=data_mean_of_means, layout=layout_means)

	plotly.offline.plot(fig_mean_of_means, filename="user_survey_plots/"+plot_name.replace(" ", "_")+"_mean_of_means.html", config=config)