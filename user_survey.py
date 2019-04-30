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

for i, plot_name in enumerate(["Service", "Quality", "Importance", "User fee", "Used for more than one project", "Would use again"]):

	data = list()
	data_pre = list()
	# data_vio_pre = list()
	# data_vio = list()

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

		# data_vio_pre.append([{
		# 	"type": 'violin',
		# 	"y": survey_data[key][i],
		# 	"name": key,
		# 	"box": {
		# 		"visible": True
		# 	},
		# 	"meanline": {
		# 		"visible": True
		# 	},
		# 	"line": {
		# 		"color": colour
		# 	}
		# }, mean(survey_data[key][i])])


	data_pre = sorted(data_pre, key = lambda x: x[1])
	# data_vio = sorted(data_vio, key = lambda x: x[1])

	for trace in data_pre:
		data.append(trace[0])

	# for trace in data_vio_pre:
	# 	data_vio.append(trace[0])

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

	fig = go.Figure(data=data, layout=layout)

	config={'showLink': False, "displayModeBar":False}
	plotly.offline.plot(fig, filename="user_survey_plots/"+plot_name.replace(" ", "_")+".html", config=config)

	# fig = go.Figure(data=data_vio, layout=layout)

	# config={'showLink': False, "displayModeBar":False}
	# plotly.offline.plot(fig, filename=plot_name+"_vio.html", config=config)