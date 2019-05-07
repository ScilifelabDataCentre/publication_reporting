#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import os
import pandas as pd

from reportlab.platypus import BaseDocTemplate, Paragraph, Spacer, Image, PageTemplate, Frame, CondPageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from functools import partial
from svglib.svglib import svg2rlg


responses_file = 'user_survey_data/responses.xlsx'

# Load spreadsheets
responses_xl = pd.ExcelFile(responses_file)

responses_df = responses_xl.parse(responses_xl.sheet_names[0])

# print responses_df

for i, row in responses_df.iterrows():
	response_id = row[0]
	response_name = row[1]
	response_position = row[2]
	response_email = row[3]
	response_affiliation = [x for x in list(row[4:30]) if isinstance(x, basestring)]
	response_prev_platforms = [x for x in list(row[30:38]) if isinstance(x, basestring)]
	response_propose = row[38]
	response_representing = row[39]
	response_description = row[40]
	response_platform_fit = [x for x in list(row[41:50]) if isinstance(x, basestring)]
	response_num_users = row[50]
	response_additional_comments = row[51]
	response_start_date = row[52]
	response_submit_date = row[53]
	response_network_id = row[54]

	print response_affiliation
	print response_prev_platforms
	print response_platform_fit