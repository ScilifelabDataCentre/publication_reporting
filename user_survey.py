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

correlation_data = [[],[],[]]

with open("user_survey_data/user_survey_parsed.tsv", "r") as survey_file:
	first_line = survey_file.readline()
	for line in survey_file:
		# print line
		line_split = line.split("\t")
		# print line_split[3]
		survey_response = line_split[3].split(",")
		# print len(survey_response)

		for response in survey_response:
			response_split = response.rsplit("-", 1)
			response_values = response_split[1].split(":")
			if response_split[0] not in survey_data.keys():
				survey_data[response_split[0]] = [[],[],[],[],[],[]]

			# print response_values
			for i, response_list in enumerate(survey_data[response_split[0]]):
				response_list.append(int(response_values[i]))
			
			all_service.append(int(response_values[0]))
			all_quality.append(int(response_values[1]))
			all_importance.append(int(response_values[2]))
			all_fee.append(int(response_values[3]))
			all_morethanone.append(int(response_values[4]))
			all_again.append(int(response_values[5]))

			all_impact.append(int(line_split[4]))

			correlation_data[0].append(int(response_values[0])+random.uniform(-0.25, 0.25))
			correlation_data[1].append(int(line_split[4])+random.uniform(-0.25, 0.25))
			correlation_data[2].append(line_split[3])

			# print response_split[0], survey_data[response_split[0]]

global_means = [mean(all_service), mean(all_quality), mean(all_importance), mean(all_fee), mean(all_morethanone), mean(all_again)]

# print correlation_data

trace = go.Scatter(
	x= correlation_data[1],
	y= correlation_data[0],
	mode= 'markers',
	marker= dict(size= 14,
		line= dict(width=1),
		opacity=0.2
	),
	text= correlation_data[2]
)

layout = go.Layout(
	title = "correlate",
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
plotly.offline.plot(fig, filename="user_survey_plots/correlate_scatter.html")


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
	)

	fig = go.Figure(data=data, layout=layout)

	config={'showLink': False, "displayModeBar":False}
	# plotly.offline.plot(fig, filename="user_survey_plots/"+plot_name.replace(" ", "_")+".html", config=config)

	fig_means = go.Figure(data=data_means, layout=layout_means)

	plotly.offline.plot(fig_means, filename="user_survey_plots/"+plot_name.replace(" ", "_")+"_means.html", config=config)

	fig_mean_of_means = go.Figure(data=data_mean_of_means, layout=layout_means)

	plotly.offline.plot(fig_mean_of_means, filename="user_survey_plots/"+plot_name.replace(" ", "_")+"_mean_of_means.html", config=config)