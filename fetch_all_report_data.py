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
import string

def all_same(items):
	return all(x == items[0] for x in items)
def is_number(number):
	try:
		float(number)
		return True
	except ValueError:
		return False

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

cwd = os.getcwd()

directory = cwd+"/fetched_facility_reports"
if not os.path.exists(directory):
	os.makedirs(directory)

submitted_report_urls = fcr.get_reports(status="submitted", return_url=True)

reports = []

for report in submitted_report_urls:
	print "Fetched:", report
	reports.append(fcr.get_url_json(report))

# Stores all data gathered from all fetched reports
all_reports_data = dict()

# Go through all fetched reports
for report in reports:
	# Stores the data for this specific report
	report_id = report["identifier"]
	report_data = dict()
	
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
				report_data["files"][fkey] = report[key][fkey]["href"]
		else: # Just store the rest
			report_data[key] = report[key]

	volume_file = u"{}/{}".format(sub_directory, u''.join(filter(lambda x: x in string.printable, report["fields"]["volume_data"])))

	# Read the volume data spreadsheet
	volume_xl = pd.ExcelFile(volume_file)
	# print volume_xl.sheet_names
	user_sheet_index = None
	for i, sheet_name in enumerate(volume_xl.sheet_names):
		if "Users" in sheet_name:
			user_sheet_index = i
	if user_sheet_index == None:
		raise Exception("No Users tab in Volume data file")
	
	courses_sheet_index = None
	for i, sheet_name in enumerate(volume_xl.sheet_names):
		if "Courses" in sheet_name:
			courses_sheet_index = i
	if courses_sheet_index == None:
		raise Exception("No Courses tab in Volume data file")
	
	events_sheet_index = None
	for i, sheet_name in enumerate(volume_xl.sheet_names):
		if "Conf, symp, semin" in sheet_name:
			events_sheet_index = i
	if events_sheet_index == None:
		raise Exception("No Conf tab in Volume data file")

	external_sheet_index = None
	for i, sheet_name in enumerate(volume_xl.sheet_names):
		if "External" in sheet_name:
			external_sheet_index = i
	if external_sheet_index == None:
		raise Exception("No External tab in Volume data file")


	### USERS
	users_df = volume_xl.parse(volume_xl.sheet_names[user_sheet_index])
	
	facility_name = None
	facility_contact = None
	user_dict = dict()
	user_list_per_facility = list()

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

			user_list_per_facility.append([facility_contact, user_email, user_fname, user_lname, user_aff, user_aff_spec])

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
	
	report_data["user_all"] = user_list_per_facility
	report_data["user_affiliation"] = affiliation_dict


	### COURSES
	courses_df = volume_xl.parse(volume_xl.sheet_names[courses_sheet_index])
	
	facility_name = None
	facility_contact = None
	courses_list_per_facility = list()

	for i, row in courses_df.iterrows():
		if i > 6: # the 7th row starts the user list
			if type(row[0]) == float and math.isnan(row[0]): # Lazy python checks
				break

			# row[0] is facility name
			# row[1] is facility email contact
			# row[2] is Full name of the course
			# row[3] is Did the reporting unit organize or co-organize the course?* 
			# row[4] is If co-organized, with whom?
			# row[5] is Start date* (yyyy-mm-dd)
			# row[6] is End date* (yyyy-mm-dd) 
			# row[7] is Location (city) of the course*
			# row[8] is Comment

			if not facility_name:
				facility_name = row[0]
			if not facility_contact:
				facility_contact = row[1]

			courses_name = row[2].strip() if isinstance(row[2], basestring) else unicode(row[2])
			courses_organize = row[3].strip() if isinstance(row[3], basestring) else unicode(row[3])
			courses_ifcoorganize = row[4].strip() if isinstance(row[4], basestring) else unicode(row[4])
			courses_start = row[5].strip() if isinstance(row[5], basestring) else unicode(row[5])
			courses_end = row[6].strip() if isinstance(row[6], basestring) else unicode(row[6])
			courses_location = row[7].strip() if isinstance(row[7], basestring) else unicode(row[7])
			courses_comment = row[8].strip() if isinstance(row[8], basestring) else unicode(row[8])

			courses_list_per_facility.append([facility_name, facility_contact, courses_name, courses_organize, courses_ifcoorganize, courses_start, courses_end, courses_location, courses_comment])
	
	report_data["courses_all"] = courses_list_per_facility

	### EVENTS
	event_df = volume_xl.parse(volume_xl.sheet_names[events_sheet_index])
	
	facility_name = None
	facility_contact = None
	event_list_per_facility = list()

	for i, row in event_df.iterrows():
		
		if i > 6: # the 7th row starts the user list
			if type(row[0]) == float and math.isnan(row[0]): # Lazy python checks
				break

			# row[0] is facility name
			# row[1] is facility email contact
			# row[2] is Full name of the course
			# row[3] is Did the reporting unit organize or co-organize the course?* 
			# row[4] is If co-organized, with whom?
			# row[5] is Start date* (yyyy-mm-dd)
			# row[6] is End date* (yyyy-mm-dd) 
			# row[7] is Location (city) of the course*
			# row[8] is Comment
			
			if not facility_name:
				facility_name = row[0]
			if not facility_contact:
				facility_contact = row[1]
			
			event_name = row[2].strip() if isinstance(row[2], basestring) else unicode(row[2])
			event_organize = row[3].strip() if isinstance(row[3], basestring) else unicode(row[3])
			event_ifcoorganize = row[4].strip() if isinstance(row[4], basestring) else unicode(row[4])
			event_start = row[5].strip() if isinstance(row[5], basestring) else unicode(row[5])
			event_end = row[6].strip() if isinstance(row[6], basestring) else unicode(row[6])
			event_location = row[7].strip() if isinstance(row[7], basestring) else unicode(row[7])
			event_comment = row[8].strip() if isinstance(row[8], basestring) else unicode(row[8])

			event_list_per_facility.append([facility_name, facility_contact, event_name, event_organize, event_ifcoorganize, event_start, event_end, event_location, event_comment])
	
	report_data["events_all"] = event_list_per_facility
	
	### EXTERNAL
	external_df = volume_xl.parse(volume_xl.sheet_names[external_sheet_index])
	
	facility_name = None
	facility_contact = None
	external_list_per_facility = list()

	for i, row in external_df.iterrows():
		if i > 6: # the 7th row starts the user list
			if type(row[0]) == float and math.isnan(row[0]): # Lazy python checks
				break

			# row[0] is facility name
			# row[1] is facility email contact
			# row[2] is 3. Name of external organization
			# row[3] is 4. Type of organization (choose from drop-down menu)
			# row[4] is 5. Reference person
			# row[5] is 6. Purpose of collabaration/alliance

			if not facility_name:
				facility_name = row[0]
			if not facility_contact:
				facility_contact = row[1]

			external_name = row[2].strip() if isinstance(row[2], basestring) else unicode(row[2])
			external_type = row[3].strip() if isinstance(row[3], basestring) else unicode(row[3])
			external_reference = row[4].strip() if isinstance(row[4], basestring) else unicode(row[4])
			external_purpose = row[5].strip() if isinstance(row[5], basestring) else unicode(row[5])

			external_list_per_facility.append([facility_name, facility_contact, external_name, external_type, external_reference, external_purpose])
	
	report_data["external_all"] = external_list_per_facility

	# Write json data
	with open("{}/{}.json".format(sub_directory, report_id), 'w') as f:
		json.dump(report_data, f)
	# Save to collected output
	all_reports_data[report_id] = report_data

with open("{}/all_reports_data.json".format(directory), 'w') as f:
	json.dump(all_reports_data, f)

### Reopen the json file and convert to xlsx so that humans can edit
### Only put the relevant stuff in the excel file, to not confuse humans
### reporting_data will contain relevant stuff, garbage will contain garbage

reporting_data = dict()
meta_data = dict()
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
	meta_data[facility] = dict()
	garbage_data[facility] = dict()

	# Meta data
	meta_data[facility]["report_id"] = all_data_dict[report]["links"]["display"]["href"]
	meta_data[facility]["owner"] = all_data_dict[report]["owner"]

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
	reporting_data[facility]["user_all"] = all_data_dict[report]["user_all"]
	reporting_data[facility]["courses_all"] = all_data_dict[report]["courses_all"]
	reporting_data[facility]["events_all"] = all_data_dict[report]["events_all"]
	reporting_data[facility]["external_all"] = all_data_dict[report]["external_all"]
	reporting_data[facility]["eln_usage"] = all_data_dict[report]["eln_usage"]
	reporting_data[facility]["user_feedback"] = all_data_dict[report]["user_feedback"]
	reporting_data[facility]["innovation_utilization"] = all_data_dict[report]["innovation_utilization"]
	reporting_data[facility]["technology_development"] = all_data_dict[report]["technology_development"]
	reporting_data[facility]["scientific_achievements"] = all_data_dict[report]["scientific_achievements"]
	reporting_data[facility]["number_projects"] = all_data_dict[report]["number_projects"]
	reporting_data[facility]["immaterial_property_rights"] = all_data_dict[report]["immaterial_property_rights"]

	# USED LATER INSERT TO META DATA
	garbage_data[facility]["budget_next_year"] = all_data_dict[report]["budget_next_year"]
	garbage_data[facility]["volume_data"] = all_data_dict[report]["volume_data"]
	garbage_data[facility]["facility_kpi"] = all_data_dict[report]["facility_kpi"]

	# NOT USED IN REPORT BUT I THINK CONTAINS DATA??:
	garbage_data[facility]["personnel"] = all_data_dict[report]["personnel"]
	garbage_data[facility]["personnel_count"] = all_data_dict[report]["personnel_count"]
	garbage_data[facility]["personnel_count_male"] = all_data_dict[report]["personnel_count_male"]
	garbage_data[facility]["personnel_count_phd"] = all_data_dict[report]["personnel_count_phd"]
	garbage_data[facility]["personnel_count_phd_male"] = all_data_dict[report]["personnel_count_phd_male"]
	garbage_data[facility]["user_fees"] = all_data_dict[report]["user_fees"]
	garbage_data[facility]["identifier"] = all_data_dict[report]["identifier"]
	garbage_data[facility]["resource_allocation"] = all_data_dict[report]["resource_allocation"]
	garbage_data[facility]["finances"] = all_data_dict[report]["finances"]
	garbage_data[facility]["achievements_of_the_year"] = all_data_dict[report]["achievements_of_the_year"]
	garbage_data[facility]["type_of_costs"] = all_data_dict[report]["type_of_costs"]
	garbage_data[facility]["user_fee_models"] = all_data_dict[report]["user_fee_models"]
	garbage_data[facility]["deliverables"] = all_data_dict[report]["deliverables"]

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
	garbage_data[facility]["title"] = all_data_dict[report]["title"]
	garbage_data[facility]["history"] = all_data_dict[report]["history"]
	garbage_data[facility]["status"] = all_data_dict[report]["status"]

	# Adding budget and kpi file to the meta data dictionary
	sub_directory = cwd+"/fetched_facility_reports/"+all_data_dict[report]["id"].split("/")[-1]

	if all_data_dict[report]["budget_next_year"]:
		meta_data[facility]["budget_next_year"] = u"{}/{}".format(sub_directory, u''.join(filter(lambda x: x in string.printable, all_data_dict[report]["budget_next_year"])))
	else:
		meta_data[facility]["budget_next_year"] = u""
	if all_data_dict[report]["facility_kpi"]:
		meta_data[facility]["facility_kpi"] = u"{}/{}".format(sub_directory, u''.join(filter(lambda x: x in string.printable, all_data_dict[report]["facility_kpi"])))
	else:
		meta_data[facility]["facility_kpi"] = u""

	# Tries to match the facility name with a DB label name
	database_label_name = difflib.get_close_matches(facility, labels_check_dict.keys(), 1)
	reporting_data[facility]["database_label_names"] = database_label_name

# Create excel file and sheets
workbook = xlsxwriter.Workbook('Facility_report_data.xlsx')

bold = workbook.add_format({'bold': True})

worksheet_onepager = workbook.add_worksheet("Onepager_data")
worksheet_onepager.set_column(0, 0, 40)
worksheet_onepager.set_column(1, 1000, 20)
worksheet_db_labels = workbook.add_worksheet("Publications_DB_labels")
worksheet_db_labels.set_column(0,0,90)
worksheet_users = workbook.add_worksheet("Users")
worksheet_users.set_column(0,1000,20)
worksheet_courses = workbook.add_worksheet("Courses")
worksheet_courses.set_column(0,1000,20)
worksheet_events = workbook.add_worksheet("Events")
worksheet_events.set_column(0,1000,20)
worksheet_external = workbook.add_worksheet("External_collab")
worksheet_external.set_column(0,1000,20)
worksheet_additional_funding = workbook.add_worksheet("Additional_funding")
worksheet_additional_funding.set_column(0,1000,30)
worksheet_directors = workbook.add_worksheet("Facility_directors")
worksheet_directors.set_column(0,1000,30)
worksheet_heads = workbook.add_worksheet("Facility_heads")
worksheet_heads.set_column(0,1000,30)
worksheet_ip = workbook.add_worksheet("Immaterial property rights")
worksheet_ip.set_column(0,1000,30)
worksheet_statistics = workbook.add_worksheet("Statistics")
worksheet_statistics.set_column(0,1000,30)

# These are headers not in the reporting data, but are needed for onepagers
additional_headers = ["platform", "scilifelab_funding", "services_bullets", "national_scilifelab_facility_since", "host_university", "asterisk_footnote"]
all_headers = ["facility", "facility_report_id", "budget_next_year", "facility_kpi"]+sorted(reporting_data[reporting_data.keys()[0]])+additional_headers

column_names = list()
for i, header in enumerate(all_headers):
	column_names.append({"header":header})
table_onepager = worksheet_onepager.add_table(
	0, # start row
	0, # start col
	len(reporting_data.keys()), # end row
	4 + len(reporting_data[reporting_data.keys()[0]]) + len(additional_headers) - 1, # end col
	{
		"name": "Onepager_table",
		"columns": column_names
	}
)

for row, facility in enumerate(sorted(reporting_data.keys()),1):
	worksheet_onepager.write(row, 0, facility, bold)
	worksheet_onepager.write_url(row, 1, meta_data[facility]["report_id"], string=meta_data[facility]["report_id"].split("/")[-1])
	if meta_data[facility]["budget_next_year"]:
		worksheet_onepager.write_url(row, 2, "file://"+meta_data[facility]["budget_next_year"], string=meta_data[facility]["budget_next_year"].split("/")[-1])
	if meta_data[facility]["facility_kpi"]:
		worksheet_onepager.write_url(row, 3, "file://"+meta_data[facility]["facility_kpi"], string=meta_data[facility]["facility_kpi"].split("/")[-1])

	for col, item in enumerate(sorted(reporting_data[facility].keys()),4):
		if is_number(unicode(reporting_data[facility][item])):
			worksheet_onepager.write_number(row, col, float(reporting_data[facility][item]))
		else:
			worksheet_onepager.write_string(row, col, unicode(reporting_data[facility][item]))

for i, col_head in enumerate(additional_headers, 4):
	worksheet_onepager.write(0, len(reporting_data[reporting_data.keys()[0]].keys())+i, col_head, bold)

# Writing the DB labels to separate sheet so that user can fill them in
for i, label in enumerate(sorted(labels_check_dict.keys()), 1):
	worksheet_db_labels.write(i, 0, unicode([label]))
worksheet_db_labels.add_table(0,0,len(labels_check_dict.keys()),0, {"columns":[{"header":"Publications DB label. Put one of these in the 'database_label_names' column in the Onepager_data sheet"}]})

user_row = 1
worksheet_users.write(0, 0, "facility", bold)
worksheet_users.write(0, 1, "facility_contact", bold)
worksheet_users.write(0, 2, "user_email", bold)
worksheet_users.write(0, 3, "user_first_name", bold)
worksheet_users.write(0, 4, "user_last_name", bold)
worksheet_users.write(0, 5, "affiliation", bold)
worksheet_users.write(0, 6, "additional_info", bold)
for facility in sorted(reporting_data.keys()):
	for user in reporting_data[facility]["user_all"]:
		worksheet_users.write(user_row, 0, facility)
		worksheet_users.write(user_row, 1, user[0])
		worksheet_users.write(user_row, 2, user[1])
		worksheet_users.write(user_row, 3, user[2])
		worksheet_users.write(user_row, 4, user[3])
		worksheet_users.write(user_row, 5, user[4])
		worksheet_users.write(user_row, 6, user[5])
		user_row += 1
worksheet_users.add_table(0,0,user_row-1,6, {"columns":[
	{"header":"Facility name"},
	{"header":"Facility contact"},
	{"header":"User email"},
	{"header":"User first name"},
	{"header":"User last name"},
	{"header":"Affiliation"},
	{"header":"Additional info"}
]})

courses_row = 1
for facility in sorted(reporting_data.keys()):
	for course in reporting_data[facility]["courses_all"]:
		worksheet_courses.write(courses_row, 0, course[0])
		worksheet_courses.write(courses_row, 1, course[1])
		worksheet_courses.write(courses_row, 2, course[2])
		worksheet_courses.write(courses_row, 3, course[3])
		worksheet_courses.write(courses_row, 4, course[4])
		worksheet_courses.write(courses_row, 5, course[5])
		worksheet_courses.write(courses_row, 6, course[6])
		worksheet_courses.write(courses_row, 7, course[7])
		worksheet_courses.write(courses_row, 8, course[8])
		courses_row += 1
worksheet_courses.add_table(0,0,courses_row-1,8, {"columns":[
	{"header":"Facility name"},
	{"header":"Facility contact"},
	{"header":"Full name of the course"},
	{"header":"Did the reporting unit organize or co-organize the event?"},
	{"header":"If co-organized, with whom?"},
	{"header":"Start date"},
	{"header":"End date"},
	{"header":"Location (city) of the event"},
	{"header":"Comment"}
]})

events_row = 1
for facility in sorted(reporting_data.keys()):
	for event in reporting_data[facility]["events_all"]:
		worksheet_events.write(events_row, 0, event[0])
		worksheet_events.write(events_row, 1, event[1])
		worksheet_events.write(events_row, 2, event[2])
		worksheet_events.write(events_row, 3, event[3])
		worksheet_events.write(events_row, 4, event[4])
		worksheet_events.write(events_row, 5, event[5])
		worksheet_events.write(events_row, 6, event[6])
		worksheet_events.write(events_row, 7, event[7])
		worksheet_events.write(events_row, 8, event[8])
		events_row += 1
worksheet_events.add_table(0,0,events_row-1,8, {"columns":[
	{"header":"Facility name"},
	{"header":"Facility contact"},
	{"header":"Full name of the event"},
	{"header":"Did the reporting unit organize or co-organize the event?"},
	{"header":"If co-organized, with whom?"},
	{"header":"Start date"},
	{"header":"End date"},
	{"header":"Location (city) of the event"},
	{"header":"Comment"}
]})

external_row = 1
for facility in sorted(reporting_data.keys()):
	for external in reporting_data[facility]["external_all"]:
		worksheet_external.write(external_row, 0, external[0])
		worksheet_external.write(external_row, 1, external[1])
		worksheet_external.write(external_row, 2, external[2])
		worksheet_external.write(external_row, 3, external[3])
		worksheet_external.write(external_row, 4, external[4])
		worksheet_external.write(external_row, 5, external[5])
		external_row += 1
worksheet_external.add_table(0,0,external_row-1,5, {"columns":[
	{"header":"Facility name"},
	{"header":"Facility contact"},
	{"header":"Name of external organization"},
	{"header":"Type of organization"},
	{"header":"Reference person"},
	{"header":"Purpose of collabaration/alliance"}
]})

additional_funding_row = 1
for facility in sorted(reporting_data.keys()):
	for item in reporting_data[facility]["additional_funding"]:
		worksheet_additional_funding.write(additional_funding_row,0,facility)
		worksheet_additional_funding.write(additional_funding_row,1,meta_data[facility]["owner"]["email"])
		worksheet_additional_funding.write(additional_funding_row,2,unicode(item[0]))
		worksheet_additional_funding.write(additional_funding_row,3,unicode(item[1]))
		if is_number(unicode(item[2])):
			worksheet_additional_funding.write(additional_funding_row,4,float(item[2]))
		else:
			worksheet_additional_funding.write(additional_funding_row,4,unicode(item[2]))
		additional_funding_row += 1
worksheet_additional_funding.add_table(0,0,additional_funding_row-1,4, {"columns":[{"header":"Facility name"},{"header":"Facility contact"},{"header":"Name of financier"},{"header":"Type of financier"},{"header":"Amount"}]})
directors_row = 1
for facility in sorted(reporting_data.keys()):
	for item in reporting_data[facility]["facility_director"]:
		worksheet_directors.write(directors_row,0,facility)
		worksheet_directors.write(directors_row,1,meta_data[facility]["owner"]["email"])
		worksheet_directors.write(directors_row,2,unicode(item[0]))
		worksheet_directors.write(directors_row,3,unicode(item[1]))
		worksheet_directors.write(directors_row,4,unicode(item[2]))
		directors_row += 1
worksheet_directors.add_table(0,0,directors_row-1,4, {"columns":[{"header":"Facility name"},{"header":"Facility contact"},{"header":"First name"},{"header":"Last name"},{"header":"Affiliation"}]})
heads_row = 1
for facility in sorted(reporting_data.keys()):
	for item in reporting_data[facility]["facility_head"]:
		worksheet_heads.write(heads_row,0,facility)
		worksheet_heads.write(heads_row,1,meta_data[facility]["owner"]["email"])
		worksheet_heads.write(heads_row,2,unicode(item[0]))
		worksheet_heads.write(heads_row,3,unicode(item[1]))
		worksheet_heads.write(heads_row,4,unicode(item[2]))
		heads_row += 1
worksheet_heads.add_table(0,0,heads_row-1,4, {"columns":[{"header":"Facility name"},{"header":"Facility contact"},{"header":"First name"},{"header":"Last name"},{"header":"Affiliation"}]})

ip_row = 1
for facility in sorted(reporting_data.keys()):
	for item in reporting_data[facility]["immaterial_property_rights"]:
		worksheet_ip.write(ip_row,0,facility)
		worksheet_ip.write(ip_row,1,meta_data[facility]["owner"]["email"])
		worksheet_ip.write(ip_row,2,unicode(item[0]))
		worksheet_ip.write(ip_row,3,unicode(item[1]))
		worksheet_ip.write(ip_row,4,unicode(item[2]))
		worksheet_ip.write(ip_row,5,unicode(item[3]))
		worksheet_ip.write(ip_row,6,unicode(item[4]))
		ip_row += 1
worksheet_ip.add_table(0,0,ip_row-1,6, {"columns":[
	{"header":"Facility name"},
	{"header":"Facility contact"},
	{"header":"Patent title"},
	{"header":"Patent application number"},
	{"header":"Filed or granted during 2018?"},
	{"header":"Registered designs"},
	{"header":"Registered trademarks"}
]})

workbook.close()

