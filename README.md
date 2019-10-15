# publication_reporting
Set of python scripts that generate publications visualisation for SciLifeLab reporting reasons including onepager reports for SciLifeLab facilities

### File descriptions

#### 2018_IAB_survey.py
Contains most of the plots for the IAB report. It needs a lot of data files in a folder called excel_data_sheets. This should not be needed at all for next year, the data here was the "handmade" data from OO. Next year data should come from the fetch_all_reports_data.py script.

#### 2018_venn_diagram.py
Has a few venn diagrams created for the IAB report, they were a bit of a late entry so put them in their own script.

#### facility_report_pdf.py
Creates a onepager PDF for each facility based on the file Facility_report_data.xlsx, which is created by fetch_all_report_data.py. It uses facility_reports_plots.py to create the figures, which are inserted in the PDF.

#### facility_report_plots.py
As stated above, creates plots for the onepager PDF.

#### fetch_all_report_data.py
Uses get_report.py to fetch all facility reports, and parses them into Facility_report_data.xlsx. This file is then used by facility_report_pdf.py to create onepagers. The Excel file needs hands on work. 

#### get_report.py
Fetches reports using the API.

#### ideogram.py
Contains functions from plotly, to create an ideogram plot.

#### inventory_survey.py
Creates PDF report for the inventory surveys created by OO. This does not need an input file, it uses the API of the website where the survey is hosted to download the survey data. 

#### issn_files.py
Wrangles the ISSN files, more information on those files and how they are created below.

#### publication_jif_plots.py
Old version of the publication plots for the onepager PDF. Should probably just be removed. 

#### publications_api.py
Class to call the API of publications.scilifelab.se

#### user_survey.py
Generates a set of plots based on the user survey. uses the file user_survey_data/user_survey_parsed.tsv as data source. 

#### word_cloud_plotter.py
Creates the word clouds, used in the IAB report script.

### Installation
This runs under Python 2.7.16

#### python packages
There is a requirements.txt file, but here is a list of packages that need installation in a fresh virtualenv

```
numpy
crossrefapi
biopython
plotly
wordcloud
matplotlib
psutil
matplotlib_venn
pandas
reportlab
svglib
xlrd
xlsxwriter
```

#### Mac matplotlib settings
matplotlib needs a backend set, the easiest way to organise this is to use the matplotlibrc file as follows
```
cat ~/.matplotlib/matplotlibrc
backend: Agg
```

### Required files
These files are all in the assets folder
#### ISSN files 
* ISSN-L-to-ISSN.tsv (https://www.issn.org)
* ISSN-to-ISSN-L.tsv (https://www.issn.org)
* ISSN_impact_2015.tsv (http://webofknowledge.com/)
 - Tab separated col1 ISSN col2 JIF (for some reason the JIF is without a decimal sign, thus 1000x the value)
* ISSN_impact_2016.tsv (http://webofknowledge.com/)
 - Tab separated col1 ISSN col2 JIF (for some reason the JIF is without a decimal sign, thus 1000x the value)
* ISSN_impact_2017.tsv (http://webofknowledge.com/)
 - Tab separated col1 ISSN col2 JIF (for some reason the JIF is without a decimal sign, thus 1000x the value)

Creating the ISSN relevant files:
```
cat ISSN_impact_2015.tsv | cut -f 1 >> ISSNs_that_have_impact.txt
cat ISSN_impact_2016.tsv | cut -f 1 >> ISSNs_that_have_impact.txt
cat ISSN_impact_2017.tsv | cut -f 1 >> ISSNs_that_have_impact.txt
cat ISSNs_that_have_impact.txt | sort | uniq > ISSNs_that_have_impact.txt.sort.uniq

while read f; do grep $f ISSN-L-to-ISSN.tsv >> ISSN-L-to-ISSN.tsv.grepped.1; done < ISSNs_that_have_impact.txt.sort.uniq.1
while read f; do grep $f ISSN-L-to-ISSN.tsv >> ISSN-L-to-ISSN.tsv.grepped.2; done < ISSNs_that_have_impact.txt.sort.uniq.2
while read f; do grep $f ISSN-L-to-ISSN.tsv >> ISSN-L-to-ISSN.tsv.grepped.3; done < ISSNs_that_have_impact.txt.sort.uniq.3
while read f; do grep $f ISSN-L-to-ISSN.tsv >> ISSN-L-to-ISSN.tsv.grepped.4; done < ISSNs_that_have_impact.txt.sort.uniq.4
while read f; do grep $f ISSN-L-to-ISSN.tsv >> ISSN-L-to-ISSN.tsv.grepped.5; done < ISSNs_that_have_impact.txt.sort.uniq.5

while read f; do grep $f ISSN-to-ISSN-L.tsv >> ISSN-to-ISSN-L.tsv.grepped.1; done < ISSNs_that_have_impact.txt.sort.uniq.1
while read f; do grep $f ISSN-to-ISSN-L.tsv >> ISSN-to-ISSN-L.tsv.grepped.2; done < ISSNs_that_have_impact.txt.sort.uniq.2
while read f; do grep $f ISSN-to-ISSN-L.tsv >> ISSN-to-ISSN-L.tsv.grepped.3; done < ISSNs_that_have_impact.txt.sort.uniq.3
while read f; do grep $f ISSN-to-ISSN-L.tsv >> ISSN-to-ISSN-L.tsv.grepped.4; done < ISSNs_that_have_impact.txt.sort.uniq.4
while read f; do grep $f ISSN-to-ISSN-L.tsv >> ISSN-to-ISSN-L.tsv.grepped.5; done < ISSNs_that_have_impact.txt.sort.uniq.5

cat ISSN-to-ISSN-L.tsv.grepped.* > ISSN-to-ISSN-L.tsv.relevant
cat ISSN-L-to-ISSN.tsv.grepped.* > ISSN-L-to-ISSN.tsv.relevant
```

#### Cloud outline
* cloud.png (I drew this, you can draw your own shape if you like, black parts will be filled with words)




