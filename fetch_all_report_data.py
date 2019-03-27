#!/usr/bin/env python
# -*- coding: utf-8 -*-

from get_report import facility_reports
from api_key import API_KEY
import os
import json
import pandas as pd
import math

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

# print submitted_report_urls

reports = []

for report in submitted_report_urls:
	print "Fetched:", report
	reports.append(fcr.get_url_json(report))

# print reports

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

# for warning in warnings:
# 	print warning

