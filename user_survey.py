#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

#Plotting libs
import plotly
import plotly.graph_objs as go

survey_data = dict()

def mean(numbers):
	return float(sum(numbers)) / max(len(numbers), 1)

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

			# print response_split[0], survey_data[response_split[0]]

print survey_data

for i, plot_name in enumerate(["general impression", "quality and scientific level of services", "importance of access", "user fee level", "more than one project", "future"]):

	data = list()
	data_pre = list()

	for key in survey_data.keys():
		if len(survey_data[key][i])>=5:
			colour = 'rgb(8,81,156)'
		else:
			colour = 'rgb(255,81,56)'
		data_pre.append([go.Box(
			y = survey_data[key][i],
			name = key,
			boxpoints = 'suspectedoutliers',
			marker = dict(
				color = colour,
				outliercolor = 'rgba(219, 64, 82, 0.6)',
				line = dict(
					outliercolor = 'rgba(219, 64, 82, 0.6)',
					outlierwidth = 2)),
			line = dict(
				color = colour)
		),mean(survey_data[key][i])])


	data_pre = sorted(data_pre, key = lambda x: x[1])

	for trace in data_pre:
		data.append(trace[0])

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
	)

	fig = go.Figure(data=data, layout=layout)

	config={'showLink': False, "displayModeBar":False}
	plotly.offline.plot(fig, filename=plot_name+".html", config=config)