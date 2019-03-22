#!/usr/bin/env python

import requests
import json

class facility_reports(object):
    """
        A class object to make API request easy
    """
    def __init__(self, api_key):
        self.api_headers = {'X-OrderPortal-API-key': api_key}
        self.base_url = "https://facility-reports.scilifelab.se"

    def get_reports(self, status=None, form_title=None, facility=None, return_url=False):
        """Return all report ids or api url if requested"""
        report_list = []
        list_url = "{}/api/v1/orders?".format(self.base_url)
        if status:
            list_url += "status={}".format(status)
        all_reports = self.get_url_json(list_url, raise_error=True)
        for rep in all_reports["items"]:
            if return_url:
                report_list.append(rep["links"]["api"]["href"])
            else:
                report_list.append(rep["identifier"])
        return report_list


    def get_report_url(self, report_id):
        """Generate API url for given report"""
        return "{}/api/v1/order/{}".format(self.base_url, order_id)


    def get_url_json(self, url, raise_error=False):
        """Make a requests get for given URL, validate the response and return JSON"""
        resp = requests.get(url, headers=self.api_headers)
        if resp.status_code != 200:
            if raise_error:
                resp.raise_for_status()
            else:
                return {}
        return resp.json()

    def download_file(self, url, path):
        """Downloads a file from URL, used to download the suppl files to report"""
        local_filename = url.split('/')[-1]
        with requests.get(url, stream=True, headers=self.api_headers) as r:
            r.raise_for_status()
            with open("{}/{}".format(path, local_filename), 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    if chunk:
                        f.write(chunk)
        return local_filename