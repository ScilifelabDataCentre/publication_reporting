#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path
import pandas as pd
import json
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

from facility_report_plots import user_plot

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

def generatePdf(facility_name, reporting_data):
	doc = BaseDocTemplate(u"facility_onepagers/{}.pdf".format(facility_name.lower().replace(" ", "_")),
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
	
	frame1 = Frame(doc.leftMargin, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-18*mm, id='col1', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	frame2 = Frame(doc.leftMargin+doc.width/2+3.5*mm, doc.bottomMargin, doc.width/2-3.5*mm, doc.height-18*mm, id='col2', leftPadding=0*mm, topPadding=0*mm, rightPadding=0*mm, bottomPadding=0*mm)
	
	header_content = Paragraph(
		u'<b>{}</b><br/><font name=Frutiger-45-Light size=12> {} platform</font>'.format(facility_name, reporting_data["platform"]), 
		styles["onepager_title"])

	#print header_content

	template = PageTemplate(id='test', frames=[frame1,frame2], onPage=partial(header, content=header_content))
	doc.addPageTemplates([template])

	Story = []

	Story.append(Paragraph("<font color='#95C11E' name=Frutiger-65-Bold><b>Basic information</b></font>", styles["onepager_inner_heading"]))

	directors = ""
	for director in reporting_data["facility_director"]:
		if directors:
			directors += u', ' + u' '.join((director[0], director[1])).strip()
		else:
			directors = u' '.join((director[0], director[1])).strip()
	
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>Facility director: </b></font>{}".format(directors), 
		styles["onepager_text"]))

	try:
		heads = ""
		print facility_name
		for head in reporting_data["facility_head"]:
			if heads:
				heads += u', ' + u' '.join((head[0], head[1])).strip()
			else:
				heads = u' '.join((head[0], head[1])).strip()
		Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>Head of facility: </b></font>{}".format(heads), 
			styles["onepager_text"]))
	except KeyError as e:
		print "WARNING: NO HEAD OF FACILITY FOR:", facility_name

	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>SciLifeLab facility since: </b></font>{}".format(reporting_data["national_scilifelab_facility_since"]), 
		styles["onepager_text"]))
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>Host university: </b></font>{}".format(reporting_data["host_university"]), 
		styles["onepager_text"]))
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>FTEs: </b></font>{}".format(reporting_data["fte"]), 
		styles["onepager_text"]))
	Story.append(Paragraph(u"<font name=Frutiger-65-Bold><b>FTEs financed by SciLifeLab: </b></font>{}".format(reporting_data["fte_scilifelab"]), 
		styles["onepager_text"]))

	Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Funding 2018 (in kSEK)</b></font></font>", 
		styles["onepager_inner_heading"]))
	
	total_funding = 0
	if "funding" in reporting_data.keys():
		for funds in reporting_data["funding"]:
			try:
				if funds[0].lower() != "user fees":#DONT count user fees to funding
					total_funding += int(funds[1])
			except ValueError as e:
				#If we cannot convert funds[1] to int, its probably not a number...
				print "WARNING: FUNDING ITEM NOT A NUMBER:", funds
	total_funding += int(reporting_data["scilifelab_funding_2018"])


	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>SciLifeLab: </b></font>{}".format(reporting_data["scilifelab_funding_2018"]), 
		styles["onepager_text"]))

	user_fees_flag = False
	user_fees_amount = None

	if "funding" in reporting_data.keys():
		for funds in reporting_data["funding"]:
			try:
				funds_amount = int(funds[1])
			except ValueError:
				funds_amount = "-"
			if funds[0].lower() == "user fees":
				user_fees_flag = True
				user_fees_amount = funds_amount
				continue

			if funds_amount == "-":
				Story.append(Paragraph("<font color='#FF0000' name=Frutiger-65-Bold><b>{}: </b></font>{}".format(funds[0], funds_amount), 
					styles["onepager_text"]))
			else:
				Story.append(Paragraph("<font name=Frutiger-65-Bold><b>{}: </b></font>{}".format(funds[0], funds_amount), 
					styles["onepager_text"]))

	Story.append(HRFlowable(width="40%", thickness=0.5, lineCap='round', color="#999999", spaceBefore=1, spaceAfter=1, hAlign='LEFT', vAlign='BOTTOM', dash=None))
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>Total: </b></font>{}".format(total_funding), 
		styles["onepager_text"]))


	##RESOURCE ALLOCATION
	total_percentage = reporting_data["resource_academic_national"]+reporting_data["resource_academic_international"]+\
		reporting_data["resource_internal"]+reporting_data["resource_industry"]+\
		reporting_data["resource_healthcare"]+reporting_data["resource_other"]
	if total_percentage == 100:
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Resource allocation 2018</b></font></font>", 
			styles["onepager_inner_heading"]))
	else:
		print "WARNING: PERCENTAGE DOES NOT ADD UP TO 100 IN RESOURCE_ALLOCATION FOR", facility_name, total_percentage
		Story.append(Paragraph("<font color='#FFFFFF'><font name=Frutiger-65-Bold><b>Resource allocation 2018</b></font></font>", 
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
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>User Fees 2018</b></font></font>", 
			styles["onepager_inner_heading"]))
	else:
		print "WARNING: PERCENTAGE DOES NOT ADD UP TO 100 IN COSTS FOR", facility_name, total_percentage
		Story.append(Paragraph("<font color='#FFFFFF'><font name=Frutiger-65-Bold><b>User Fees 2018</b></font></font>", 
			styles["onepager_inner_heading"]))
	
	if user_fees_flag:
		Story.append(Paragraph("<font color='#000000' name=Frutiger-65-Bold><b>Total (kSEK): </b></font>{}".format( user_fees_amount), 
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
		Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>User fees by sector 2018</b></font></font>", 
			styles["onepager_inner_heading"]))
	else:
		print "WARNING: PERCENTAGE DOES NOT ADD UP TO 100 IN USER FEES FOR", facility_name, total_percentage
		Story.append(Paragraph("<font color='#FFFFFF'><font name=Frutiger-65-Bold><b>User fees by sector 2018</b></font></font>", 
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

	bullet_points = reporting_data["service"].split("\n")
	for bullet in bullet_points:
		Story.append(Paragraph(bullet, styles["onepager_text"]))

	##USERS
	Story.append(CondPageBreak(100*mm))

	Story.append(Paragraph("<font color='#95C11E'><font name=Frutiger-65-Bold><b>Users 2018</b></font></font>", 
		styles["onepager_inner_heading"]))

	user_dist_filename = u"facility_onepagers_figures/{}".format(reporting_data["user_dist_plot"])

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

	if os.path.isfile("facility_onepagers_figures/{}_pub_count.txt".format(reporting_data["figure_prefix"])):
		pub_count = open("facility_onepagers_figures/{}_pub_count.txt".format(reporting_data["figure_prefix"]), "r").read().split("\t")
	else:
		pub_count = ["-", "-", "-"]
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>2016: </b></font>{}".format(pub_count[0]), 
		styles["onepager_text"]))
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>2017: </b></font>{}".format(pub_count[1]), 
		styles["onepager_text"]))
	Story.append(Paragraph("<font name=Frutiger-65-Bold><b>2018: </b></font>{}".format(pub_count[2]), 
		styles["onepager_text"]))

	pub_label_cat_filename = "facility_onepagers_figures/{}_publications_by_category.svg".format(reporting_data["figure_prefix"])
	pub_label_jif_filename = "facility_onepagers_figures/{}_jif.svg".format(reporting_data["figure_prefix"])
	
	if os.path.isfile(pub_label_cat_filename) and os.path.isfile(pub_label_jif_filename):	 

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
		print "WARNING: NO PUB PLOTS FOR:", facility_name, reporting_data["figure_prefix"]

	#print Story
	doc.build(Story)


if __name__ == "__main__":
	reporting_data = dict()
	garbage_data = dict()

	all_data_raw = open("fetched_facility_reports/all_reports_data.json", "r").read()

	all_data_dict = json.loads(all_data_raw)

	for report in all_data_dict.keys():

		facility = all_data_dict[report]["facility"]
		reporting_data[facility] = dict()
		garbage_data[facility] = dict()

		print facility

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
		reporting_data[facility]["id"] = all_data_dict[report]["id"]
		garbage_data[facility]["title"] = all_data_dict[report]["title"]
		garbage_data[facility]["history"] = all_data_dict[report]["history"]
		garbage_data[facility]["status"] = all_data_dict[report]["status"]














		del all_data_dict[report]["facility"]

		del all_data_dict[report]["fte"]
		del all_data_dict[report]["fte_scilifelab"]

		del all_data_dict[report]["resource_academic_national"]
		del all_data_dict[report]["resource_academic_international"]
		del all_data_dict[report]["resource_internal"]
		del all_data_dict[report]["resource_industry"]
		del all_data_dict[report]["resource_healthcare"]
		del all_data_dict[report]["resource_other"]

		del all_data_dict[report]["user_fees_academic_sweden"]
		del all_data_dict[report]["user_fees_academic_international"]
		del all_data_dict[report]["user_fees_industry"]
		del all_data_dict[report]["user_fees_healthcare"]
		del all_data_dict[report]["user_fees_other"]

		del all_data_dict[report]["cost_reagents"]
		del all_data_dict[report]["cost_instrument"]
		del all_data_dict[report]["cost_salaries"]
		del all_data_dict[report]["cost_rents"]
		del all_data_dict[report]["cost_other"]

		del all_data_dict[report]["facility_head"]
		del all_data_dict[report]["facility_director"]

		del all_data_dict[report]["user_affiliation"]


		# NOT USED IN REPORT BUT I THINK CONTAINS DATA??:
		del all_data_dict[report]["personnel"]
		del all_data_dict[report]["personnel_count"]
		del all_data_dict[report]["personnel_count_male"]
		del all_data_dict[report]["personnel_count_phd"]
		del all_data_dict[report]["personnel_count_phd_male"]



		del all_data_dict[report]["eln_usage"]
		del all_data_dict[report]["facility_kpi"]
		del all_data_dict[report]["user_fees"]
		del all_data_dict[report]["immaterial_property_rights"]
		del all_data_dict[report]["identifier"]
		del all_data_dict[report]["resource_allocation"]
		del all_data_dict[report]["finances"]
		del all_data_dict[report]["scientific_achievements"]
		del all_data_dict[report]["technology_development"]


		del all_data_dict[report]["innovation_utilization"]
		del all_data_dict[report]["achievements_of_the_year"]
		del all_data_dict[report]["budget_next_year"]
		del all_data_dict[report]["type_of_costs"]
		del all_data_dict[report]["number_projects"]
		del all_data_dict[report]["user_fee_models"]

		del all_data_dict[report]["additional_funding"]
		del all_data_dict[report]["deliverables"]
		del all_data_dict[report]["user_feedback"]



		# NOT USED AND NOT RELEVANT
		del all_data_dict[report]["type"]
		del all_data_dict[report]["invalid"]
		del all_data_dict[report]["site"]
		del all_data_dict[report]["links"]
		del all_data_dict[report]["form"]
		del all_data_dict[report]["tags"]
		del all_data_dict[report]["timestamp"]
		del all_data_dict[report]["report"]
		del all_data_dict[report]["created"]
		del all_data_dict[report]["iuid"]
		del all_data_dict[report]["modified"]
		del all_data_dict[report]["volume_data"]

		del all_data_dict[report]["owner"]
		del all_data_dict[report]["id"]
		del all_data_dict[report]["title"]
		del all_data_dict[report]["history"]
		del all_data_dict[report]["status"]

		user_plot(reporting_data[facility]["user_affiliation"], facility)
	
		# for key in sorted(garbage_data[facility].keys()):
		# 	print key, garbage_data[facility][key]
	
	workbook = xlsxwriter.Workbook('Facility_report_data.xlsx')
	worksheet = workbook.add_worksheet()
	bold = workbook.add_format({'bold': True})

	for row, facility in enumerate(sorted(reporting_data.keys()),1):

		if row == 1:
			 worksheet.write(0,0, 'Facility', bold)
			 worksheet.write(0,1, 'Facility report ID', bold)

		worksheet.write(row, 0, facility, bold)

		# Create a Pandas dataframe from the data.
		facility_item_list = []

		for col, item in enumerate(sorted(reporting_data[facility].keys()),2):
			if row == 1:
				worksheet.write(0, col, item, bold)

			if item == "id":
				worksheet.write(row, 1, reporting_data[facility][item], bold)
			else:
				worksheet.write(row, col, unicode(reporting_data[facility][item]))
	workbook.close()






'''

	reporting_data = dict()

	facility_to_pubdb_label = open("excel_data_sheets/reporting_facility_to_pubdb_label.tsv").readlines()
	for facility_entry in facility_to_pubdb_label:
		
		facility = facility_entry.split("\t")[0].strip()
		
		if isinstance(facility, str):
			facility = unicode(facility, "utf-8")

		pubdb_labels = facility_entry.split("\t")[1].split(",")
		
		reporting_data[facility] = dict()

		reporting_data[facility]["publication_labels"] = pubdb_labels
		if len(pubdb_labels) > 1:
			reporting_data[facility]["figure_prefix"] = "ngi_stockholm_(genomics_applications)" #facility.lower().replace(" ", "_")
		else:
			reporting_data[facility]["figure_prefix"] = pubdb_labels[0].strip().lower().replace(" ", "_")

		##User dist plot
		reporting_data[facility]["user_dist_plot"] = u"{}_user.svg".format(facility.lower().replace(" ", "_"))

	# Assign spreadsheet filename to `file`
	user_data_file = 'excel_data_sheets/user_data_for_facility_report_2018.xlsx'
	table_data_file = 'excel_data_sheets/table_data_for_facility_report_2018.xlsx'
	free_data_file = 'excel_data_sheets/free_text_data_for_facility_report_2018.xlsx'
	heads_data_file = 'excel_data_sheets/heads_of_facilities_for_facility_report_2018.xlsx'
	directors_data_file = 'excel_data_sheets/facility_directors_for_facility_report_2018.xlsx'
	funding_data_file = 'excel_data_sheets/additional_funding_for_facility_report_2018.xlsx'

	# Load spreadsheets
	user_xl = pd.ExcelFile(user_data_file)
	table_xl = pd.ExcelFile(table_data_file)
	free_xl = pd.ExcelFile(free_data_file)
	heads_xl = pd.ExcelFile(heads_data_file)
	directors_xl = pd.ExcelFile(directors_data_file)
	funding_xl = pd.ExcelFile(funding_data_file)
	
	user_df = user_xl.parse(user_xl.sheet_names[0])
	table_df = table_xl.parse(table_xl.sheet_names[0])
	free_df = free_xl.parse(free_xl.sheet_names[0])
	heads_df = heads_xl.parse(heads_xl.sheet_names[0])
	directors_df = directors_xl.parse(directors_xl.sheet_names[0])
	funding_df = funding_xl.parse(funding_xl.sheet_names[0])

	for i, row in table_df.iterrows():
		facility = row["facility"]

		reporting_data[facility]["fte"] = row["fte"]
		reporting_data[facility]["fte_scilifelab"] = row["fte_scilifelab"]

		reporting_data[facility]["resource_academic_national"] = row["resource_academic_national"]
		reporting_data[facility]["resource_academic_international"] = row["resource_academic_international"]
		reporting_data[facility]["resource_internal"] = row["resource_internal"]
		reporting_data[facility]["resource_industry"] = row["resource_industry"]
		reporting_data[facility]["resource_healthcare"] = row["resource_healthcare"]
		reporting_data[facility]["resource_other"] = row["resource_other"]
		
		reporting_data[facility]["user_fees_academic_sweden"] = row["user_fees_academic_sweden"]
		reporting_data[facility]["user_fees_academic_international"] = row["user_fees_academic_international"]
		reporting_data[facility]["user_fees_industry"] = row["user_fees_industry"]
		reporting_data[facility]["user_fees_healthcare"] = row["user_fees_healthcare"]
		reporting_data[facility]["user_fees_other"] = row["user_fees_other"]

		reporting_data[facility]["cost_reagents"] = row["cost_reagents"]
		reporting_data[facility]["cost_instrument"] = row["cost_instrument"]
		reporting_data[facility]["cost_salaries"] = row["cost_salaries"]
		reporting_data[facility]["cost_rents"] = row["cost_rents"]
		reporting_data[facility]["cost_other"] = row["cost_other"]

	for i, row in free_df.iterrows():
		facility = row["Reporting Units (34)"]
		reporting_data[facility]["platform"] = row["Platform"]
		reporting_data[facility]["scilifelab_funding_2018"] = row["SciLifeLab funding 2018"]
		reporting_data[facility]["service"] = row["Service"]
		reporting_data[facility]["national_scilifelab_facility_since"] = row["National SciLifeLab facility since"]
		if isinstance(row["Host university"], str):
			print row["Host university"]
			reporting_data[facility]["host_university"] = unicode(row["Host university"], "utf-8")
		else:
			reporting_data[facility]["host_university"] = row["Host university"]

	for i, row in heads_df.iterrows():
		facility = row["facility"]
		if isinstance(row["facility_head: First name"], str):
			fname = unicode(row["facility_head: First name"], "utf-8")
		else:
			fname = row["facility_head: First name"]
		if isinstance(row["facility_head: First name"], str):
			lname = unicode(row["facility_head: Last name"], "utf-8")
		else:
			lname = row["facility_head: Last name"]

		try:
			reporting_data[facility]["facility_head"].append((fname, lname))
		except KeyError as e:
			#First entry:
			reporting_data[facility]["facility_head"] = [(fname, lname)]

	for i, row in directors_df.iterrows():
		facility = row["facility"]
		if isinstance(row["facility_director: First name"], str):
			fname = unicode(row["facility_director: First name"], "utf-8")
		else:
			fname = row["facility_director: First name"]
		if isinstance(row["facility_director: First name"], str):
			lname = unicode(row["facility_director: Last name"], "utf-8")
		else:
			lname = row["facility_director: Last name"]
		try:
			reporting_data[facility]["facility_director"].append((fname, lname))
		except KeyError as e:
			#First entry:
			reporting_data[facility]["facility_director"] = [(fname, lname)]

	for i, row in funding_df.iterrows():
		facility = row["facility"]
		try:
			reporting_data[facility]["funding"].append((row["additional_funding: Name of financier"], row["additional_funding: Amount (kSEK)"]))
		except KeyError as e:
			#First entry:
			reporting_data[facility]["funding"] = [(row["additional_funding: Name of financier"], row["additional_funding: Amount (kSEK)"])]
	#print reporting_data

	for facility in reporting_data.keys():
		generatePdf(facility, reporting_data[facility])
'''	
