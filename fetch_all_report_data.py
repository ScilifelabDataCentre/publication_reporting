#!/usr/bin/env python
# -*- coding: utf-8 -*-

from get_report import facility_reports
from api_key import API_KEY
import os
import json
import pandas as pd
import math
import urllib
import difflib
import xlsxwriter

def all_same(items):
	return all(x == items[0] for x in items)

warnings = []
fcr = facility_reports(api_key=API_KEY)

valid_affiliations = [u"Chalmers University of Technology",
	u"Karolinska Institutet",
	u"KTH Royal Institute of Technology",
	u"Linköping University",
	u"Lund University",
	u"Stockholm University",
	u"Swedish University of Agricultural Sciences",
	u'Umeå University',
	u"University of Gothenburg",
	u"Uppsala University",
	u"Other Swedish University",
	u"International University",
	u"Healthcare",
	u"Industry",
	u"Naturhistoriska Riksmuséet",
	u"Other Swedish organization",
	u"Other international organization"]

submitted_report_urls = fcr.get_reports(status="submitted", return_url=True)

reports = []

for report in submitted_report_urls:
	print "Fetched:", report
	reports.append(fcr.get_url_json(report))

cwd = os.getcwd()

directory = cwd+"/fetched_facility_reports"
if not os.path.exists(directory):
	os.makedirs(directory)

# Stores all data gathered from all fetched reports
all_reports_data = dict()

# Go through all fetched reports
for report in reports:
	# Stores the data for this specific report
	report_id = report["identifier"]
	report_data = dict()
	volume_file = None
	volume_file_backup = None
	
	# Create a subdir for this report, we will download files
	sub_directory = cwd+"/fetched_facility_reports/"+report_id
	if not os.path.exists(sub_directory):
		os.makedirs(sub_directory)

	# Go through all the fields in the report
	for key in report:
		# Break this field of "fields" down a bit to make it easier later
		if key == "fields":
			for fkey in report[key]:
				report_data[fkey] = report[key][fkey]
		elif key == "files": # Download all the files listed
			report_data["files"] = dict()
			for fkey in report[key]:
				cwd = os.getcwd()
				# print "Downloading:", report[key][fkey]["href"]
				fcr.download_file(report[key][fkey]["href"], sub_directory)
				if "volume" in report[key][fkey]["href"].lower():
					volume_file = report[key][fkey]["href"]
				if ".xlsm" in report[key][fkey]["href"].lower():
					if not volume_file_backup:
						volume_file_backup = report[key][fkey]["href"]
					else:
						if not volume_file:
							raise Exception("Several possible files found for Volume data")
				report_data["files"][fkey] = report[key][fkey]["href"]
		else: # Just store the rest
			report_data[key] = report[key]
	if not volume_file:
		warnings.append("WARNING: NO EXPLICITLY NAMED VOLUME FILE FOR {}, USING {}".format( report_id, volume_file_backup))
		volume_file = volume_file_backup

	volume_file = "{}/{}".format(sub_directory, volume_file.split("/")[-1])
	# Read the volume data spreadsheet
	volume_xl = pd.ExcelFile(volume_file)
	# print volume_xl.sheet_names
	user_sheet_index = None
	for i, sheet_name in enumerate(volume_xl.sheet_names):
		if "Users" in sheet_name:
			user_sheet_index = i
	if user_sheet_index == None:
		raise Exception("No Users tab in Volume data file")

	users_df = volume_xl.parse(volume_xl.sheet_names[user_sheet_index])
	
	facility_name = None
	facility_contact = None
	user_dict = {}

	for i, row in users_df.iterrows():
		if i > 6: # the 7th row starts the user list
			if type(row[0]) == float and math.isnan(row[0]): # Lazy python checks
				break

			# row[0] is facility name
			# row[1] is facility email contact
			# row[2] is PI first name
			# row[3] is PI last name
			# row[4] is PI email
			# row[5] is PI affiliation
			# row[6] is PI affiliation specification if needed

			if not facility_name:
				facility_name = row[0]
			if not facility_contact:
				facility_contact = row[1]
			
			# First name
			if type(row[2]) == unicode and row[2].strip() != u"":
				user_fname = row[2].strip()
			else:
				warnings.append("WARNING: Missing user first name in {} row {}. Report ID: {}".format(facility_name, i, report_id))
				user_fname = u""
			# Last name
			if type(row[3]) == unicode and row[3].strip() != u"":
				user_lname = row[3].strip()
			else:
				warnings.append("WARNING: Missing user last name in {} row {}. Report ID: {}".format(facility_name, i, report_id))
				user_lname = u""
			# Email
			if type(row[4]) == unicode and row[4].strip() != u"":
				user_email = row[4].strip().lower()
				if u"@" not in user_email:
					warnings.append("WARNING: Broken email address: '{}' in {} row {}. Report ID: {}".format(user_email, facility_name, i, report_id))
			else:
				warnings.append("WARNING: Missing user email in {} row {}. Report ID: {}".format(facility_name, i, report_id))
				user_email = u""
			# Affiliation
			if type(row[5]) == unicode and row[5].strip() != u"":
				user_aff = row[5].strip()
			else:
				warnings.append("WARNING: Missing user affiliation in {} row {}. Report ID: {}".format(facility_name, i, report_id))
				user_aff = u""
			# Affiliation specification
			if type(row[6]) == unicode and row[6].strip() != u"":
				user_aff_spec = row[6].strip()
			else:
				# Dont care about this being missing, since it only applies to some affiliations
				user_aff_spec = u""

			if user_email in user_dict.keys():
				user_dict[user_email].append([user_fname, user_lname, user_aff, user_aff_spec])
			else:
				user_dict[user_email] = [[user_fname, user_lname, user_aff, user_aff_spec]]

	for user_email in user_dict.keys():
		if len(user_dict[user_email]) > 1:
			if u"@" in user_email:
				if not all_same(user_dict[user_email]):
					warnings.append("WARNING: Same user email different info: {} {}. Report ID: {}".format(user_dict[user_email], user_email, report_id))

	affiliation_dict = {}
	for aff in valid_affiliations:
		affiliation_dict[aff] = 0

	for user_email in user_dict.keys():
		for user in user_dict[user_email]:
			try:
				affiliation_dict[user[2]] += 1
			except KeyError as e:
				warnings.append("WARNING: Affiliation not valid: {}. Report ID: {}".format(user, report_id))
	
	report_data["user_affiliation"] = affiliation_dict

	# Write json data
	with open("{}/{}.json".format(sub_directory, report_id), 'w') as f:
		json.dump(report_data, f)
	# Save to collected output
	all_reports_data[report_id] = report_data

with open("{}/all_reports_data.json".format(directory), 'w') as f:
	json.dump(all_reports_data, f)

### Reopen the json file and convert to xlsx so that humans can edit
# Only put the relevant stuff in the excel file, to not confuse humans
# reporting_data will contain relevant stuff, garbage will contain garbage

reporting_data = dict()
garbage_data = dict()

all_data_raw = open("{}/all_reports_data.json".format(directory), "r").read()
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

