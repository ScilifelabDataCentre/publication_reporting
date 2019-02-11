#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import time, operator
import multiprocessing
import numpy as np

#API for CrossRef
from crossref.restful import Works

#API for PubMed
from Bio import Entrez

#Plotting libs
import plotly
import plotly.graph_objs as go

# My own files
from word_cloud_plotter import Word_cloud_plotter
from ideogram import ideogram_plot
from colour_science import linear_gradient, SCILIFE_COLOURS_NOGREY, COLOURS
from publications_api import Publications_api

def get_xref(doi):
    xrefapi = Works()
    try:
        xref_data = xrefapi.doi(doi)
        if not xref_data:
            print "Could not get data for DOI:", doi
            print xrefapi.doi(doi)
        return xref_data
    except ValueError as e:
        print "Error: {}".format(e)

def xref_stats(dois):
    CROSSREF_THREADS = 16

    stats_dict = {}

    pool = multiprocessing.Pool(processes=CROSSREF_THREADS) # how much parallelism?
    try:
        xref_list = pool.map(get_xref, dois)
    except TypeError:
        print "ERROR getting crossrefs. DOIs:", dois
    total_refs = 0
    total_citations = 0
    total_xrefs = len(xref_list)
    all_issns = list()
    for xref in xref_list:
        if xref:
            #Get the number of references in the papers. Maybe useless
            try:
                total_refs += int(xref["reference-count"])
            except KeyError as e:
                print "XREF ERROR: reference-count", e, xref
            #Get the number of citations in the papers. 
            try:
                total_citations += int(xref["is-referenced-by-count"])
            except KeyError as e:
                print "XREF ERROR: is-referenced-by-count", e, xref
            try: 
                all_issns.append(xref["ISSN"])
            except KeyError as e:
                print "XREF ERROR: ISSN", e, xref
    stats_dict["References"] = total_refs
    stats_dict["Citations"] = total_citations
    stats_dict["Total_num"] = total_xrefs
    stats_dict["ISSNs"] = all_issns
    return stats_dict


### PLOTTING FUNCTIONS ###

def pub_barplot(data_dict, prefix):
    '''
    params:
    data_dict - dictionary of label numbers with number of labels as key and
                number of publications with tha number of labels as value
                example:
                {1: 335, 2: 143, 3: 72, 4: 19, 5: 8, 7: 1}
    prefix -    prefix for file outname, will be prefixed to:
                _label_numbers_bar.html
    '''
    x = data_dict.keys()

    for i in range(len(x)):
        if x[i] == 1:
            x[i] = str(x[i]) + " label"
        else:
            x[i] = str(x[i]) + " labels"

    y = data_dict.values()
    ytext = []

    for val in y:
        ytext.append(str(round(float(val)/float(sum(y)),3)*100) + "%")

    data = [go.Bar(
                x=x,
                y=y,
                text=ytext,
                marker=dict(
                    color=COLOURS[1][0],
                    line=dict(
                        color='#000000',
                        width=1.5),
                ), 
                textfont=dict(
                    family='sans serif',
                    size=48,
                    color='#000000'
                ),
                showlegend=False,
                hoverinfo="none"
    )]
    config={'showLink': False, "displayModeBar":False}
    layout = go.Layout(
        title='Number of labels assigned to publications',
        titlefont=dict(size=58),
        xaxis=dict(
            title="Number of labels",
            titlefont=dict(
                size=54
            ),
            tickfont=dict(
                size=34
            )
        ),
        yaxis=dict(
            titlefont=dict(
                size=54
            ),
            tickfont=dict(
                size=34
            ),
            title="Number of publications"
        ),
        margin = dict(
            r = 10,
            t = 200,
            b = 200,
            l = 200
        ),
        width=2000, #+int(float(plot_size)/3.3), #Adding for the legend
        height=2000,
    )
    fig = go.Figure(data=data, layout=layout)
    # plotly.offline.plot(fig, filename='{}_label_numbers_bar.html'.format(prefix), config=config)
    plotly.io.write_image(fig, '{}_label_numbers_bar.svg'.format(prefix))

def pubmed_wordcloud_info(pubmedids):
    '''
    Takes a list of pubmed IDs and gets all meshterms and keywords from pubmed
    Makes use of the Entrez efetch
    '''
    #Entrez email setting
    Entrez.email = "adrian.larkeryd@scilifelab.uu.se"
    
    entrez_handle = Entrez.efetch(db="pubmed", retmode="xml", id=','.join(pubmedids))
    entrez_result = Entrez.read(entrez_handle)

    # meshterm_descriptor_list = []
    meshterm_qualifier_list = []
    keyword_list = []

    for i in range(len(entrez_result["PubmedArticle"])):
        if "MeshHeadingList" in entrez_result["PubmedArticle"][i]["MedlineCitation"].keys():
            for meshterm in entrez_result["PubmedArticle"][i]["MedlineCitation"]["MeshHeadingList"]:
                if meshterm["QualifierName"]:
                    for meshterm_qualifier in meshterm["QualifierName"]:
                        meshterm_qualifier_list.append(str(meshterm_qualifier).upper().strip())
                # if meshterm["DescriptorName"]:
                #     meshterm_descriptor_list.append(str(meshterm["DescriptorName"]).upper().strip())

        if entrez_result["PubmedArticle"][i]["MedlineCitation"]["KeywordList"]:
            for keyword in entrez_result["PubmedArticle"][i]["MedlineCitation"]["KeywordList"]:
                for key in keyword:
                    keyword_list.append(unicode(key.upper()).strip())

    #Generate frequencies for the mesh terms and keywords
    meshterm_freq = {}
    keyword_freq = {}
    for word in keyword_list:
        if word in keyword_freq.keys():
            keyword_freq[word] += 1
        else:
            keyword_freq[word] = 1

    for word in meshterm_qualifier_list:
        if word in meshterm_freq.keys():
            meshterm_freq[word] += 1
        else:
            meshterm_freq[word] = 1

    return meshterm_freq, keyword_freq
    
if __name__ == "__main__":

    ### GLOBALS ### 

    T_ZERO = time.time()

    FACILITY_TO_PLATFORM = dict()
    FACILITY_ORDER = list()
    for line in open("excel_data_sheets/facility_platform_conversion_table.tsv", "r"):
        line_split = line.strip().split("\t")
        FACILITY_TO_PLATFORM[line_split[0]] = line_split[1]
        FACILITY_ORDER.append(line_split[0])

    # Get the data from publications database
    years = ["2017", "2018"]
    input_filename = "-".join(years)

    pub_getter = Publications_api(years=years)

    pubs = pub_getter.get_publications()
    affs = pub_getter.get_publications_affiliated()

    pub_count = len(pubs)+len(affs)

    print "Sources:", pub_getter.source_links

    dois = []
    all_xrefs = []
    pubmedids = []
    label_count = {}
    xref_by_label = {} #dict of lists, first list element is label count, second is label count with any xref

    #String for gathering all titles, to be used in word cloud later
    titles_for_title_cloud = ""

    #Dict for gathering how many publications have how many lablels
    collaborative_numbers_data = {}
    #count the number of publications each facility did on their own
    lone_publications = {}
    lone_publications_platorm = {}

    #These four will collect the data thats used for the network and chord diagrams
    collab_list = []
    collab_matrix = np.zeros(shape=(1,1))
    collab_list_platform = []
    collab_matrix_platform = np.zeros(shape=(1,1))
  
    #FOR AFFILIATION CLOUD
    aff_titles_for_title_cloud = ""
    aff_dois = []
    aff_pubmedids = []
    
    print "Processing publication data..."

    #FOR AFFILIATION CLOUD
    for pub in affs:
        if pub["doi"] is not None:
            aff_dois.append(pub["doi"])
        if pub["pmid"]:
            aff_pubmedids.append(pub["pmid"])
        aff_titles_for_title_cloud += " " + pub["title"]

    for pub in pubs:
        if pub["doi"] is not None:
            dois.append(pub["doi"])
        xrefs = pub["xrefs"]
        if xrefs is not None:
            all_xrefs.append(xrefs)

        if pub["pmid"]:
            pubmedids.append(pub["pmid"])

        titles_for_title_cloud += " " + pub["title"]

        labels = list(pub["labels"])
        labels_for_collab = list(pub["labels"])
        labels_for_collab_pie = list(pub["labels"])

        #investigating a publication that has 0 labels. will be skipping it. 
        if len(labels) == 0:
            print "Publication without labels in database:",  pub["links"]["self"]["href"]
            continue # SKIPPING all publications without labels. 

        #Merging NGI stockholm into one label in both labels and labels_for_collab
        if "NGI Stockholm (Genomics Applications)" in labels and "NGI Stockholm (Genomics Production)" in labels:
            labels.remove("NGI Stockholm (Genomics Applications)")
            labels.remove("NGI Stockholm (Genomics Production)")
            labels.append("NGI Stockholm")
            labels_for_collab.remove("NGI Stockholm (Genomics Applications)")
            labels_for_collab.remove("NGI Stockholm (Genomics Production)")
            labels_for_collab.append("NGI Stockholm")
            labels_for_collab_pie.remove("NGI Stockholm (Genomics Applications)")
            labels_for_collab_pie.remove("NGI Stockholm (Genomics Production)")
            labels_for_collab_pie.append("NGI Stockholm")

        #IMPLEMENT RULES FOR COLLABORATIVE DATA
        if "Bioinformatics Compute and Storage" in labels:
            labels.remove("Bioinformatics Compute and Storage")
            labels_for_collab.remove("Bioinformatics Compute and Storage")
            labels_for_collab_pie.remove("Bioinformatics Compute and Storage")
            if len(labels) == 0:
                print "Publication without labels after removing Bioinformatics Compute and Storage:", pub["links"]["self"]["href"]
        if "Tissue Profiling" in labels:
            labels.remove("Tissue Profiling")
            labels_for_collab.remove("Tissue Profiling")
            labels_for_collab_pie.remove("Tissue Profiling")
            if len(labels) == 0:
                print "Publication without labels after removing Tissue Profiling:", pub["links"]["self"]["href"]
        if "Clinical Proteomics Mass spectrometry" in labels:
            labels.remove("Clinical Proteomics Mass spectrometry")
            labels_for_collab.remove("Clinical Proteomics Mass spectrometry")
            labels_for_collab_pie.remove("Clinical Proteomics Mass spectrometry")
            if len(labels) == 0:
                print "Publication without labels after removing Clinical Proteomics Mass spectrometry:", pub["links"]["self"]["href"]
        if "Fluorescence Tissue Profiling" in labels:
            labels.remove("Fluorescence Tissue Profiling")
            labels_for_collab.remove("Fluorescence Tissue Profiling")
            labels_for_collab_pie.remove("Fluorescence Tissue Profiling")
            if len(labels) == 0:
                print "Publication without labels after removing Flourescence Tissue Profiling:", pub["links"]["self"]["href"]
        if "Mass Spectrometry-based Proteomics, Uppsala" in labels:
            labels.remove("Mass Spectrometry-based Proteomics, Uppsala")
            labels_for_collab.remove("Mass Spectrometry-based Proteomics, Uppsala")
            labels_for_collab_pie.remove("Mass Spectrometry-based Proteomics, Uppsala")
            if len(labels) == 0:
                print "Publication without labels after removing Mass Spectrometry-based Proteomics, Uppsala:", pub["links"]["self"]["href"]

        #Handle NGI collaborations, ie dont show them in pie
        #Im just going to keep one of the labels, the first one. Will handle it differently in the Chord plot. 
        if "NGI Stockholm" in labels_for_collab_pie and "NGI Uppsala (SNP&SEQ Technology Platform)" in labels_for_collab_pie:
            labels_for_collab_pie.remove("NGI Uppsala (SNP&SEQ Technology Platform)")
        # if "NGI Stockholm" in labels_for_collab_pie and "NGI Uppsala (Uppsala Genome Center)" in labels_for_collab_pie:
        #     labels_for_collab_pie.remove("NGI Uppsala (Uppsala Genome Center)")
        # if "NGI Uppsala (SNP&SEQ Technology Platform)" in labels_for_collab_pie and "NGI Uppsala (Uppsala Genome Center)" in labels_for_collab_pie:
        #     labels_for_collab_pie.remove("NGI Uppsala (Uppsala Genome Center)")

        #Handle NBIS collaborations, ie dont show them in pie
        if "Bioinformatics Long-term Support WABI" in labels_for_collab_pie and "Bioinformatics Support and Infrastructure" in labels_for_collab_pie:
            labels_for_collab_pie.remove("Bioinformatics Support and Infrastructure")
        if "Bioinformatics Long-term Support WABI" in labels_for_collab_pie and "Systems Biology" in labels_for_collab_pie:
            labels_for_collab_pie.remove("Systems Biology")
        if "Bioinformatics Support and Infrastructure" in labels_for_collab_pie and "Systems Biology" in labels_for_collab_pie:
            labels_for_collab_pie.remove("Systems Biology")

        #intantiate the lone publications dictionary entries
        labels_platform = list()
        for label in labels:
            if label not in lone_publications.keys():
                lone_publications[label] = 0
            if FACILITY_TO_PLATFORM[label] not in lone_publications_platorm.keys():
                lone_publications_platorm[FACILITY_TO_PLATFORM[label]] = 0
            if FACILITY_TO_PLATFORM[label] not in labels_platform:
                labels_platform.append(FACILITY_TO_PLATFORM[label])

        #then add to the lone pubs dict if it is in fact a lone pub
        if len(labels) == 1:
            lone_publications[labels[0]] += 1
        if len(labels_platform) == 1:
            lone_publications_platorm[FACILITY_TO_PLATFORM[labels[0]]] += 1

        #then we start counting collaborative numbers
        if len(labels_for_collab_pie) in collaborative_numbers_data.keys():
            collaborative_numbers_data[len(labels_for_collab_pie)] += 1
        else:
            collaborative_numbers_data[len(labels_for_collab_pie)] = 1

        #This is for the collaborative matrix based on platforms instead of facilities
        platform_collaborations = list()
        for label in labels_for_collab:
            if FACILITY_TO_PLATFORM[label] not in platform_collaborations:
                platform_collaborations.append(FACILITY_TO_PLATFORM[label])
        while len(platform_collaborations)>1:
            current_platform = platform_collaborations.pop(0)
            if current_platform not in collab_list_platform:
                #add to collaborator list
                collab_list_platform.append(current_platform)
                collab_matrix_platform = np.vstack([collab_matrix_platform, np.zeros(shape=(len(collab_list_platform)))])
                collab_matrix_platform = np.hstack([collab_matrix_platform, np.zeros(shape=(len(collab_list_platform)+1, 1))])

            for remaining_platform in platform_collaborations:
                if remaining_platform not in collab_list_platform:
                    collab_list_platform.append(remaining_platform)
                    collab_matrix_platform = np.vstack([collab_matrix_platform, np.zeros(shape=(len(collab_list_platform)))])
                    collab_matrix_platform = np.hstack([collab_matrix_platform, np.zeros(shape=(len(collab_list_platform)+1, 1))])

                collab_matrix_platform[collab_list_platform.index(current_platform), collab_list_platform.index(remaining_platform)] += 1
                collab_matrix_platform[collab_list_platform.index(remaining_platform), collab_list_platform.index(current_platform)] += 1

        #count labels with xrefs
        for label in labels:
            if label in label_count.keys():
                label_count[label] += 1
                xref_by_label[label][0] += 1
                if xrefs:
                    xref_by_label[label][1] += 1
            else:
                label_count[label] = 1
                xref_by_label[label] = [1,0]
                if xrefs:
                    xref_by_label[label][1] += 1

        #and finally add information to the collaboration matrix and the collaborator list
        while len(labels_for_collab)>1:
            current = labels_for_collab.pop(0)
            if current not in collab_list:
                #add to collaborator list
                collab_list.append(current)
                collab_matrix = np.vstack([collab_matrix, np.zeros(shape=(len(collab_list)))])
                collab_matrix = np.hstack([collab_matrix, np.zeros(shape=(len(collab_list)+1, 1))])

            for remaining in labels_for_collab:
                if remaining not in collab_list:
                    collab_list.append(remaining)
                    collab_matrix = np.vstack([collab_matrix, np.zeros(shape=(len(collab_list)))])
                    collab_matrix = np.hstack([collab_matrix, np.zeros(shape=(len(collab_list)+1, 1))])
                #Handle NGI collaborations, ie dont show those ribbons
                if "NGI Stockholm" in [current, remaining] and "NGI Uppsala (SNP&SEQ Technology Platform)" in [current, remaining]:
                    continue
                # if "NGI Stockholm" in [current, remaining] and "NGI Uppsala (Uppsala Genome Center)" in [current, remaining]:
                #     continue
                # if "NGI Uppsala (SNP&SEQ Technology Platform)" in [current, remaining] and "NGI Uppsala (Uppsala Genome Center)" in [current, remaining]:
                #     continue
                #Handle NBIS collaborations, ie dont show those ribbons
                if "Bioinformatics Long-term Support WABI" in [current, remaining] and "Bioinformatics Support and Infrastructure" in [current, remaining]:
                    continue
                if "Bioinformatics Long-term Support WABI" in [current, remaining] and "Systems Biology" in [current, remaining]:
                    continue
                if "Bioinformatics Support and Infrastructure" in [current, remaining] and "Systems Biology" in [current, remaining]:
                    continue
                collab_matrix[collab_list.index(current), collab_list.index(remaining)] += 1
                collab_matrix[collab_list.index(remaining), collab_list.index(current)] += 1

    
    #GETTING PUBMED INFORMATION
    print "Getting pubmed information for word clouds..."
    # cloud_freq_mesh, cloud_freq_key = pubmed_wordcloud_info(pubmedids)
    aff_cloud_freq_mesh, aff_cloud_freq_key = pubmed_wordcloud_info(aff_pubmedids)

    #REMOVING USELESS WORDS FROM THE TITLE CLOUD
    blacklist_for_title_cloud = ["reveal", "associated", "using", "related", "type", "based", "within", "one", "two", "via"]
    for word in blacklist_for_title_cloud:
        titles_for_title_cloud = titles_for_title_cloud.replace(word, "")

    print "Generating wordclouds..."

    # cloud = Word_cloud_plotter(cloud_freq_key, 4000, 2000)
    # cloud.plot_cloudshape("{}_word_cloud_key".format(input_filename))
    # cloud.plot_rectangle("{}_word_cloud_key".format(input_filename))
    # cloud = Word_cloud_plotter(titles_for_title_cloud, 4000, 2000)
    # cloud.plot_cloudshape("{}_word_cloud_title".format(input_filename))
    # cloud.plot_rectangle("{}_word_cloud_title".format(input_filename))
    # cloud = Word_cloud_plotter(cloud_freq_mesh, 4000, 2000)
    # cloud.plot_cloudshape("{}_word_cloud_mesh".format(input_filename))
    # cloud.plot_rectangle("{}_word_cloud_mesh".format(input_filename))
    cloud = Word_cloud_plotter(aff_cloud_freq_key, 4000, 2000)
    cloud.plot_cloudshape("{}_word_cloud_key_affiliated".format(input_filename))
    # cloud.plot_rectangle("{}_word_cloud_key_affiliated".format(input_filename))


    # IDEOGRAM PLOTS AND THE SETUP FOR THEM
    print "Ideogram plot..."
    # SORTING THE COLLABORATION MATRIX
    #We need to sort once by row and once by column, first vstack then hstack
    collab_matrix_sorted_once = None
    collab_list_sorted = list()
    collab_list_platform_number = list() #going to use this to colorise properly
    for fac in FACILITY_ORDER:
        if fac in collab_list:
            if collab_list_platform_number:
                if FACILITY_TO_PLATFORM[fac] == collab_list_platform_number[-1][0]:
                    collab_list_platform_number[-1][1] += 1
                else:
                    collab_list_platform_number.append([FACILITY_TO_PLATFORM[fac],1])
            else:
                collab_list_platform_number = [[FACILITY_TO_PLATFORM[fac],1]]
            collab_list_sorted.append(fac) #we only need to do this once, the order will be the same next sort iteration
            if collab_matrix_sorted_once is not None:
                collab_matrix_sorted_once = np.vstack([collab_matrix_sorted_once, collab_matrix[collab_list.index(fac),:]])
            else:
                collab_matrix_sorted_once = collab_matrix[collab_list.index(fac),:]
    collab_matrix_sorted = None
    # Second sort:
    for fac in collab_list_sorted:
        if collab_matrix_sorted is not None:
            collab_matrix_sorted = np.hstack([collab_matrix_sorted, collab_matrix_sorted_once[:,[collab_list.index(fac)]]])
        else:
            collab_matrix_sorted = collab_matrix_sorted_once[:,[collab_list.index(fac)]]

    # Set up colours for ideogram
    if len(collab_list_platform_number) > len(SCILIFE_COLOURS_NOGREY):
        COLOURS_PLATFORM = SCILIFE_COLOURS_NOGREY + COLOURS[len(collab_list_platform_number)-len(SCILIFE_COLOURS_NOGREY)]
        COLOURS_PLATFORM_ALT = COLOURS["12-mix"] + SCILIFE_COLOURS_NOGREY
    else:
        COLOURS_PLATFORM = COLOURS[12]
        COLOURS_PLATFORM_ALT = COLOURS["12-mix"]
    COLOURS_PLATFORM_SHADES = list()
    COLOURS_PLATFORM_SHADES_ALT = list()
    for i, key in enumerate(collab_list_platform_number):
        towards_black = int(collab_list_platform_number[i][1]/2)
        towards_white = collab_list_platform_number[i][1]-towards_black

        COLOURS_PLATFORM_SHADES_ALT += linear_gradient(COLOURS_PLATFORM_ALT[i], "#FFFFFF", collab_list_platform_number[i][1]+1)["hex"][:-1]
        COLOURS_PLATFORM_SHADES += linear_gradient(COLOURS_PLATFORM[i], "#000000", towards_black+3)["hex"][::-1][2:]
        COLOURS_PLATFORM_SHADES += linear_gradient(COLOURS_PLATFORM[i], "#FFFFFF", towards_white+2)["hex"][:-2][1:]

    # Plot ideogram finally...
    if collab_list:
        for i in range(len(collab_list)):
            collab_matrix[i,i] = lone_publications[collab_list[i]]
        ideogram_plot(collab_list, collab_matrix, input_filename, 2000, file_formats=["svg"])
        # ideogram_plot(collab_list_sorted, collab_matrix_sorted, input_filename+"_sorted", 2000, colorscheme=COLOURS_PLATFORM_SHADES, file_formats=["svg"])
        for i in range(len(collab_list_sorted)):
            collab_matrix_sorted[i,i] = lone_publications[collab_list_sorted[i]]
        # ideogram_plot(collab_list_sorted, collab_matrix_sorted, input_filename+"_sorted_withlone", 2000, colorscheme=COLOURS_PLATFORM_SHADES, file_formats=["svg"])
        ideogram_plot(collab_list_sorted, collab_matrix_sorted, input_filename+"_sorted_withlone_colour", 2000, colorscheme=COLOURS_PLATFORM_SHADES_ALT, file_formats=["svg"])
    else:
        print "Skipping ideogram plot, no collaborations..."
    if collab_list_platform:
        for i in range(len(collab_list_platform)):
            collab_matrix_platform[i,i] = lone_publications_platorm[collab_list_platform[i]]
        ideogram_plot(collab_list_platform, collab_matrix_platform, input_filename+"_platform", 2000, file_formats=["svg"])
    

    # OTHER PLOTS
    print "Generating simple plots..."

    # Collaborative pie chart, single vs multiple labels on a publication
    collaborative_pie_data = [0,0]
    for key in collaborative_numbers_data.keys():
        if key == 1:
            collaborative_pie_data[0]=collaborative_numbers_data[key]
        else:
            collaborative_pie_data[1]+=collaborative_numbers_data[key]
    trace = go.Pie(
        labels=["Single facility","Multiple facilities"], 
        values=collaborative_pie_data,
        textinfo="value",
        marker=dict(colors=[SCILIFE_COLOURS_NOGREY[0], SCILIFE_COLOURS_NOGREY[5]], line=dict(color='#000000', width=1)), 
        textfont=dict(size=80, color='#000000'),
        hoverlabel=dict(font=dict(size=34)),
        sort=False
    )
    layout = go.Layout(
        title='Publications made by multiple facility collaborations',
        titlefont=dict(size=58),
        margin = dict(
            r = 10,
            t = 200,
            b = 200,
            l = 200
        ),
        legend=dict(font=dict( family='sans-serif', size=32, color='#000' )),
        width=2000, 
        height=2000,
    )
    fig = go.Figure(data=[trace], layout=layout)
    config={'showLink': False, "displayModeBar":False}
    # plotly.offline.plot(fig, filename='{}_pie_chart_collab.html'.format(input_filename), config=config)
    # plotly.io.write_image(fig, '{}_pie_chart_collab.png'.format(input_filename))
    plotly.io.write_image(fig, '{}_pie_chart_collab.svg'.format(input_filename))

    # Barplot for the same collaborative numbers
    # Remove the publications with 0 and 1 labels in this case
    try:
        collaborative_numbers_data.pop(1)
        collaborative_numbers_data.pop(0)
    except: 
        pass
    pub_barplot(collaborative_numbers_data, input_filename)
    
    # Pie chart of all labels
    # Sort according to size first
    sorted_label_count = sorted(label_count.items(), key=operator.itemgetter(1), reverse=True)
    labels = []
    values = []
    for label in sorted_label_count:
        labels.append(label[0])
        values.append(label[1])
    trace = go.Pie(
        labels=labels, 
        values=values,
        textinfo="value",
        textposition="inside", 
        marker=dict(colors=COLOURS[8],line=dict(color='#000000', width=1)), 
        textfont=dict(size=30, color='#000000'),
        hoverlabel=dict(font=dict(size=34)),
        sort=False)
    layout = go.Layout(
        title='Number of publications per label',
        titlefont=dict(size=58),
        margin = dict(
            r = 10,
            t = 200,
            b = 200,
            l = 200
        ),
        legend=dict(font=dict( family='sans-serif', size=32, color='#000' )),
        width=2000, 
        height=2000,
    )
    fig = go.Figure(data=[trace], layout=layout)
    config={'showLink': False, "displayModeBar":False}
    # plotly.offline.plot(fig, filename='{}_pie_chart_all.html'.format(input_filename), config=config)
    # plotly.io.write_image(fig, '{}_pie_chart_all.png'.format(input_filename))
    plotly.io.write_image(fig, '{}_pie_chart_all.svg'.format(input_filename))

    # Same pie chart as previously, but only plot the largest 11 labels, 
    # put the rest together in an "Other" label
    labels = []
    values = []
    for label in sorted_label_count:
        if len(labels)<11:
            labels.append(label[0])
            values.append(label[1])
        elif len(labels) == 11:
            labels.append("Other")
            values.append(label[1])
        else:
            values[-1] += label[1]

    trace = go.Pie(labels=labels, 
            values=values,
            textinfo="value",
            textposition="inside",
            marker=dict(colors=COLOURS[12], line=dict(color='#000000', width=1)), 
            textfont=dict(size=30, color='#000000'),
            hoverlabel=dict(font=dict(size=34)),
            sort=False)
    fig = go.Figure(data=[trace], layout=layout)
    config={'showLink': False, "displayModeBar":False}
    # plotly.offline.plot(fig, filename='{}_pie_chart_other.html'.format(input_filename), config=config)
    # plotly.io.write_image(fig, '{}_pie_chart_other.png'.format(input_filename))
    plotly.io.write_image(fig, '{}_pie_chart_other.svg'.format(input_filename))

    # DONE
    print "time elapsed: {}".format(round(time.time()-T_ZERO, 3))