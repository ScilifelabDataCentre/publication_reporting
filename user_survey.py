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
	aff_0.append(round(mean(affiliation_data[aff][0]), 2))
	aff_1.append(round(mean(affiliation_data[aff][1]), 2))
	aff_2.append(round(mean(affiliation_data[aff][2]), 2))
	aff_3.append(round(mean(affiliation_data[aff][3]), 2))
	aff_4.append(round(mean(affiliation_data[aff][4]), 2))
	aff_5.append(round(mean(affiliation_data[aff][5]), 2))
	aff_6.append(round(mean(affiliation_data[aff][6]), 2))
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
		yaxis="y2"
	))

fig = plotly.tools.make_subplots(rows=4, cols=2,vertical_spacing = 0.15)
fig.append_trace(aff_traces[0], 1, 1)
fig.append_trace(aff_traces[1], 1, 2)
fig.append_trace(aff_traces[2], 2, 1)
fig.append_trace(aff_traces[3], 2, 2)
fig.append_trace(aff_traces[4], 3, 1)
fig.append_trace(aff_traces[5], 3, 2)
fig.append_trace(aff_traces[6], 4, 1)
fig['layout'].update(margin=go.layout.Margin(l=100,r=250,b=200,t=100,pad=4),width=2000,height=1200,title="Scores by affiliation")
fig['layout']['yaxis'].update(range=[1, 5])
fig['layout']['yaxis2'].update(range=[1, 5])
fig['layout']['yaxis3'].update(range=[1, 5])
fig['layout']['yaxis4'].update(range=[1, 5])
fig['layout']['yaxis5'].update(range=[0, 1])
fig['layout']['yaxis6'].update(range=[0, 1])
fig['layout']['yaxis7'].update(range=[1, 5])
config={'showLink': False, "displayModeBar":False}
# fig = go.Figure(data=aff_traces, layout=layout)
# plotly.offline.plot(fig, filename="user_survey_plots/aff_bars.html", config=config)

plotly.io.write_image(fig, "user_survey_plots/aff_bars.png")

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
# plotly.offline.plot(fig, filename="user_survey_plots/scatter_service.html")

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
# plotly.offline.plot(fig, filename="user_survey_plots/scatter_quality.html")

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
# plotly.offline.plot(fig, filename="user_survey_plots/scatter_importance.html")

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
# plotly.offline.plot(fig, filename="user_survey_plots/scatter_userfee.html")

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
# plotly.offline.plot(fig, filename="user_survey_plots/scatter_morethanone.html")

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
# plotly.offline.plot(fig, filename="user_survey_plots/scatter_useagain.html")
plot_file_names = ["general", "service", "importance", "user_fee", "several_projects", "use_again"]
for i, plot_name in enumerate([
		"What is your general impression of the facility with regards to service-mindedness keeping of timelines and communication?<br>(1 Poor, 5 Excellent)", 
		"How do you rate the quality and scientific level of services technologies and data provided by the facility?<br>(1 Poor, 5 Excellent)", 
		"How do you rate the importance of access to the facility services for your research project?<br>(1 Low importance, 5 High importance)", 
		"How did you experience the user fee level at the facility?<br>(1 Low, 3 Fair, 5 High)", 
		"Have you used the facility for more than one project?<br>(Yes/No)", 
		"Would you consider using the facility in future research projects?<br>(Yes/No)"]):

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

		data_means_pre.append([mean(survey_data[key][i]),key,mean(survey_data[key][i]), colour, len(survey_data[key][i])])

	mean_of_means = mean(list_of_means)

	data_pre = sorted(data_pre, key = lambda x: x[1])
	data_means_pre = sorted(data_means_pre, key = lambda x: x[2])

	data_means_values = list()
	data_means_labels = list()
	data_means_colours = list()
	data_means_values_mean_of_means = list()
	list_of_num_responses = list()

	for trace in data_pre:
		data.append(trace[0])
	for trace in data_means_pre:
		# data_means_values.append(trace[0])
		data_means_values_mean_of_means.append(round(trace[0], 2))
		data_means_labels.append(trace[1])
		data_means_colours.append(trace[3])
		list_of_num_responses.append(trace[4])

	if max(data_means_values_mean_of_means) > 1:
		data_mean_of_means = [
			go.Bar(
				x = data_means_labels,
				y = data_means_values_mean_of_means,
				marker = dict(
					color = data_means_colours
				),
				text=["{}<br>({})".format(data_means_values_mean_of_means[j], list_of_num_responses[j]) for j in range(len(data_means_values_mean_of_means))],
				textposition = 'auto',
				name="Facility mean"
			),
			go.Scatter(
				x = data_means_labels,
				y = [mean_of_means]*len(data_means_labels),
				mode = 'lines',
				name = 'Mean of means'
			)
		]
		layout_means = go.Layout(
			title = plot_name,
			showlegend=False,
			margin=go.layout.Margin(
				l=200,
				r=200,
				b=200,
				t=100,
				pad=10
			),
			yaxis=go.layout.YAxis(
				title="Mean score, N user replies in parentheses",
				ticktext=["1", "3", "Average: "+str(round(mean_of_means, 2)), "5"],
				tickvals=[1, 3, mean_of_means, 5],
				range=[1,5]
			),
			width=2300,
			height=1000
		)
	else:
		data_mean_of_means = [
			go.Bar(
				x = data_means_labels,
				y = [x*100 for x in data_means_values_mean_of_means],
				marker = dict(
					color = data_means_colours
				),
				text=["{}%<br>({})".format(100*data_means_values_mean_of_means[j], list_of_num_responses[j]) for j in range(len(data_means_values_mean_of_means))],
				textposition = 'auto',
				name="Facility mean"
			),
			go.Scatter(
				x = data_means_labels,
				y = [mean_of_means*100]*len(data_means_labels),
				mode = 'lines',
				name = 'Mean of means'
			)
		]
		layout_means = go.Layout(
			title = plot_name,
			showlegend=False,
			margin=go.layout.Margin(
				l=200,
				r=200,
				b=200,
				t=100,
				pad=10
			),
			yaxis=go.layout.YAxis(
				title="Percent Yes answers",
				ticktext=["0", "Average: {}%".format(round(mean_of_means, 2)*100), "100"],
				tickvals=[0, mean_of_means*100, 100],
				range=[0,100],
				dtick=0.25
			),
			width=2300,
			height=1000
		)		

	# fig = go.Figure(data=data, layout=layout)

	# config={'showLink': False, "displayModeBar":False}
	# # plotly.offline.plot(fig, filename="user_survey_plots/"+plot_name.replace(" ", "_")+".html", config=config)

	# fig_means = go.Figure(data=data_means, layout=layout_means)

	# plotly.offline.plot(fig_means, filename="user_survey_plots/"+plot_name.replace(" ", "_")+"_means.html", config=config)

	fig_mean_of_means = go.Figure(data=data_mean_of_means, layout=layout_means)
	plotly.io.write_image(fig_mean_of_means, "user_survey_plots/"+plot_file_names[i]+".png")
	# plotly.offline.plot(fig_mean_of_means, filename="user_survey_plots/"+plot_file_names[i]+".html", config=config)