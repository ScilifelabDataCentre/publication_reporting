#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import json, sys, time, os, operator, random, urllib
import multiprocessing
import numpy as np

#API for CrossRef
from crossref.restful import Works
#from habanero import Crossref   ##this is an alt lib to get use the Crossref API, slower than the currently used one!

#API for PubMed
from Bio import Entrez

#Creates wordclouds
#import wordcloud
#from PIL import Image

from word_cloud_plotter import word_cloud_plotter

#Plotting libs
import plotly
import plotly.graph_objs as go
import matplotlib
#import matplotlib.pyplot as plt
import colorlover as cl
import networkx as nx


def hex_to_RGB(hex):
    ''' "#FFFFFF" -> [255,255,255] '''
    # Pass 16 to the integer function for change of base
    return [int(hex[i:i+2], 16) for i in range(1,6,2)]
def RGB_to_hex(RGB):
    ''' [255,255,255] -> "#FFFFFF" '''
    # Components need to be integers for hex to make sense
    RGB = [int(x) for x in RGB]
    return "#"+"".join(["0{0:x}".format(v) if v < 16 else
              "{0:x}".format(v) for v in RGB])
def color_dict(gradient):
    ''' Takes in a list of RGB sub-lists and returns dictionary of
      colors in RGB and hex form for use in a graphing function
      defined later on '''
    return {"hex":[RGB_to_hex(RGB) for RGB in gradient],
        "r":[RGB[0] for RGB in gradient],
        "g":[RGB[1] for RGB in gradient],
        "b":[RGB[2] for RGB in gradient]}
def linear_gradient(start_hex, finish_hex="#FFFFFF", n=10):
    ''' returns a gradient list of (n) colors between
      two hex colors. start_hex and finish_hex
      should be the full six-digit color string,
      inlcuding the number sign ("#FFFFFF") '''
    # Starting and ending colors in RGB form
    s = hex_to_RGB(start_hex)
    f = hex_to_RGB(finish_hex)
    # Initilize a list of the output colors with the starting color
    RGB_list = [s]
    # Calcuate a color at each evenly spaced value of t from 1 to n
    for t in range(1, n):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = [
          int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
          for j in range(3)
        ]
        # Add it to our list of output colors
        RGB_list.append(curr_vector)
    return color_dict(RGB_list)
def rand_hex_color(num=1):
    ''' Generate random hex colors, default is one,
        returning a string. If num is greater than
        1, an array of strings is returned. '''
    colors = [
        RGB_to_hex([x*255 for x in np.random.rand(3)])
        for i in range(num)
    ]
    if num == 1:
        return colors[0]
    else:
        return colors
def polylinear_gradient(colors, n):
    ''' returns a list of colors forming linear gradients between
        all sequential pairs of colors. "n" specifies the total
        number of desired output colors '''
    # The number of colors per individual linear gradient
    n_out = int(float(n) / (len(colors) - 1))
    # returns dictionary defined by color_dict()
    gradient_dict = linear_gradient(colors[0], colors[1], n_out)

    if len(colors) > 1:
        for col in range(1, len(colors) - 1):
            next = linear_gradient(colors[col], colors[col+1], n_out)
            for k in ("hex", "r", "g", "b"):
                # Exclude first point to avoid duplicates
                gradient_dict[k] += next[k][1:]
    return gradient_dict




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




### IDEOGRAM FUNCTIONS ###
# I DIDNT WRITE THESE, THEYRE FROM https://plot.ly/python/filled-chord-diagram/

def moduloAB(x, a, b): 
    #maps a real number onto the unit circle identified with 
    #the interval [a,b), b-a=2*PI
    if a>=b:
        raise ValueError('Incorrect interval ends')
    y=(x-a)%(b-a)
    return y+b if y<0 else y+a

def test_2PI(x):
    return 0<= x <2*PI
def get_ideogram_ends(ideogram_len, gap):
    ideo_ends=[]
    left=0
    for k in range(len(ideogram_len)):
        right=left+ideogram_len[k]
        ideo_ends.append([left, right])
        left=right+gap
    return ideo_ends
def make_ideogram_arc(R, phi, a=500):
    # R is the circle radius
    # phi is the list of ends angle coordinates of an arc
    # a is a parameter that controls the number of points to be evaluated on an arc
    if not test_2PI(phi[0]) or not test_2PI(phi[1]):
        phi=[moduloAB(t, 0, 2*PI) for t in phi]
    length=(phi[1]-phi[0])% 2*PI
    nr=10 if length<=PI/4 else int(a*length/PI)
    #print length
    #print nr
    #ADRLAR EDIT!!
    #nr = int(a*length/PI)
    if phi[0] < phi[1]:
        theta=np.linspace(phi[0], phi[1], nr)
    else:
        phi=[moduloAB(t, -PI, PI) for t in phi]
        theta=np.linspace(phi[0], phi[1], nr)
    return R*np.exp(1j*theta)
def map_data(data_matrix, row_value, ideogram_length, L):
    mapped=np.zeros(data_matrix.shape)
    for j  in range(L):
        mapped[:, j]=ideogram_length*data_matrix[:,j]/row_value
    return mapped
def make_ribbon_ends(mapped_data, ideo_ends,  idx_sort):
    L=mapped_data.shape[0]
    ribbon_boundary=np.zeros((L,L+1))
    for k in range(L):
        start=ideo_ends[k][0]
        ribbon_boundary[k][0]=start
        for j in range(1,L+1):
            J=idx_sort[k][j-1]
            ribbon_boundary[k][j]=start+mapped_data[k][J]
            start=ribbon_boundary[k][j]
    return [[(ribbon_boundary[k][j],ribbon_boundary[k][j+1] ) for j in range(L)] for k in range(L)]
def control_pts(angle, radius):
    #angle is a  3-list containing angular coordinates of the control points b0, b1, b2
    #radius is the distance from b1 to the  origin O(0,0)

    if len(angle)!=3:
        raise InvalidInputError('angle must have len =3')
    b_cplx=np.array([np.exp(1j*angle[k]) for k in range(3)])
    b_cplx[1]=radius*b_cplx[1]
    return zip(b_cplx.real, b_cplx.imag)
def ctrl_rib_chords(l, r, radius):
    # this function returns a 2-list containing control poligons of the two quadratic Bezier
    #curves that are opposite sides in a ribbon
    #l (r) the list of angular variables of the ribbon arc ends defining 
    #the ribbon starting (ending) arc 
    # radius is a common parameter for both control polygons
    if len(l)!=2 or len(r)!=2:
        raise ValueError('the arc ends must be elements in a list of len 2')
    return [control_pts([l[j], (l[j]+r[j])/2, r[j]], radius) for j in range(2)]
def make_q_bezier(b):# defines the Plotly SVG path for a quadratic Bezier curve defined by the
                     #list of its control points
    if len(b)!=3:
        raise valueError('control poligon must have 3 points')
    A, B, C=b
    return 'M '+str(A[0])+',' +str(A[1])+' '+'Q '+\
                str(B[0])+', '+str(B[1])+ ' '+\
                str(C[0])+', '+str(C[1])
###THE FOLLOWING IS THE ONLY ONE I EDITED, FUNCTIONALLY. I THINK IT BREAKS WHEN RIBBONS ARE TOO TIGHT
def make_ribbon_arc(theta0, theta1):
    if test_2PI(theta0) and test_2PI(theta1) :
        if theta0 < theta1:
            theta0= moduloAB(theta0, -PI, PI)
            theta1= moduloAB(theta1, -PI, PI)
            if theta0*theta1>0:
                print "Error: Ribbon arc broken" #ADRLAR EDIT: THIS BROKE FOR SOME REASON I COULDNT FIGURE OUT 
                ###raise ValueError('incorrect angle coordinates for ribbon')

        nr=int(40*(theta0-theta1)/PI)
        if nr<=2: nr=3
        theta=np.linspace(theta0, theta1, nr)
        pts=np.exp(1j*theta)# points on arc in polar complex form

        string_arc=''
        for k in range(len(theta)):
            string_arc+='L '+str(pts.real[k])+', '+str(pts.imag[k])+' '
        return   string_arc
    else:
        raise ValueError('the angle coordinates for an arc side of a ribbon must be in [0, 2*pi]')
def make_layout(title, plot_size):
    axis=dict(showline=False, # hide axis line, grid, ticklabels and  title
          zeroline=False,
          showgrid=False,
          showticklabels=False,
          title=None
          )
    return go.Layout(
                  xaxis=dict(axis),
                  yaxis=dict(axis),
                  showlegend=False,
                  width=plot_size, #+int(float(plot_size)/3.3), #Adding for the legend
                  height=int(plot_size*1.05),
                  margin=dict(t=25, b=25, l=25, r=25),
                  hovermode='closest',
                  hoverdistance=250, # ADRLAR EDIT: SET THIS NUMBER HIGHER THAT DEFAULT
                  shapes=[]# to this list one appends below the dicts defining the ribbon,
                           #respectively the ideogram shapes
                 )
def make_ideo_shape(path, line_color, fill_color):
    #line_color is the color of the shape boundary
    #fill_collor is the color assigned to an ideogram
    return  dict(
                  line=dict(
                  color=line_color,
                  width=2
                 ),
            path=  path,
            type='path',
            fillcolor=fill_color,
            layer='below'
        )
def make_ribbon(l, r, line_color, fill_color, radius=0.2):
    #l=[l[0], l[1]], r=[r[0], r[1]]  represent the opposite arcs in the ribbon 
    #line_color is the color of the shape boundary
    #fill_color is the fill color for the ribbon shape
    poligon=ctrl_rib_chords(l,r, radius)
    b,c =poligon

    return  dict(
                line=dict(
                color=line_color, width=2
            ),
            path=  make_q_bezier(b)+make_ribbon_arc(r[0], r[1])+
                   make_q_bezier(c[::-1])+make_ribbon_arc(l[1], l[0]),
            type='path',
            fillcolor=fill_color,
            layer='below'
        )
def make_self_rel(l, line_color, fill_color, radius):
    #radius is the radius of Bezier control point b_1
    b=control_pts([l[0], (l[0]+l[1])/2, l[1]], radius)
    return  dict(
                line=dict(
                color=line_color, width=0.5
            ),
            path=  make_q_bezier(b)+make_ribbon_arc(l[1], l[0]),
            type='path',
            fillcolor=fill_color,
            layer='below'
        )
def invPerm(perm):
    # function that returns the inverse of a permutation, perm
    inv = [0] * len(perm)
    for i, s in enumerate(perm):
        inv[s] = i
    return inv
def ideogram_plot(labels, matrix, filename, plot_size, colorscheme=None):

    L=len(labels)

    #remove the last row and column - they are empty because how I filled the matrix
    
    matrix = matrix[:L,:L]
    

    total_collabs = [np.sum(matrix[i,:]) for i in range(L)]
    
    #testing how it would look with empty ribbons to illustrate single label pubs
    #for i in range(len(total_collabs)):
    #    matrix[i,i]=total_collabs[i]
    #total_collabs = [np.sum(matrix[i,:]) for i in range(L)]


    #set the gap between two consecutive ideograms
    gap=0.0075
    ideogram_length=2*PI*np.asarray(total_collabs)/sum(total_collabs)-gap*np.ones(L)
    #print "IDEOGRAMLENGTH",ideogram_length
    ideo_ends=get_ideogram_ends(ideogram_length, gap)
    #print "IDEOENDS", ideo_ends
    

    #Setting colours, interpolating colours if there are too many labels
    if colorscheme:
        ideo_colors = colorscheme
    else:
        ideo_colors = COLOURS[min(L,12)]
        if L > len(ideo_colors):
            #get the interpolated colours, seems like it can only do set numbers of interpolations
            #between the colours, so adding 24 to the number of labels (L) to get enough colours
            #I shuffle tmp_colors to not get all the similar ones next to each other
            tmp_colors = polylinear_gradient(COLOURS[12],L+24)["hex"]
            random.shuffle(tmp_colors)
            #tmp_colors now includes the originals used for interpolation, but I want those
            #originals first, they are already in ideo_colours, so Im adding the other shuffled ones now
            for col in tmp_colors:
                if col.upper() not in COLOURS[12]:
                    ideo_colors.append(col)
        

    row_sum = total_collabs

    mapped_data=map_data(matrix, total_collabs, ideogram_length, L)
    idx_sort=np.argsort(mapped_data, axis=1)
    ribbon_ends=make_ribbon_ends(mapped_data, ideo_ends,  idx_sort)
    print ideo_colors
    ribbon_color=[L*[ideo_colors[k]] for k in range(L)]

    b=[(1,4), (-0.5, 2.35), (3.745, 1.47)]

    make_q_bezier(b)
    make_ribbon_arc(np.pi/3, np.pi/6)

    layout=make_layout('Chord diagram', plot_size)
    ribbon_info=[] 

    #I had to create this werid workaround because of the fact that the layout["shapes"] is converted to a tuple
    #and I needed it to be appendable, so Im using a list and then inserting it at the end
    weird = list()

    for k in range(L):
        sigma=idx_sort[k]
        sigma_inv=invPerm(sigma)
        for j in range(k, L):
            if matrix[k][j]==0 and matrix[j][k]==0: continue
            eta=idx_sort[j]
            eta_inv=invPerm(eta)
            l=ribbon_ends[k][sigma_inv[j]]

            r=ribbon_ends[j][eta_inv[k]]
            zi=0.9*np.exp(1j*(l[0]+l[1])/2)
            zf=0.9*np.exp(1j*(r[0]+r[1])/2)
            #texti and textf are the strings that will be displayed when hovering the mouse 
            #over the two ribbon ends
            texti=labels[k]+'<br>collaborated on '+ '{}'.format(int(matrix[k][j]))+' publications with <br>'+\
                    labels[j],
            textf=labels[j]+'<br>collaborated on '+ '{}'.format(int(matrix[j][k]))+' publications with <br>'+\
                    labels[k],
            if labels[j] == labels[k]:
                continue
            ribbon_info.append(go.Scatter(x=[zi.real],
                y=[zi.imag],
                mode='markers',
                marker=dict(size=0.5, color='rgb(0,0,0)'),
                text=texti,
                hoverinfo='text',
                showlegend=False,
                hoverlabel=dict(font=dict(size=40))
            )),
            ribbon_info.append(go.Scatter(x=[zf.real],
                y=[zf.imag],
                mode='markers',
                marker=dict(size=0.5, color='rgb(0,0,0)'),
                text=textf,
                hoverinfo='text',
                showlegend=False,
                hoverlabel=dict(font=dict(size=40))
            ))
            r=(r[1], r[0])#IMPORTANT!!!  Reverse these arc ends because otherwise you get
                          # a twisted ribbon
            #WERID workaround explained above: append the ribbon shape
            weird.append((make_ribbon(l, r, 'rgb(0,0,0)' , ribbon_color[k][j])))
    ideograms=[]
    for k in range(len(ideo_ends)):
        z= make_ideogram_arc(1.11, ideo_ends[k])
        zi=make_ideogram_arc(1.01, ideo_ends[k])
        m=len(z)
        n=len(zi)
        ideograms.append(go.Scatter(
            x=z.real,
            y=z.imag,
            mode='lines',
            line=dict(color="rgb(0,0,0)", shape='spline', width=0),
            text=labels[k],#text=labels[k]+'<br>'+'{}'.format(row_sum[k]),
            hoverinfo='text',
            showlegend=False,
            #name='<span style="{}">{}</span>'.format(ideo_colors[k], labels[k]), 
            textfont=dict(color=ideo_colors[k]),
            hoverlabel=dict(font=dict(size=40))
        ))
        path='M '
        for s in range(m):
            path+=str(z.real[s])+', '+str(z.imag[s])+' L '

        Zi=np.array(zi.tolist()[::-1])

        for s in range(m):
            path+=str(Zi.real[s])+', '+str(Zi.imag[s])+' L '
        path+=str(z.real[0])+' ,'+str(z.imag[0])

        #WERID workaround explained above
        weird.append(make_ideo_shape(path,'rgb(0,0,0)' , ideo_colors[k]))

    #Here I am inserting the layout shapes list again
    layout["shapes"] = weird

    data = go.Data(ideograms+ribbon_info)
    fig = go.Figure(data=data, layout=layout)
    config={'showLink': False, "displayModeBar":False}
    plotly.offline.plot(fig, filename='{}_chord_diagram.html'.format(filename), config=config)
    plotly.io.write_image(fig, '{}_chord_diagram.svg'.format(filename))
    plotly.io.write_image(fig, '{}_chord_diagram.png'.format(filename))




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
    plotly.offline.plot(fig, filename='{}_label_numbers_bar.html'.format(prefix), config=config)
    plotly.io.write_image(fig, '{}_label_numbers_bar.svg'.format(prefix))


def word_cloud_plot(word_data, width, height, filename):

    cloud_mask = np.array(Image.open("cloud.png"))

    # cloud_cloud = wordcloud.WordCloud(width=width, height=height, repeat=False, background_color="black", colormap="rainbow", min_font_size=16,mask=cloud_mask)
    # if type(word_data) is unicode:
    #     cloud_cloud.generate(word_data)
    # else:
    #     cloud_cloud.generate_from_frequencies(word_data)

    # plt.imshow(cloud_cloud, interpolation="bilinear")
    # plt.axis("off")
    # plt.savefig(filename+"_cloudshape.eps", dpi=1000, format="eps")
    # plt.savefig(filename+"_cloudshape.svg", dpi=1000, format="svg")
    # plt.savefig(filename+"_cloudshape.png", dpi=1000, format="png")


    # cloud = wordcloud.WordCloud(width=width, height=height, repeat=False, background_color="black", colormap="rainbow", min_font_size=16)
    # if type(word_data) is unicode:
    #     cloud.generate(word_data)
    # else:
    #     cloud.generate_from_frequencies(word_data)

    # plt.imshow(cloud, interpolation="bilinear")
    # plt.axis("off")
    # plt.savefig(filename+".eps", dpi=1000, format="eps")


    # cloud_white = wordcloud.WordCloud(scale=10, width=width, height=height, repeat=False, background_color="white", colormap="viridis", min_font_size=16)
    # if type(word_data) is unicode:
    #     cloud_white.generate(word_data)
    # else:
    #     cloud_white.generate_from_frequencies(word_data)

    # plt.imshow(cloud_white, interpolation="bilinear")
    # plt.axis("off")
    # # fig = plt.gcf() #get current figure
    # # fig.set_size_inches(20, 10)  
    # plt.savefig(filename+"_white_10_2000.png", dpi=2000, format="png")

    cloud_cloud_white = wordcloud.WordCloud(scale=10, width=width, height=height, repeat=False, background_color="white", colormap="viridis", min_font_size=16,mask=cloud_mask)
    if type(word_data) is unicode:
        cloud_cloud_white.generate(word_data)
    else:
        cloud_cloud_white.generate_from_frequencies(word_data)

    plt.imshow(cloud_cloud_white, interpolation="bilinear")
    plt.axis("off")
    # fig = plt.gcf() #get current figure
    # fig.set_size_inches(20, 10)  
    plt.savefig(filename+"_cloudshape_white_10_2000.png", dpi=2000, format="png")
    
if __name__ == "__main__":

    ### GLOBALS ### 

    T_ZERO = time.time()

    PI=np.pi

    #Entrez email setting
    Entrez.email = "adrian.larkeryd@scilifelab.uu.se"

    #Number of threads to use when grabbing CrossRef info
    CROSSREF_THREADS = 16

    #Colourblind friendly colour sets
    COLOURS = {
    1 : ['#4477AA'],
    2 : ['#4477AA', '#CC6677'],
    3 : ['#4477AA', '#DDCC77', '#CC6677'],
    4 : ['#4477AA', '#117733', '#DDCC77', '#CC6677'],
    5 : ['#332288', '#88CCEE', '#117733', '#DDCC77', '#CC6677'],
    6 : ['#332288', '#88CCEE', '#117733', '#DDCC77', '#CC6677', '#AA4499'],
    7 : ['#332288', '#88CCEE', '#44AA99', '#117733', '#DDCC77', '#CC6677', '#AA4499'],
    8 : ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#CC6677', '#AA4499'],
    9 : ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#CC6677', '#882255', '#AA4499'],
    10 : ['#332288', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#661100', '#CC6677', '#882255', '#AA4499'],
    11 : ['#332288', '#6699CC', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#661100', '#CC6677', '#882255', '#AA4499'],
    12 : ['#332288', '#6699CC', '#88CCEE', '#44AA99', '#117733', '#999933', '#DDCC77', '#661100', '#CC6677', '#AA4466', '#882255', '#AA4499'],
    "12-mix" : ['#DDCC77', '#117733', '#6699CC', '#661100', '#882255', '#332288', '#AA4466', '#88CCEE', '#44AA99', '#999933', '#CC6677', '#AA4499']
    }
    COLOURS_SCILIFE = ["#80C41C", "#1E3F32", "#AECE53", "#AEC69C", "#01646B", "#378CAF", "#87B0AB", "#468365"]
    COLOURS_SCILIFE_GREYS = ["#4D4D4D", "#B1B0B1"]

    #This is used to interpolate more colours. Will probably be very bad...
    COLOURS_MORE = [(51,34,136), (102,153,204), (136,204,238), (68,170,153), (17,119,51), (153,153,51), (221,204,119), (102,17,0), (204,102,119), (170,68,102), (136,34,85), (170,68,153)]

    FACILITY_TO_PLATFORM = dict()
    FACILITY_ORDER = list()
    for line in open("facility_platform_conversion_table.tsv", "r"):
        line_split = line.strip().split("\t")
        FACILITY_TO_PLATFORM[line_split[0]] = line_split[1]
        FACILITY_ORDER.append(line_split[0])

    #input_filename = sys.argv[1]

    #json_in = json.loads(open(input_filename, "r").read())

    pub_json_2017 = json.loads(urllib.urlopen("https://publications.scilifelab.se/publications/2017.json").read())
    pub_json_2018 = json.loads(urllib.urlopen("https://publications.scilifelab.se/publications/2018.json").read())
    aff_json_2017 = json.loads(urllib.urlopen("https://publications-affiliated.scilifelab.se/publications/2017.json").read())
    aff_json_2018 = json.loads(urllib.urlopen("https://publications-affiliated.scilifelab.se/publications/2018.json").read())

    input_filename = "2017-2018"

    #print json_in.keys()

    pubs = pub_json_2018["publications"]+pub_json_2017["publications"]
    affs = aff_json_2018["publications"]+aff_json_2017["publications"]
    collection_timestamp = pub_json_2017["timestamp"]
    pub_count = len(pubs)

    source_links = [pub_json_2017["links"]["self"]["href"], pub_json_2018["links"]["self"]["href"], 
        aff_json_2017["links"]["self"]["href"], aff_json_2018["links"]["self"]["href"]] 
    print "Sources:",source_links
    #print "{} publications collected at {} from {}".format(pub_count, collection_timestamp, source_link)
    #print pubs[0].keys()

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



    
    #SORTING THE COLLABORATION MATRIX
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
    for fac in collab_list_sorted:
        if collab_matrix_sorted is not None:
            collab_matrix_sorted = np.hstack([collab_matrix_sorted, collab_matrix_sorted_once[:,[collab_list.index(fac)]]])
        else:
            collab_matrix_sorted = collab_matrix_sorted_once[:,[collab_list.index(fac)]]


    if len(collab_list_platform_number) > len(COLOURS_SCILIFE):
        COLOURS_PLATFORM = COLOURS_SCILIFE + COLOURS[len(collab_list_platform_number)-len(COLOURS_SCILIFE)]
        COLOURS_PLATFORM_ALT = COLOURS["12-mix"] + COLOURS_SCILIFE
    else:
        COLOURS_PLATFORM = COLOURS[12]
        COLOURS_PLATFORM_ALT = COLOURS["12-mix"]

    COLOURS_PLATFORM_SHADES = list()
    COLOURS_PLATFORM_SHADES_ALT = list()
    for i, key in enumerate(collab_list_platform_number):
        towards_black = int(collab_list_platform_number[i][1]/2)
        towards_white = collab_list_platform_number[i][1]-towards_black

        #COLOURS_PLATFORM_SHADES += linear_gradient(COLOURS_PLATFORM[i], "#FFFFFF", collab_list_platform_number[i][1]+1)["hex"][:-1]
        COLOURS_PLATFORM_SHADES_ALT += linear_gradient(COLOURS_PLATFORM_ALT[i], "#FFFFFF", collab_list_platform_number[i][1]+1)["hex"][:-1]
        COLOURS_PLATFORM_SHADES += linear_gradient(COLOURS_PLATFORM[i], "#000000", towards_black+3)["hex"][::-1][2:]
        COLOURS_PLATFORM_SHADES += linear_gradient(COLOURS_PLATFORM[i], "#FFFFFF", towards_white+2)["hex"][:-2][1:]

    #print COLOURS_PLATFORM_SHADES
    
    #GETTING PUBMED INFORMATION
    print "Getting pubmed information..."

    entrez_handle = Entrez.efetch(db="pubmed", retmode="xml", id=','.join(pubmedids))
    entrez_result = Entrez.read(entrez_handle)

    meshterm_descriptor_list = []
    meshterm_qualifier_list = []
    keyword_list = []

    for i in range(len(entrez_result["PubmedArticle"])):
        if "MeshHeadingList" in entrez_result["PubmedArticle"][i]["MedlineCitation"].keys():
            for meshterm in entrez_result["PubmedArticle"][i]["MedlineCitation"]["MeshHeadingList"]:
                if meshterm["QualifierName"]:
                    for meshterm_qualifier in meshterm["QualifierName"]:
                        meshterm_qualifier_list.append(str(meshterm_qualifier))
                if meshterm["DescriptorName"]:
                    meshterm_descriptor_list.append(str(meshterm["DescriptorName"]))

        if entrez_result["PubmedArticle"][i]["MedlineCitation"]["KeywordList"]:
            for keyword in entrez_result["PubmedArticle"][i]["MedlineCitation"]["KeywordList"]:
                for key in keyword:
                    keyword_list.append(unicode(key.upper()).strip())

    entrez_handle = Entrez.efetch(db="pubmed", retmode="xml", id=','.join(aff_pubmedids))
    entrez_result = Entrez.read(entrez_handle)

    aff_meshterm_descriptor_list = []
    aff_meshterm_qualifier_list = []
    aff_keyword_list = []

    for i in range(len(entrez_result["PubmedArticle"])):
        if "MeshHeadingList" in entrez_result["PubmedArticle"][i]["MedlineCitation"].keys():
            for meshterm in entrez_result["PubmedArticle"][i]["MedlineCitation"]["MeshHeadingList"]:
                if meshterm["QualifierName"]:
                    for meshterm_qualifier in meshterm["QualifierName"]:
                        aff_meshterm_qualifier_list.append(str(meshterm_qualifier))
                if meshterm["DescriptorName"]:
                    aff_meshterm_descriptor_list.append(str(meshterm["DescriptorName"]))

        if entrez_result["PubmedArticle"][i]["MedlineCitation"]["KeywordList"]:
            for keyword in entrez_result["PubmedArticle"][i]["MedlineCitation"]["KeywordList"]:
                for key in keyword:
                    aff_keyword_list.append(unicode(key.upper()).strip())



    


    #REMOVING USELESS WORDS FROM THE TITLE CLOUD
    blacklist_for_title_cloud = ["reveal", "associated", "using", "related", "type", "based", "within", "one", "two", "via"]
    for word in blacklist_for_title_cloud:
        titles_for_title_cloud = titles_for_title_cloud.replace(word, "")

    #Generate frequencies for the mesh terms and keywords
    cloud_freq_mesh = {}
    cloud_freq_key = {}
    for word in keyword_list:
        if word in cloud_freq_key.keys():
            cloud_freq_key[word] += 1
        else:
            cloud_freq_key[word] = 1
    for word in meshterm_qualifier_list:
        if word in cloud_freq_mesh.keys():
            cloud_freq_mesh[word] += 1
        else:
            cloud_freq_mesh[word] = 1


    #AFFILIATED CLOUD
    aff_cloud_freq_key = {}
    for word in aff_keyword_list:
        if word in aff_cloud_freq_key.keys():
            aff_cloud_freq_key[word] += 1
        else:
            aff_cloud_freq_key[word] = 1

    print "Generating wordclouds..."
    
    #word_cloud_plot(titles_for_title_cloud, 2000, 1000, "{}_word_cloud_titles".format(input_filename))
    #word_cloud_plot(cloud_freq_mesh, 2000, 1000, "{}_word_cloud_mesh".format(input_filename))
    #word_cloud_plot(cloud_freq_key, 4000, 2000, "{}_word_cloud_key".format(input_filename))
    #word_cloud_plot(aff_cloud_freq_key, 4000, 2000, "{}_word_cloud_key_affiliated".format(input_filename))
    #exit("EXITING PREMATURELY AFTER WORDCLOUD")
    cloud = word_cloud_plotter(cloud_freq_key, 4000, 2000)
    cloud.plot_cloudshape("{}_word_cloud_key".format(input_filename))
    exit("PREMATURELY")

    if collab_list:
        for i in range(len(collab_list)):
            collab_matrix[i,i] = lone_publications[collab_list[i]]
        ideogram_plot(collab_list, collab_matrix, input_filename, 2000)
        ideogram_plot(collab_list_sorted, collab_matrix_sorted, input_filename+"_sorted", 2000, colorscheme=COLOURS_PLATFORM_SHADES)
        for i in range(len(collab_list_sorted)):
            collab_matrix_sorted[i,i] = lone_publications[collab_list_sorted[i]]
        ideogram_plot(collab_list_sorted, collab_matrix_sorted, input_filename+"_sorted_withlone", 2000, colorscheme=COLOURS_PLATFORM_SHADES)
        ideogram_plot(collab_list_sorted, collab_matrix_sorted, input_filename+"_sorted_withlone_colour", 2000, colorscheme=COLOURS_PLATFORM_SHADES_ALT)

    else:
        print "Skipping ideogram plot, no collaborations..."
    if collab_list_platform:
        for i in range(len(collab_list_platform)):
            collab_matrix_platform[i,i] = lone_publications_platorm[collab_list_platform[i]]
        ideogram_plot(collab_list_platform, collab_matrix_platform, input_filename+"_platform", 2000)
    #exit("QUITTING PREMATURELY AFTER IDEOGRAM PLOT")
    


    print "Generating simple plots..."
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
        marker=dict(colors=[COLOURS_SCILIFE[0], COLOURS_SCILIFE[5]], line=dict(color='#000000', width=1)), 
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
    plotly.offline.plot(fig, filename='{}_pie_chart_collab.html'.format(input_filename), config=config)
    plotly.io.write_image(fig, '{}_pie_chart_collab.svg'.format(input_filename))
    plotly.io.write_image(fig, '{}_pie_chart_collab.png'.format(input_filename))

    try:
        collaborative_numbers_data.pop(1)
        collaborative_numbers_data.pop(0)
    except: 
        pass
    pub_barplot(collaborative_numbers_data, input_filename)
    

    sorted_label_count = sorted(label_count.items(), key=operator.itemgetter(1), reverse=True)

    labels = []
    values = []

    for label in sorted_label_count:
        labels.append(label[0])
        values.append(label[1])

    pie_colors = COLOURS[min(len(labels),12)]
    if len(labels) > len(pie_colors):
        #get the interpolated colours, seems like it can only do set numbers of interpolations
        #between the colours, so adding 24 to the number of labels (L) to get enough colours
        #I shuffle tmp_colors to not get all the similar ones next to each other
        tmp_colors = polylinear_gradient(COLOURS[12],len(labels)+24)["hex"]
        #random.shuffle(tmp_colors)
        #tmp_colors now includes the originals used for interpolation, but I want those
        #originals first, they are already in ideo_colours, so Im adding the other shuffled ones now
        for col in tmp_colors:
            if col.upper() not in COLOURS[12]:
                ideo_colors.append(col)

    try:
        trace = go.Pie(
            labels=labels, 
            values=values,
            textinfo="value",
            textposition="inside", 
            marker=dict(colors=COLOURS[8],line=dict(color='#000000', width=1)), 
            textfont=dict(size=30, color='#000000'),
            hoverlabel=dict(font=dict(size=34)),
            sort=False)
    except IndexError as e: #Excepting an index error caused by the colour picking procedure
         trace = go.Pie(labels=labels, 
            values=values,
            marker=dict(line=dict(color='#000000', width=1)), 
            textfont=dict(size=20, color='#000000'),
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
    plotly.offline.plot(fig, filename='{}_pie_chart_all.html'.format(input_filename), config=config)
    plotly.io.write_image(fig, '{}_pie_chart_all.svg'.format(input_filename))
    plotly.io.write_image(fig, '{}_pie_chart_all.png'.format(input_filename))

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
    plotly.offline.plot(fig, filename='{}_pie_chart_other.html'.format(input_filename), config=config)
    plotly.io.write_image(fig, '{}_pie_chart_other.svg'.format(input_filename))
    plotly.io.write_image(fig, '{}_pie_chart_other.png'.format(input_filename))



    #total_collabs = [np.sum(collab_matrix[i,:]) for i in range(len(collab_list))]
    #graph = nx.Graph()
    #for i, node in enumerate(collab_list):
    #    graph.add_node(node)
    #options = {
    #        "node_color":cl.interp(COLOURS_MORE, len(labels)),
    #        "node_size":[i*10000 for i in total_collabs],}
    #plt.subplot(111)
    #nx.draw(graph, with_labels=True, **options)
    #plt.axis("off")
    #plt.savefig("test.png", format="png", dpi=1000)


    trace1 = go.Bar(
        y=['giraffes', 'orangutans', 'monkeys'],
        x=[20, 14, 23],
        name='SF Zoo',
        orientation = 'h',
        marker = dict(
            color = 'rgba(246, 78, 139, 0.6)',
            line = dict(
                color = 'rgba(246, 78, 139, 1.0)',
                width = 3)
        )
    )
    trace2 = go.Bar(
        y=['giraffes', 'orangutans', 'monkeys'],
        x=[12, 18, 29],
        name='LA Zoo',
        orientation = 'h',
        marker = dict(
            color = 'rgba(58, 71, 80, 0.6)',
            line = dict(
                color = 'rgba(58, 71, 80, 1.0)',
                width = 3)
        )
    )

    data = [trace1, trace2]
    layout = go.Layout(
        barmode='stack'
    )

    #fig = go.Figure(data=data, layout=layout)
    #config={'showLink': False, "displayModeBar":False}
    #plotly.offline.plot(fig, filename='{}label_horizontal_bar'.format(input_filename), config=config)
    

    #print "Gathering CrossRef information..."
    #xref_results = xref_stats(dois)

    #print "Information gathered from {} publications\nRefs: {}\nCitations:{}".format(xref_results["Total_num"],xref_results["References"],xref_results["Citations"])
    #print len(dois), len(xref_results["ISSNs"])

    print "time elapsed: {}".format(round(time.time()-T_ZERO, 3))


