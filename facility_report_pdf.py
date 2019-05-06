#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pandas as pd
import json
import urllib
import difflib
import xlsxwriter
import datetime

from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, Image, PageTemplate, Frame, CondPageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from functools import partial
from svglib.svglib import svg2rlg

from facility_report_plots import user_plot, publication_plot

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

def generatePdf(facility_name, reporting_data, current_year):

	print "\nFacility report {}: {}".format(current_year, facility_name.encode("utf-8"))
	cwd = os.getcwd()
	directory = cwd+"/facility_onepagers"
	if not os.path.exists(directory):
		os.makedirs(directory)

	doc = BaseDocTemplate(u"facility_onepagers/{}_{}.pdf".format(current_year, facility_name.lower().replace(" ", "_")),
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
		u'<b>{}</b><br/><font name=Frutiger-45-Light size=12> {} platform</font>'.format(facility_name.replace('&', '&amp;'), reporting_data["platform"]), 
		styles["onepager_title"])

	# print header_content

	template = PageTemplate(id='test', frames=[frame1,frame2], onPage=partial(header, content=header_content))
	doc.addPageTemplates([template])

	Story = []

	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>Basic information</b></font>", styles["onepager_inner_heading"]))

	directors = ""
	for director in eval(reporting_data["facility_director"]):
		if directors:
			directors += u', ' + u' '.join((director[0], director[1])).strip()
		else:
			directors = u' '.join((director[0], director[1])).strip()
	
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>Facility director: </b></font>{}".format(directors), 
		styles["onepager_text"]))

	heads = ""
	for head in eval(reporting_data["facility_head"]):
		if heads:
			heads += u', ' + u' '.join((head[0], head[1])).strip()
		else:
			heads = u' '.join((head[0], head[1])).strip()
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>Head of facility: </b></font>{}".format(heads), 
		styles["onepager_text"]))

	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>SciLifeLab facility since: </b></font>{}".format(reporting_data["national_scilifelab_facility_since"]), 
		styles["onepager_text"]))
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>Host university: </b></font>{}".format(reporting_data["host_university"]), 
		styles["onepager_text"]))
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>FTEs: </b></font>{}".format(reporting_data["fte"]), 
		styles["onepager_text"]))
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>FTEs financed by SciLifeLab: </b></font>{}".format(reporting_data["fte_scilifelab"]), 
		styles["onepager_text"]))

	Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Funding {} (in kSEK)</b></font></font>".format(current_year), 
		styles["onepager_inner_heading"]))
	
	total_funding = 0
	if "additional_funding" in reporting_data.keys():
		for funds in eval(reporting_data["additional_funding"]):
			try:
				if funds[1] != "User fees/invoicing":#DONT count user fees to funding
					total_funding += int(funds[2])
			except (ValueError, TypeError) as e:
				#If we cannot convert funds[1] to int, its probably not a number...
				print "WARNING: FUNDING ITEM NOT A NUMBER:", funds, facility_name
	
	try:
		total_funding += int(reporting_data["scilifelab_funding"])
	except ValueError as e:
		pass # NaN, ie no data in the cell

	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>SciLifeLab: </b></font>{}".format(reporting_data["scilifelab_funding"]), 
		styles["onepager_text"]))

	user_fees_flag = False
	user_fees_amount = None

	if "additional_funding" in reporting_data.keys():
		for funds in eval(reporting_data["additional_funding"]):
			try:
				funds_amount = int(funds[2])
			except (ValueError, TypeError) as e:
				funds_amount = "-"

			if funds[1] == "User fees/invoicing":
				user_fees_flag = True
				user_fees_amount = funds_amount
				continue

			if funds_amount == "-":
				Story.append(Paragraph("<font color='#FF0000' name=Frutiger-65-Bold><b>{}: </b></font>{}".format(funds[0].encode("utf-8"), funds_amount), 
					styles["onepager_text"]))
			else:
				Story.append(Paragraph("<font name=Frutiger-65-Bold><b>{}: </b></font>{}".format(funds[0].encode("utf-8"), funds_amount), 
					styles["onepager_text"]))

	Story.append(HRFlowable(width="40%", thickness=0.5, lineCap='round', color="#999999", spaceBefore=1, spaceAfter=1, hAlign='LEFT', vAlign='BOTTOM', dash=None))
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Total: </b></font>{}".format(total_funding), 
		styles["onepager_text"]))

	##RESOURCE ALLOCATION
	total_percentage = int(reporting_data["resource_academic_national"])+int(reporting_data["resource_academic_international"])+\
		int(reporting_data["resource_internal"])+int(reporting_data["resource_industry"])+\
		int(reporting_data["resource_healthcare"])+int(reporting_data["resource_other"])
	if total_percentage == 100:
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Resource allocation {}</b></font></font>".format(current_year), 
			styles["onepager_inner_heading"]))
	else:
		print "WARNING: PERCENTAGE DOES NOT ADD UP TO 100 IN RESOURCE_ALLOCATION FOR", facility_name, total_percentage
		Story.append(Paragraph("<font color='#FF0000'><font name=Frutiger-65-Bold><b>Resource allocation {}</b></font></font>".format(current_year), 
			styles["onepager_inner_heading"]))

	if reporting_data["resource_academic_national"]:
		tmp_input = "{}%".format(reporting_data["resource_academic_national"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Academia (national): </b></font>{}".format(tmp_input),
		styles["onepager_text"]))

	if reporting_data["resource_academic_international"]:
		tmp_input = "{}%".format(reporting_data["resource_academic_international"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Academia (international): </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	if reporting_data["resource_internal"]:
		tmp_input = "{}%".format(reporting_data["resource_internal"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Internal tech. dev.: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	if reporting_data["resource_industry"]:
		tmp_input = "{}%".format(reporting_data["resource_industry"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Industry: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	if reporting_data["resource_healthcare"]:
		tmp_input = "{}%".format(reporting_data["resource_healthcare"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Healthcare: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	if reporting_data["resource_other"]:
		tmp_input = "{}%".format(reporting_data["resource_other"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Other gov. agencies: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	##USER FEES
	total_percentage = reporting_data["cost_reagents"]+reporting_data["cost_instrument"]+\
		reporting_data["cost_salaries"]+reporting_data["cost_rents"]+reporting_data["cost_other"]
	if total_percentage == 100:
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>User Fees {}</b></font></font>".format(current_year), 
			styles["onepager_inner_heading"]))
	else:
		print "WARNING: PERCENTAGE DOES NOT ADD UP TO 100 IN COSTS FOR", facility_name, total_percentage
		Story.append(Paragraph("<font color='#FF0000'><font name=Frutiger-65-Bold><b>User Fees {}</b></font></font>".format(current_year), 
			styles["onepager_inner_heading"]))
	
	if user_fees_flag:
		Story.append(Paragraph("<font color='#000000' name=Frutiger-65-Bold><b>Total (kSEK): </b></font>{}".format(user_fees_amount), 
			styles["onepager_text"]))
	else:
		Story.append(Paragraph("<font color='#000000' name=Frutiger-65-Bold><b>Total (kSEK): </b></font>0", 
			styles["onepager_text"]))

	Story.append(HRFlowable(width="40%", thickness=0.5, lineCap='round', color="#999999", spaceBefore=1, spaceAfter=1, hAlign='LEFT', vAlign='BOTTOM', dash=None))

	if reporting_data["cost_reagents"]:
		tmp_input = "{}%".format(reporting_data["cost_reagents"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Reagents: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["cost_instrument"]:
		tmp_input = "{}%".format(reporting_data["cost_instrument"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Instrument: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["cost_salaries"]:
		tmp_input = "{}%".format(reporting_data["cost_salaries"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Salaries: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["cost_rents"]:
		tmp_input = "{}%".format(reporting_data["cost_rents"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Rent: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["cost_other"]:
		tmp_input = "{}%".format(reporting_data["cost_other"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Other: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	##USER FEES BY SECTOR
	total_percentage = reporting_data["user_fees_academic_sweden"]+reporting_data["user_fees_academic_international"]+\
		reporting_data["user_fees_industry"]+reporting_data["user_fees_healthcare"]+\
		reporting_data["user_fees_other"]
	if total_percentage == 100:
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>User fees by sector {}</b></font></font>".format(current_year), 
			styles["onepager_inner_heading"]))
	else:
		print "WARNING: PERCENTAGE DOES NOT ADD UP TO 100 IN USER FEES FOR", facility_name, total_percentage
		Story.append(Paragraph("<font color='#FF0000'><font name=Frutiger-65-Bold><b>User fees by sector {}</b></font></font>".format(current_year), 
			styles["onepager_inner_heading"]))

	if reporting_data["user_fees_academic_sweden"]:
		tmp_input = "{}%".format(reporting_data["user_fees_academic_sweden"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Academia (national): </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["user_fees_academic_international"]:
		tmp_input = "{}%".format(reporting_data["user_fees_academic_international"])
	else:
		tmp_input = "-"	
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Academia (international): </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["user_fees_industry"]:
		tmp_input = "{}%".format(reporting_data["user_fees_industry"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Industry: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))

	if reporting_data["user_fees_healthcare"]:
		tmp_input = "{}%".format(reporting_data["user_fees_healthcare"])
	else:
		tmp_input = "-"	
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Healthcare: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	if reporting_data["user_fees_other"]:
		tmp_input = "{}%".format(reporting_data["user_fees_other"])
	else:
		tmp_input = "-"
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Other gov. agencies: </b></font>{}".format(tmp_input), 
		styles["onepager_text"]))
	
	Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Services</b></font></font>", 
		styles["onepager_inner_heading"]))

	if isinstance(reporting_data["services_bullets"], basestring):
		bullet_points = reporting_data["services_bullets"].split("\n")
		for bullet in bullet_points:
			Story.append(Paragraph(bullet, styles["onepager_text"]))
	else:
		Story.append(Paragraph("Service information goes here, please input text in excel file", styles["onepager_text"]))
	
	##USERS
	Story.append(CondPageBreak(100*mm))

	Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Users {}</b></font></font>".format(current_year), 
		styles["onepager_inner_heading"]))

	# user_dist_filename = reporting_data["user_figure_name"]
	user_dist_filename = user_plot(eval(reporting_data["user_affiliation"]), facility_name)

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
	else:
		print "WARNING: NO USER PLOT FOR:", facility_name, user_dist_filename

	#PUBLICATIONS
	Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Publications</b></font></font>", 
		styles["onepager_inner_heading"]))

	if eval(reporting_data["database_label_names"]):
		pub_label_cat_filename, pub_label_jif_filename, pub_counts = publication_plot(eval(reporting_data["database_label_names"]), current_year)
	else:
		pub_label_cat_filename, pub_label_jif_filename, pub_counts = None, None, (0, 0, 0)

	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>{}: </b></font>{}".format(current_year-2, pub_counts[2]), 
		styles["onepager_text"]))
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>{}: </b></font>{}".format(current_year-1, pub_counts[1]), 
		styles["onepager_text"]))
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>{}: </b></font>{}".format(current_year, pub_counts[0]), 
		styles["onepager_text"]))

	if pub_label_cat_filename and pub_label_jif_filename and sum(pub_counts)>0:	 

		pub_label_cat_image = svg2rlg(pub_label_cat_filename)
		pub_label_jif_image = svg2rlg(pub_label_jif_filename)

		#print pub_label_cat_image_svg.width, pub_label_cat_image_svg.height, 87.5*mm, 62.5*mm
		#Scaling the svg files
		tmp_width = 83
		tmp_height = 60
		scaling_factor = tmp_width*mm/pub_label_cat_image.width

		pub_label_cat_image.width = tmp_width*mm
		pub_label_cat_image.height = tmp_height*mm
		pub_label_cat_image.scale(scaling_factor, scaling_factor)
		pub_label_jif_image.width = tmp_width*mm
		pub_label_jif_image.height = tmp_height*mm
		pub_label_jif_image.scale(scaling_factor, scaling_factor)

		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Publications by category</b></font></font>", 
			styles["onepager_inner_heading"]))
		Story.append(pub_label_cat_image)
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Publications by Journal Impact Factor</b></font></font>", 
			styles["onepager_inner_heading"]))
		Story.append(pub_label_jif_image)
	else:
		print "WARNING: NO PUB PLOTS FOR:", facility_name

	if isinstance(reporting_data["asterisk_footnote"], basestring):
		Story.append(Paragraph("* {}".format(reporting_data["asterisk_footnote"].encode("utf-8")), 
			styles["onepager_footnote"]))

	#print Story
	doc.build(Story)

if __name__ == "__main__":
	reporting_data = dict()
	garbage_data = dict()

	all_data_raw = open("fetched_facility_reports/all_reports_data.json", "r").read()
	all_data_dict = json.loads(all_data_raw)

	label_response = urllib.urlopen("https://publications.scilifelab.se/labels.json")
	labels = json.loads(label_response.read())
	labels_check_dict = dict()
	for label in labels["labels"]:
		labels_check_dict[label["value"]] = label["links"]["self"]["href"]

	for report in all_data_dict.keys():

		facility = all_data_dict[report]["facility"]
		report_id = all_data_dict[report]["id"]
		reporting_data[facility] = dict()
		garbage_data[facility] = dict()

		# Reporting data
		reporting_data[facility]["files"] = all_data_dict[report]["files"]
		
		reporting_data[facility]["fte"] = all_data_dict[report]["fte"]
		reporting_data[facility]["fte_scilifelab"] = all_data_dict[report]["fte_scilifelab"]

		reporting_data[facility]["resource_academic_national"] = all_data_dict[report]["resource_academic_national"]
		reporting_data[facility]["resource_academic_international"] = all_data_dict[report]["resource_academic_international"]
		reporting_data[facility]["resource_internal"] = all_data_dict[report]["resource_internal"]
		reporting_data[facility]["resource_industry"] = all_data_dict[report]["resource_industry"]
		reporting_data[facility]["resource_healthcare"] = all_data_dict[report]["resource_healthcare"]
		reporting_data[facility]["resource_other"] = all_data_dict[report]["resource_other"]

		reporting_data[facility]["user_fees_academic_sweden"] = all_data_dict[report]["user_fees_academic_sweden"]
		reporting_data[facility]["user_fees_academic_international"] = all_data_dict[report]["user_fees_academic_international"]
		reporting_data[facility]["user_fees_industry"] = all_data_dict[report]["user_fees_industry"]
		reporting_data[facility]["user_fees_healthcare"] = all_data_dict[report]["user_fees_healthcare"]
		reporting_data[facility]["user_fees_other"] = all_data_dict[report]["user_fees_other"]

		reporting_data[facility]["cost_reagents"] = all_data_dict[report]["cost_reagents"]
		reporting_data[facility]["cost_instrument"] = all_data_dict[report]["cost_instrument"]
		reporting_data[facility]["cost_salaries"] = all_data_dict[report]["cost_salaries"]
		reporting_data[facility]["cost_rents"] = all_data_dict[report]["cost_rents"]
		reporting_data[facility]["cost_other"] = all_data_dict[report]["cost_other"]

		reporting_data[facility]["additional_funding"] = all_data_dict[report]["additional_funding"]

		reporting_data[facility]["facility_head"] = all_data_dict[report]["facility_head"]
		reporting_data[facility]["facility_director"] = all_data_dict[report]["facility_director"]

		reporting_data[facility]["user_affiliation"] = all_data_dict[report]["user_affiliation"]

		# NOT USED IN REPORT BUT I THINK CONTAINS DATA??:
		garbage_data[facility]["personnel"] = all_data_dict[report]["personnel"]
		garbage_data[facility]["personnel_count"] = all_data_dict[report]["personnel_count"]
		garbage_data[facility]["personnel_count_male"] = all_data_dict[report]["personnel_count_male"]
		garbage_data[facility]["personnel_count_phd"] = all_data_dict[report]["personnel_count_phd"]
		garbage_data[facility]["personnel_count_phd_male"] = all_data_dict[report]["personnel_count_phd_male"]
		garbage_data[facility]["eln_usage"] = all_data_dict[report]["eln_usage"]
		garbage_data[facility]["facility_kpi"] = all_data_dict[report]["facility_kpi"]
		garbage_data[facility]["user_fees"] = all_data_dict[report]["user_fees"]
		garbage_data[facility]["immaterial_property_rights"] = all_data_dict[report]["immaterial_property_rights"]
		garbage_data[facility]["identifier"] = all_data_dict[report]["identifier"]
		garbage_data[facility]["resource_allocation"] = all_data_dict[report]["resource_allocation"]
		garbage_data[facility]["finances"] = all_data_dict[report]["finances"]
		garbage_data[facility]["scientific_achievements"] = all_data_dict[report]["scientific_achievements"]
		garbage_data[facility]["technology_development"] = all_data_dict[report]["technology_development"]
		garbage_data[facility]["innovation_utilization"] = all_data_dict[report]["innovation_utilization"]
		garbage_data[facility]["achievements_of_the_year"] = all_data_dict[report]["achievements_of_the_year"]
		garbage_data[facility]["budget_next_year"] = all_data_dict[report]["budget_next_year"]
		garbage_data[facility]["type_of_costs"] = all_data_dict[report]["type_of_costs"]
		garbage_data[facility]["number_projects"] = all_data_dict[report]["number_projects"]
		garbage_data[facility]["user_fee_models"] = all_data_dict[report]["user_fee_models"]
		garbage_data[facility]["deliverables"] = all_data_dict[report]["deliverables"]
		garbage_data[facility]["user_feedback"] = all_data_dict[report]["user_feedback"]

		# NOT USED AND NOT RELEVANT
		garbage_data[facility]["type"] = all_data_dict[report]["type"]
		garbage_data[facility]["invalid"] = all_data_dict[report]["invalid"]
		garbage_data[facility]["site"] = all_data_dict[report]["site"]
		garbage_data[facility]["links"] = all_data_dict[report]["links"]
		garbage_data[facility]["form"] = all_data_dict[report]["form"]
		garbage_data[facility]["tags"] = all_data_dict[report]["tags"]
		garbage_data[facility]["timestamp"] = all_data_dict[report]["timestamp"]
		garbage_data[facility]["report"] = all_data_dict[report]["report"]
		garbage_data[facility]["created"] = all_data_dict[report]["created"]
		garbage_data[facility]["iuid"] = all_data_dict[report]["iuid"]
		garbage_data[facility]["modified"] = all_data_dict[report]["modified"]
		garbage_data[facility]["volume_data"] = all_data_dict[report]["volume_data"]
		garbage_data[facility]["owner"] = all_data_dict[report]["owner"]
		garbage_data[facility]["title"] = all_data_dict[report]["title"]
		garbage_data[facility]["history"] = all_data_dict[report]["history"]
		garbage_data[facility]["status"] = all_data_dict[report]["status"]

		# Trying to find a budget file for next year
		budget_file = ""
		for reporting_file in reporting_data[facility]["files"]:
			if "budget" in reporting_file.lower():
				budget_file = reporting_data[facility]["files"][reporting_file]
		reporting_data[facility]["next_year_budget_file"] = budget_file

		# Tries to match the facility name with a DB label name
		database_label_name = difflib.get_close_matches(facility, labels_check_dict.keys(), 1)
		reporting_data[facility]["database_label_names"] = database_label_name

	if not os.path.isfile('Facility_report_data.xlsx'):
		workbook = xlsxwriter.Workbook('Facility_report_data.xlsx')
		worksheet_data = workbook.add_worksheet("Data")
		worksheet_db_labels = workbook.add_worksheet("Publications DB labels")
		bold = workbook.add_format({'bold': True})

		for row, facility in enumerate(sorted(reporting_data.keys()),1):
			if row == 1:
				worksheet_data.write(0, 0, 'facility', bold)
				worksheet_data.write(0, 1, 'facility_report_id', bold)
			worksheet_data.write(row, 0, facility, bold)
			worksheet_data.write(row, 1, report_id)

			for col, item in enumerate(sorted(reporting_data[facility].keys()),2):
				if row == 1:
					worksheet_data.write(0, col, item, bold)
				worksheet_data.write(row, col, str(reporting_data[facility][item]).decode('utf-8'))

		# These need additional information
		additional_headers = ["platform", "scilifelab_funding", "services_bullets", "national_scilifelab_facility_since", "host_university", "asterisk_footnote"]
		for i, col_head in enumerate(additional_headers, 2):
			worksheet_data.write(0, len(reporting_data[reporting_data.keys()[0]].keys())+i, col_head, bold)

		# Writing the DB labels to separate sheet so that user can fill them in
		worksheet_db_labels.write(0, 0, "Publications DB label. Put one of these in the 'database_label_names' column in the Data sheet", bold)
		for i, label in enumerate(sorted(labels_check_dict.keys()), 1):
			worksheet_db_labels.write(i, 0, str([label]).decode('utf-8'))

		workbook.close()

	# Load spreadsheets
	completed_data_file = 'Facility_report_data.xlsx'
	completed_data_xl = pd.ExcelFile(completed_data_file)
	completed_data_df = completed_data_xl.parse("Data")

	complete_reporting_data = dict()
	
	for i, row in completed_data_df.iterrows():
		facility = row["facility"]

		complete_reporting_data[facility] = dict()

		complete_reporting_data[facility]["fte"] = row["fte"]
		complete_reporting_data[facility]["fte_scilifelab"] = row["fte_scilifelab"]

		complete_reporting_data[facility]["resource_academic_national"] = row["resource_academic_national"]
		complete_reporting_data[facility]["resource_academic_international"] = row["resource_academic_international"]
		complete_reporting_data[facility]["resource_internal"] = row["resource_internal"]
		complete_reporting_data[facility]["resource_industry"] = row["resource_industry"]
		complete_reporting_data[facility]["resource_healthcare"] = row["resource_healthcare"]
		complete_reporting_data[facility]["resource_other"] = row["resource_other"]
		
		complete_reporting_data[facility]["user_fees_academic_sweden"] = row["user_fees_academic_sweden"]
		complete_reporting_data[facility]["user_fees_academic_international"] = row["user_fees_academic_international"]
		complete_reporting_data[facility]["user_fees_industry"] = row["user_fees_industry"]
		complete_reporting_data[facility]["user_fees_healthcare"] = row["user_fees_healthcare"]
		complete_reporting_data[facility]["user_fees_other"] = row["user_fees_other"]

		complete_reporting_data[facility]["cost_reagents"] = row["cost_reagents"]
		complete_reporting_data[facility]["cost_instrument"] = row["cost_instrument"]
		complete_reporting_data[facility]["cost_salaries"] = row["cost_salaries"]
		complete_reporting_data[facility]["cost_rents"] = row["cost_rents"]
		complete_reporting_data[facility]["cost_other"] = row["cost_other"]

		complete_reporting_data[facility]["additional_funding"] = row["additional_funding"]
		complete_reporting_data[facility]["facility_head"] = row["facility_head"]
		complete_reporting_data[facility]["facility_director"] = row["facility_director"]

		complete_reporting_data[facility]["database_label_names"] = row["database_label_names"]
		complete_reporting_data[facility]["user_affiliation"] = row["user_affiliation"]

		complete_reporting_data[facility]["platform"] = row["platform"]
		complete_reporting_data[facility]["scilifelab_funding"] = row["scilifelab_funding"]
		complete_reporting_data[facility]["services_bullets"] = row["services_bullets"]
		complete_reporting_data[facility]["national_scilifelab_facility_since"] = row["national_scilifelab_facility_since"]
		complete_reporting_data[facility]["host_university"] = row["host_university"]
		complete_reporting_data[facility]["asterisk_footnote"] = row["asterisk_footnote"]

	now = datetime.datetime.now()
	for facility in reporting_data.keys():
	 	# generatePdf(facility, complete_reporting_data[facility], now.year)
	 	generatePdf(facility, complete_reporting_data[facility], 2018)

