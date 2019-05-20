#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import os
import requests
from datetime import datetime
import pandas as pd
import xlsxwriter

from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, Image, PageTemplate, Frame, CondPageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from functools import partial
from svglib.svglib import svg2rlg

from api_key import INVENTORY_API_KEY

def header(canvas, doc, content, footer_string):
	canvas.saveState()
	w, h = content.wrap(doc.width, doc.topMargin)
	content.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
	p = canvas.beginPath()
	p.moveTo(doc.leftMargin,doc.height + doc.topMargin - h - 2*mm)
	p.lineTo(doc.leftMargin+w,doc.height + doc.topMargin - h - 2*mm)
	p.close()
	canvas.setLineWidth(0.5)
	canvas.setStrokeColor("#999999")
	canvas.drawPath(p, stroke=1)
	canvas.restoreState()
	canvas.drawString(30, 30, footer_string)

def generate_pdf(user_id, response, form_data):
	# print form_data
	title = form_data["title"]
	doc = BaseDocTemplate(u"user_survey_plots/{}_{}.pdf".format(title.lower().replace(" ", "_"), user_id.lower().replace(" ", "_")),
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
	styles.add(ParagraphStyle(name="onepager_footnote", parent=styles["Normal"], fontName="MinionPro", fontSize=7, bold=0, color="#000000", leading=14))
	
	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-21*mm, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	# print "\n\n\n"
	name_question = None
	email_question = None
	position_question = None

	for question in form_data["fields"]:
		if name_question == None and "name" in question["title"].lower():
			name_question = question["ref"]
		if email_question == None and "email" in question["title"].lower():
			email_question = question["ref"]
		if position_question == None and "position" in question["title"].lower():
			position_question = question["ref"]

	name_response = ""
	email_response = ""
	position_response = ""

	shown_responses = {}

	for q_response in response:
		if q_response["field"]["ref"] == name_question:
			name_response = q_response["text"]
		elif q_response["field"]["ref"] == email_question:
			email_response = q_response["email"]
		elif q_response["field"]["ref"] == position_question:
			position_response = q_response["text"]
		else:
			shown_responses[q_response["field"]["ref"]] = q_response



	header_content = Paragraph(
		u'<b>{}</b><br/><font name=Frutiger-45-Light size=12>{}<br/>{}</font>'.format(name_response, email_response, position_response), 
		styles["onepager_title"])

	footer_string = title
	
	header_item = PageTemplate(id='inventory_survey', frames=[frame1,frame2], onPage=partial(header, content=header_content, footer_string=footer_string))
	doc.addPageTemplates([header_item])

	Story = []

	for q in form_data["fields"]:
		if q["ref"] in shown_responses.keys():
			Story.append(Paragraph(u"<font color='#95C11E' name=Frutiger-65-Bold><b>{}</b></font>".format(q["title"].replace("*", "")),
				styles["onepager_inner_heading"]))
			if shown_responses[q["ref"]]["type"] == "choices":
				for choice in shown_responses[q["ref"]]["choices"]["labels"]:
					Story.append(Paragraph(u"{}".format(choice), 
						styles["onepager_text"]))
			elif shown_responses[q["ref"]]["type"] == "choice":
				Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["choice"][shown_responses[q["ref"]]["choice"].keys()[0]]), 
					styles["onepager_text"]))
			elif shown_responses[q["ref"]]["type"] == "url":
				Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["url"]), 
					styles["onepager_text"]))
			elif shown_responses[q["ref"]]["type"] == "email":
				Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["email"]), 
					styles["onepager_text"]))
			else:
				try:
					Story.append(Paragraph(u"{}".format(shown_responses[q["ref"]]["text"]), 
						styles["onepager_text"]))
				except KeyError as e:
					print shown_responses[q["ref"]]
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

	response_data = get_responses("mu9Pmx", INVENTORY_API_KEY)
	responses = {}
	for item in response_data["items"]:
		if "answers" in item.keys():
			if datetime.strptime(item["submitted_at"], "%Y-%m-%dT%H:%M:%SZ") > datetime.strptime("2019-05-17T00:00:01Z", "%Y-%m-%dT%H:%M:%SZ"):
				responses[item["response_id"]] = item["answers"]

	form_data = get_form("mu9Pmx", INVENTORY_API_KEY)

	for user_id in responses.keys():
		generate_pdf(user_id, responses[user_id], form_data)


