#!/usr/bin/env python
# -*- coding: utf-8 -*-

from get_report import facility_reports
from api_key import API_KEY


fcr = facility_reports(api_key=API_KEY)


submitted_reports = fcr.get_reports(status="submitted", return_url=True)

print submitted_reports

print fcr.get_url_json('https://facility-reports.scilifelab.se/api/v1/order/SFR00095')
