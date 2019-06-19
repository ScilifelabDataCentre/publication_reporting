#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import os
import requests
from datetime import datetime
import pandas as pd
import xlsxwriter
import textwrap

# pdf generation
from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, Image, PageTemplate, Frame, CondPageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Plotting libs
import plotly
import plotly.graph_objs as go

# Specialty functions
from functools import partial # used to create header
from svglib.svglib import svg2rlg # used to import svg files

# Get the API key from file api_key.py
from api_key import INVENTORY_API_KEY

def header(canvas, doc, content, footer_string=""):
	canvas.saveState()
	w, h = content.wrap(doc.width-60*mm, doc.topMargin)
	content.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
	p = canvas.beginPath()
	p.moveTo(doc.leftMargin,doc.height + doc.topMargin - h - 2*mm)
	p.lineTo(doc.leftMargin+doc.width,doc.height + doc.topMargin - h - 2*mm)
	p.close()
	canvas.setLineWidth(0.5)
	canvas.setStrokeColor("#999999")
	canvas.drawPath(p, stroke=1)
	canvas.restoreState()
	if footer_string:
		canvas.drawString(30, 30, footer_string)

def generate_summary_pdf(summary_data, form_data, heading_colour="#0093BD"):
	
	title = "Summary of {}".format(form_data["title"])
	doc = BaseDocTemplate(u"user_survey_plots/summary_of_{}.pdf".format(title.lower().replace(" ", "_")),
		pagesize=A4,
		rightMargin=18*mm, leftMargin=18*mm,
		topMargin=16*mm, bottomMargin=16*mm, 
		showBoundary=0
	)

	pdfmetrics.registerFont(TTFont('MinionPro', 'MinionPro-Regular.ttf'))
	pdfmetrics.registerFont(TTFont('Frutiger-65-Bold', 'Frutiger-LT-Std-65-Bold.ttf'))
	pdfmetrics.registerFont(TTFont('Frutiger-45-Light', 'Frutiger-LT-Std-45-Light.ttf'))

	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(name="onepager_inner_heading", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=10, color="#FF00AA", leading=16, spaceAfter=0, spaceBefore=8))
	styles.add(ParagraphStyle(name="onepager_title", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=16, bold=0, color="#000000", leading=16, spaceBefore=0))
	styles.add(ParagraphStyle(name="onepager_text", parent=styles["Normal"], fontName="MinionPro", fontSize=10, bold=0, color="#000000", leading=14))

	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	
	header_content = Paragraph(
		u'<b>{}</b>'.format(title), 
		styles["onepager_title"])

	header_item = PageTemplate(id='inventory_survey', frames=[frame1,frame2], onPage=partial(header, content=header_content))
	
	doc.addPageTemplates([header_item])

	Story = []

	for q in form_data["fields"]:
		if q["ref"] in summary_data.keys():
			Story.append(Paragraph(u"<font color='{}' name=Frutiger-65-Bold><b>{}</b></font>".format(heading_colour, q["title"].replace("*", "")),
				styles["onepager_inner_heading"]))
			
			labels = list()
			values = list()
			for choice in q["properties"]["choices"]:
				labels.append(textwrap.fill(choice["label"], 50).replace("\n", "<br>"))
				values.append(0)
			for item in summary_data[q["ref"]]:
				try:
					values[labels.index(textwrap.fill(item, 50).replace("\n", "<br>"))] += 1
				except ValueError as e:
					print e
			data = [go.Bar(
				x = values,
				y = labels,
				orientation = "h"
			)]
			layout = go.Layout(
				margin = dict(
					r = 20,
					t = 20,
					b = 20,
					l = 200
				),
				xaxis = go.layout.XAxis(
					tick0 = 0,
					dtick = 1
				)
			)
			fig = go.Figure(data=data, layout=layout)
			plotly.io.write_image(fig, u'user_survey_plots/{}.svg'.format(q["ref"]))

			user_dist_filename = u'user_survey_plots/{}.svg'.format(q["ref"])

			if os.path.isfile(user_dist_filename):
				user_dist_image  = svg2rlg(user_dist_filename)

				#Scaling the svg files
				tmp_width = 83
				tmp_height = 60

				scaling_factor = tmp_width*mm/user_dist_image.width

				user_dist_image.width = tmp_width*mm
				user_dist_image.height = tmp_height*mm
				user_dist_image.scale(scaling_factor, scaling_factor)
				Story.append(Spacer(1, 3*mm))
				Story.append(user_dist_image)
			Story.append(CondPageBreak(60*mm))
	
	doc.build(Story)

# def generate_summary_pdf_vertical(summary_data, form_data, heading_colour="#0093BD"):
	
# 	title = "Summary of {}".format(form_data["title"])
# 	doc = BaseDocTemplate(u"user_survey_plots/summary_of_{}_vertical.pdf".format(title.lower().replace(" ", "_")),
# 		pagesize=A4,
# 		rightMargin=18*mm, leftMargin=18*mm,
# 		topMargin=16*mm, bottomMargin=16*mm, 
# 		showBoundary=0
# 	)

# 	pdfmetrics.registerFont(TTFont('MinionPro', 'MinionPro-Regular.ttf'))
# 	pdfmetrics.registerFont(TTFont('Frutiger-65-Bold', 'Frutiger-LT-Std-65-Bold.ttf'))
# 	pdfmetrics.registerFont(TTFont('Frutiger-45-Light', 'Frutiger-LT-Std-45-Light.ttf'))

# 	styles = getSampleStyleSheet()
# 	styles.add(ParagraphStyle(name="onepager_inner_heading", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=10, color="#FF00AA", leading=16, spaceAfter=0, spaceBefore=8))
# 	styles.add(ParagraphStyle(name="onepager_title", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=16, bold=0, color="#000000", leading=16, spaceBefore=0))
# 	styles.add(ParagraphStyle(name="onepager_text", parent=styles["Normal"], fontName="MinionPro", fontSize=10, bold=0, color="#000000", leading=14))

# 	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
# 	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	
# 	header_content = Paragraph(
# 		u'<b>{}</b>'.format(title), 
# 		styles["onepager_title"])

# 	header_item = PageTemplate(id='inventory_survey', frames=[frame1,frame2], onPage=partial(header, content=header_content))
	
# 	doc.addPageTemplates([header_item])

# 	Story = []

# 	for q in form_data["fields"]:
# 		if q["ref"] in summary_data.keys():
# 			Story.append(Paragraph(u"<font color='{}' name=Frutiger-65-Bold><b>{}</b></font>".format(heading_colour, q["title"].replace("*", "")),
# 				styles["onepager_inner_heading"]))
			
# 			labels = list()
# 			values = list()
# 			for choice in q["properties"]["choices"]:
# 				labels.append(textwrap.fill(choice["label"], 50).replace("\n", "<br>"))
# 				values.append(0)
# 			for item in summary_data[q["ref"]]:
# 				try:
# 					values[labels.index(textwrap.fill(item, 50).replace("\n", "<br>"))] += 1
# 				except ValueError as e:
# 					print e
# 			data = [go.Bar(
# 				y = values,
# 				x = labels,
# 			)]
# 			layout = go.Layout(
# 				margin = dict(
# 					r = 200,
# 					t = 20,
# 					b = 200,
# 					l = 20
# 				),
# 				yaxis = go.layout.YAxis(
# 					tick0 = 0,
# 					dtick = 1
# 				),
# 				xaxis=dict(
# 					tickangle = 45
# 				)
# 			)
# 			fig = go.Figure(data=data, layout=layout)
# 			plotly.io.write_image(fig, u'user_survey_plots/{}.svg'.format(q["ref"]))

# 			user_dist_filename = u'user_survey_plots/{}.svg'.format(q["ref"])

# 			if os.path.isfile(user_dist_filename):
# 				user_dist_image  = svg2rlg(user_dist_filename)

# 				#Scaling the svg files
# 				tmp_width = 83
# 				tmp_height = 60

# 				scaling_factor = tmp_width*mm/user_dist_image.width

# 				user_dist_image.width = tmp_width*mm
# 				user_dist_image.height = tmp_height*mm
# 				user_dist_image.scale(scaling_factor, scaling_factor)
# 				Story.append(Spacer(1, 3*mm))
# 				Story.append(user_dist_image)
# 			Story.append(CondPageBreak(60*mm))
	
# 	doc.build(Story)


def generate_pdf(user_id, response, form_data, index, additional_data, heading_colour="#0093BD"):
	# print form_data
	title = form_data["title"]
	doc = BaseDocTemplate(u"user_survey_plots/{}_{}{}.pdf".format(title.lower().replace(" ", "_"), additional_data[1], index),
		pagesize=A4,
		rightMargin=18*mm, leftMargin=18*mm,
		topMargin=16*mm, bottomMargin=16*mm, 
		showBoundary=0
	)

	pdfmetrics.registerFont(TTFont('MinionPro', 'MinionPro-Regular.ttf'))
	pdfmetrics.registerFont(TTFont('MinionPro-Italic', 'MinionPro-It.ttf'))
	pdfmetrics.registerFont(TTFont('Frutiger-65-Bold', 'Frutiger-LT-Std-65-Bold.ttf'))
	pdfmetrics.registerFont(TTFont('Frutiger-45-Light', 'Frutiger-LT-Std-45-Light.ttf'))

	styles = getSampleStyleSheet()
	styles.add(ParagraphStyle(name="onepager_inner_heading", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=10, color="#FF00AA", leading=16, spaceAfter=0, spaceBefore=8))
	styles.add(ParagraphStyle(name="onepager_title", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=16, bold=0, color="#000000", leading=16, spaceBefore=0))
	styles.add(ParagraphStyle(name="onepager_text", parent=styles["Normal"], fontName="MinionPro", fontSize=10, bold=0, color="#000000", leading=14))
	styles.add(ParagraphStyle(name="onepager_text_ita", parent=styles["Normal"], fontName="MinionPro-Italic", fontSize=10, bold=0, color="#000000", leading=14))
	styles.add(ParagraphStyle(name="onepager_inner_heading_indent", parent=styles["Heading1"], fontName="Frutiger-65-Bold", fontSize=10, color="#FF00AA", leading=16, spaceAfter=0, spaceBefore=8, leftIndent=20))
	styles.add(ParagraphStyle(name="onepager_text_indent", parent=styles["Normal"], fontName="MinionPro", fontSize=10, bold=0, color="#000000", leading=14, leftIndent=20))
	styles.add(ParagraphStyle(name="onepager_text_indent_ita", parent=styles["Normal"], fontName="MinionPro-Italic", fontSize=10, bold=0, color="#000000", leading=14, leftIndent=20))
 
	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)

	tech_name_response = ""
	name_response = ""
	email_response = ""
	position_response = ""

	shown_responses = {}
	maybe_show_pos = {}

	for q_response in response:
		if q_response["field"]["ref"] == additional_data[2]:
			tech_name_response = q_response["text"]
		elif q_response["field"]["ref"] == additional_data[3]:
			name_response = q_response["text"]
		elif q_response["field"]["ref"] == additional_data[4]:
			position_response = q_response["text"]
			maybe_show_pos[q_response["field"]["ref"]] = q_response
		elif q_response["field"]["ref"] == additional_data[5]:
			email_response = q_response["email"]
		else:
			shown_responses[q_response["field"]["ref"]] = q_response

	if tech_name_response == "":
		if additional_data[1] == "A":
			tech_name_response = additional_data[6][index]
		else:
			tech_name_response = "Placeholder"

	thing = u'<b>{}</b><br/><font name=Frutiger-45-Light size=12>{}, {}</font><br/><font name=MinionPro-Italic size=10>{}</font>'.format(tech_name_response.replace('&', '&amp;'),name_response.replace('&', '&amp;'),position_response.replace('&', '&amp;'),email_response)

	header_content = Paragraph(
		u'<b>{}</b><br/><font name=Frutiger-45-Light size=12>{}, {}</font><br/><font name=MinionPro-Italic size=10>{}</font>'.format(tech_name_response.replace('&', '&amp;'),name_response.replace('&', '&amp;'),position_response.replace('&', '&amp;'),email_response), 
		styles["onepager_title"])

	w, h = header_content.wrap(doc.width-60*mm, doc.topMargin)

	top_margin_offset = 0
	if h > 48:
		top_margin_offset = h - 48

	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm-top_margin_offset, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm-top_margin_offset, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)

	footer_string = "{} Reg No - {}{}".format(title, additional_data[1], index)
	
	header_item = PageTemplate(id='inventory_survey', frames=[frame1,frame2], onPage=partial(header, content=header_content, footer_string=footer_string))
	doc.addPageTemplates([header_item])

	Story = list()

	# logic = dict()
	indents = list()
	for log in form_data["logic"]:
		for action in log["actions"]:
			if action["condition"]["op"] != u"always":
				indents.append(action["details"]["to"]["value"])

	for q in form_data["fields"]:
		if q["ref"] in shown_responses.keys():
			if q["ref"] in indents:
				indent_styles = [styles["onepager_inner_heading_indent"], styles["onepager_text_indent"], styles["onepager_text_indent_ita"]]
				Story.append(Spacer(1, 3*mm))
			else:
				indent_styles = [styles["onepager_inner_heading"], styles["onepager_text"], styles["onepager_text_ita"]]		
				Story.append(Paragraph(u"<font color='{}' name=Frutiger-65-Bold><b>{}</b></font>".format(heading_colour, q["title"].replace("*", "")),
					indent_styles[0]))
			if shown_responses[q["ref"]]["type"] == "choices":
				for choice in shown_responses[q["ref"]]["choices"]["labels"]:
					Story.append(Paragraph(u"<em>{}</em>".format(choice).replace('&', '&amp;'), 
						indent_styles[2]))
			elif shown_responses[q["ref"]]["type"] == "choice":
				if shown_responses[q["ref"]]["choice"]["label"] == u'Representing a group of scientists, a department, a university, a SciLifeLab committee, healthcare, industry etc. (specify  below)':
					Story.append(Paragraph(u"<em>Representing:</em>", 
						indent_styles[2]))
				else:
					Story.append(Paragraph(u"<em>{}</em>".format(shown_responses[q["ref"]]["choice"][shown_responses[q["ref"]]["choice"].keys()[0]]).replace('&', '&amp;'), 
						indent_styles[2]))
			elif shown_responses[q["ref"]]["type"] == "url":
				Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["url"]).replace('&', '&amp;'), 
					indent_styles[1]))
			elif shown_responses[q["ref"]]["type"] == "email":
				Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["email"]).replace('&', '&amp;'), 
					indent_styles[1]))
			else:
				try:
					Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["text"]).replace('&', '&amp;'), 
						indent_styles[1]))
				except KeyError as e:
					print shown_responses[q["ref"]]
			Story.append(CondPageBreak(30*mm))
	doc.build(Story)

def get_form(form_id, api_key, raise_error=True):
	base_url = "https://api.typeform.com/forms/"
	form_url = "{}{}".format(base_url, form_id)
	api_headers = {'Authorization': "Bearer {}".format(api_key)}
	resp = requests.get(form_url, headers=api_headers)
		
	if resp.status_code != 200:
		if raise_error:
			resp.raise_for_status()
		else:
			return {}
	
	return resp.json()
def get_responses(form_id, api_key, raise_error=True):
	base_url = "https://api.typeform.com/forms/"
	reponses_url = "{}{}/responses".format(base_url, form_id)
	api_headers = {'Authorization': "Bearer {}".format(api_key)}
	resp = requests.get(reponses_url, headers=api_headers)
		
	if resp.status_code != 200:
		if raise_error:
			resp.raise_for_status()
		else:
			return {}
	
	return resp.json()
	
if __name__ == "__main__":

	placeholder_tech_names = {
		1:"BioNano Genomics Saphyre system",
		2:"Service for Earth Biogenome Project / BGISeq",
		3:"Ancient DNA genome seq / Paleoproteomics",
		4:"Celsee system for single-cell transcriptomics",
		5:"Advanced Fluorescence Micoroscopy",
		6:"smFISH",
		7:"High-speed Camera for ALM Facility",
		8:"Imaging Mass Cytometry",
		9:"CUT&RUN",
		10:"eCLIP, XRNAX, PRIDE-seq",
		11:"smFISH, MERFISH, HCR and RNAscope",
		12:"Platform for Organoids",
		13:"STED-FCS",
		14:"SeqFISH, MerFISH"
	}
	additional_information = [
		"#95C11E",                              # colour
		"B",                                    # prefix
		"f3715e52-fe18-48e2-a064-d4b941c32b55", # name of tech
		"23cc0bc6-8ffb-4994-a569-0a24d64502b7", # name
		"2fcff9f3-9d5e-48e5-8268-5dc5725e170f", # position
		"e129e013-f85e-4a50-a987-fc31b0a6f938"  # email
	]
	additional_information2 = [
		"#0093BD",                              # colour
		"A",                                    # prefix
		"6b72ad82-ed01-4950-89b5-97796d0264d5", # name of tech
		"23cc0bc6-8ffb-4994-a569-0a24d64502b7", # name
		"2fcff9f3-9d5e-48e5-8268-5dc5725e170f", # position
		"e129e013-f85e-4a50-a987-fc31b0a6f938", # email
		placeholder_tech_names                  # names for technologies
		]
	form_ids = {"mu9Pmx": additional_information, "TKMJZS": additional_information2}

	for form_id in form_ids.keys():
		print form_id
		form_data = get_form(form_id, INVENTORY_API_KEY)
		response_data = get_responses(form_id, INVENTORY_API_KEY)

		responses = dict()
		for item in response_data["items"]:
			if "answers" in item.keys():
				if datetime.strptime(item["submitted_at"], "%Y-%m-%dT%H:%M:%SZ") > datetime.strptime("2019-05-17T00:00:01Z", "%Y-%m-%dT%H:%M:%SZ"):
					responses[datetime.strptime(item["submitted_at"], "%Y-%m-%dT%H:%M:%SZ")] = item["answers"]

		summary_responses = dict()
		for item in sorted(responses.keys()):
			for question in responses[item]:
				if question["field"]["type"] == "multiple_choice":
					if question["field"]["ref"] not in summary_responses.keys():
						summary_responses[question["field"]["ref"]] = list()
					if question["type"] == "choices":
						for choice in question["choices"]["labels"]:
							summary_responses[question["field"]["ref"]].append(choice)
					elif question["type"] == "choice":
						if "label" in question["choice"].keys():
							summary_responses[question["field"]["ref"]].append(question["choice"]["label"])
						else:
							summary_responses[question["field"]["ref"]].append("other")
					else:
						exit("ERROR"+str(question))

		generate_summary_pdf(summary_responses, form_data, heading_colour=form_ids[form_id][0])

		for i, user_id in enumerate(sorted(responses.keys()), 1):
			generate_pdf(user_id, responses[user_id], form_data, index=i, additional_data=form_ids[form_id], heading_colour=form_ids[form_id][0])


