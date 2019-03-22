#!/usr/bin/env python
# -*- coding: utf-8 -*-

from get_report import facility_reports
from api_key import API_KEY
import os

fcr = facility_reports(api_key=API_KEY)


submitted_report_urls = fcr.get_reports(status="submitted", return_url=True)

# print submitted_report_urls

reports = []

for report in submitted_report_urls:
	print report
	reports.append(fcr.get_url_json(report))

# print reports

cwd = os.getcwd()

directory = cwd+"/fetched_facility_reports"
if not os.path.exists(directory):
	os.makedirs(directory)

for report in reports:
	sub_directory = cwd+"/fetched_facility_reports/"+report["identifier"]
	if not os.path.exists(sub_directory):
		os.makedirs(sub_directory)
	with open("{}/{}.tsv".format(sub_directory, report["identifier"]), 'w') as f:
		for key in report:
			if key == "fields":
				for fkey in report[key]:
					if type(report[key][fkey]) == unicode:
						f.write("{}\t{}".format(fkey, report[key][fkey].encode('utf8')))
					else:
						print fkey, report[key][fkey]
			elif key == "files":

				for fkey in report[key]:
					cwd = os.getcwd()


					# print sub_directory, report[key][fkey]["href"]
					fcr.download_file(report[key][fkey]["href"], sub_directory)
					# print cwd, report[key][fkey]["href"]
					# print fkey, report[key][fkey]
			elif key == "links" or key == "form":
				pass
			else:
				if type(report[key]) == unicode:
					f.write("{}\t{}".format(key, report[key].encode('utf8')))
				else:
					print key, report[key]
	exit()

