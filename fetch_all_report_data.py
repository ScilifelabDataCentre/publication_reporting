#!/usr/bin/env python
# -*- coding: utf-8 -*-

from get_report import facility_reports
from api_key import API_KEY
import os
import json
import pandas as pd

fcr = facility_reports(api_key=API_KEY)


submitted_report_urls = fcr.get_reports(status="submitted", return_url=True)

# print submitted_report_urls

reports = []

for report in submitted_report_urls:
	print "Fethced:", report
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
	report_data = dict()
	volume_file = None
	volume_file_backup = None
	
	# Create a subdir for this report, we will download files
	sub_directory = cwd+"/fetched_facility_reports/"+report["identifier"]
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
		print "WARNING: NO EXPLICITLY NAMED VOLUME FILE FOR {}, USING {}".format( report["identifier"], volume_file_backup)
		volume_file = volume_file_backup

	volume_file = "{}/{}".format(sub_directory, volume_file.split("/")[-1])
	# Read the volume data spreadsheet
	volume_xl = pd.ExcelFile(volume_file)
	# print volume_xl.sheet_names
	user_sheet_index = None
	for i, sheet_name in enumerate(volume_xl.sheet_names):
		if "Users" in sheet_name:
			user_sheet_index = i

	if not user_sheet_index:
		raise Exception("No Users tab in Volume data file")

	users_df = volume_xl.parse(volume_xl.sheet_names[user_sheet_index])
	# print users_df

	# Write json data
	with open("{}/{}.json".format(sub_directory, report["identifier"]), 'w') as f:
		json.dump(report_data, f)

	# Save to collected output
	all_reports_data[report["identifier"]] = report_data

with open("{}/all_reports_data.json".format(directory), 'w') as f:
    json.dump(all_reports_data, f)


