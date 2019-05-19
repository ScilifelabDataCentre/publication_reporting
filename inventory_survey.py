#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import os
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

def header(canvas, doc, content):
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
	canvas.drawString(150, 65, "Technology Needs Inventory")

def generatePdf(user_responses):
	doc = BaseDocTemplate(u"user_survey_plots/Technology_Needs_Inventory{}.pdf".format(user_responses["01_id"].lower().replace(" ", "_")),
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
	
	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-18*mm, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-18*mm, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	
	header_content = Paragraph(
		u'<b>{} {}</b><br/><font name=Frutiger-45-Light size=12> {}</font>'.format(user_responses["02_name"], user_responses["04_email"], user_responses["03_position"]), 
		styles["onepager_title"])
	footer_content = Paragraph(
		u'<b>{}</b>'.format("Technology Needs Inventory"), 
		styles["onepager_text"])

	header_item = PageTemplate(id='test', frames=[frame1,frame2], onPage=partial(header, content=header_content))
	doc.addPageTemplates([header_item])
	
	Story = []

	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>Affiliation:</b></font>", styles["onepager_inner_heading"]))
	for affiliation in user_responses["05_affiliation"].split(";"):
		Story.append(Paragraph(u"{}".format(affiliation), 
			styles["onepager_text"]))

	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>I have previously used these platforms at SciLifeLab:</b></font>", styles["onepager_inner_heading"]))
	for platform in user_responses["06_prev_platforms"].split(";"):
		Story.append(Paragraph(u"{}".format(platform), 
			styles["onepager_text"]))

	if user_responses["08_representing"]:
		Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>I propose a technology/service:</b></font>", styles["onepager_inner_heading"]))
		Story.append(Paragraph(u"{}".format(user_responses["07_propose"].replace("(specify  below)", "(specified below)")), 
			styles["onepager_text"]))
		Story.append(Paragraph(u"{}".format(user_responses["08_representing"]), 
			styles["onepager_text"]))	
	else:
		Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>I propose a technology/service:</b></font>", styles["onepager_inner_heading"]))
		Story.append(Paragraph(u"{}".format(user_responses["07_propose"]), 
			styles["onepager_text"]))


	
	# print user_responses["09_description"].split("\n")
	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>Give a brief description of the technology/service suggested. Specify what makes it nationally unique and the added value for academic researchers, healthcare and industry.</b></font>", styles["onepager_inner_heading"]))
	for para in user_responses["09_description"].split("\n"):
		Story.append(Paragraph(u"{}".format(para), 
			styles["onepager_text"]))	
	
	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>In which of the existing SciLifeLab Platforms would the technology/service fit?</b></font>", styles["onepager_inner_heading"]))
	for platform in user_responses["10_platform_fit"].split(";"):
		Story.append(Paragraph(u"{}".format(platform), 
			styles["onepager_text"]))
	
	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>Estimate the number of annual users of the technology if incorporated into the SciLifeLab infrastructure and offering nation-wide service (1-10, 10-100, more than 100, Don't know):</b></font>", styles["onepager_inner_heading"]))
	Story.append(Paragraph(u"{}".format(user_responses["11_num_users"]), 
		styles["onepager_text"]))
	
	# print user_responses["12_additional_comments"].split("\n")
	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>Additional comments:	</b></font>", styles["onepager_inner_heading"]))
	for para in user_responses["12_additional_comments"].split("\n"):
		Story.append(Paragraph(u"{}".format(para), 
			styles["onepager_text"]))	

	# Story.append(HRFlowable(width="40%", thickness=0.5, lineCap='round', color="#999999", spaceBefore=1, spaceAfter=1, hAlign='LEFT', vAlign='BOTTOM', dash=None))


	#print Story
	doc.build(Story)

if __name__ == "__main__":

	responses_file = 'user_survey_data/responses.xlsx'

	# Load spreadsheets
	responses_xl = pd.ExcelFile(responses_file)

	responses_df = responses_xl.parse(responses_xl.sheet_names[0])

	responses_data = dict()

	for i, row in responses_df.iterrows():
		responses_data[i] = dict()

		responses_data[i]["01_id"] = unicode(row[0] if isinstance(row[0], basestring) else "")
		responses_data[i]["02_name"] = unicode(row[1] if isinstance(row[1], basestring) else "")
		responses_data[i]["03_position"] = unicode(row[2] if isinstance(row[2], basestring) else "")
		responses_data[i]["04_email"] = unicode(row[3] if isinstance(row[3], basestring) else "")
		responses_data[i]["05_affiliation"] = u";".join([x for x in list(row[4:30]) if isinstance(x, basestring)])
		responses_data[i]["06_prev_platforms"] = u";".join([x for x in list(row[30:38]) if isinstance(x, basestring)])
		responses_data[i]["07_propose"] = unicode(row[38] if isinstance(row[38], basestring) else "")
		responses_data[i]["08_representing"] = unicode(row[39] if isinstance(row[39], basestring) else "")
		responses_data[i]["09_description"] = unicode(row[40] if isinstance(row[40], basestring) else "")
		responses_data[i]["10_platform_fit"] = u";".join([x for x in list(row[41:50]) if isinstance(x, basestring)])
		responses_data[i]["11_num_users"] = unicode(row[50] if isinstance(row[50], basestring) else "")
		responses_data[i]["12_additional_comments"] = unicode(row[51] if isinstance(row[51], basestring) else "")
		responses_data[i]["13_start_date"] = unicode(row[52] if isinstance(row[52], basestring) else "")
		responses_data[i]["14_submit_date"] = unicode(row[53] if isinstance(row[53], basestring) else "")
		responses_data[i]["15_network_id"] = unicode(row[54] if isinstance(row[54], basestring) else "")

	workbook = xlsxwriter.Workbook('user_survey_data/responses_parsed.xlsx')
	worksheet_data = workbook.add_worksheet("Data")
	bold = workbook.add_format({'bold': True})

	for row, user in enumerate(sorted(responses_data.keys()), 1):
		for col, item in enumerate(sorted(responses_data[user].keys()), 0):
			if row == 1:
				worksheet_data.write(0, col, item[3:], bold)
			worksheet_data.write(row, col, responses_data[user][item])

	workbook.close()

	for user_responses in responses_data.keys():
		generatePdf(responses_data[user_responses])

