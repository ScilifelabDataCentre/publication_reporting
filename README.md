# publication_reporting
Set of python scripts that generate publications visualisation for SciLifeLab reporting reasons including onepager reports for SciLifeLab facilities

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




