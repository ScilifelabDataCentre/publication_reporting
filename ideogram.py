#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

# This is used in the 2018_IAB script to create the network plot. Source for these functions are plotly, see below.
# I have made some edits

import random
import numpy as np
import plotly
import plotly.graph_objs as go
from colour_science import polylinear_gradient

### IDEOGRAM FUNCTIONS ###
# I DIDNT WRITE THESE, THEYRE FROM https://plot.ly/python/filled-chord-diagram/
def moduloAB(x, a, b): 
    #maps a real number onto the unit circle identified with 
    #the interval [a,b), b-a=2*np.pi
    if a>=b:
        raise ValueError('Incorrect interval ends')
    y=(x-a)%(b-a)
    return y+b if y<0 else y+a
def test_2PI(x):
    return 0<= x <2*np.pi
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
        phi=[moduloAB(t, 0, 2*np.pi) for t in phi]
    length=(phi[1]-phi[0])% 2*np.pi
    nr=10 if length<=np.pi/4 else int(a*length/np.pi)
    #print length
    #print nr
    #ADRLAR EDIT!!
    #nr = int(a*length/np.pi)
    if phi[0] < phi[1]:
        theta=np.linspace(phi[0], phi[1], nr)
    else:
        phi=[moduloAB(t, -np.pi, np.pi) for t in phi]
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
def make_q_bezier(b):
	# defines the Plotly SVG path for a quadratic Bezier curve defined by the
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
            theta0= moduloAB(theta0, -np.pi, np.pi)
            theta1= moduloAB(theta1, -np.pi, np.pi)
            if theta0*theta1>0:
                print "Error: Ribbon arc broken" #ADRLAR EDIT: THIS BROKE FOR SOME REASON I COULDNT FIGURE OUT 
                ###raise ValueError('incorrect angle coordinates for ribbon')

        nr=int(40*(theta0-theta1)/np.pi)
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


def ideogram_plot(labels, matrix, filename, plot_size, colorscheme=None, file_formats=["html"]):
    if type(file_formats) is not list:
        exit("file_format takes a list of file formats to output the plot in")

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
    ideogram_length=2*np.pi*np.asarray(total_collabs)/sum(total_collabs)-gap*np.ones(L)
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
    # print ideo_colors
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

    for file_format in file_formats:
        if file_format == "html":
            plotly.offline.plot(fig, filename='{}_chord_diagram.html'.format(filename), config=config)
        else:
            plotly.io.write_image(fig, '{}_chord_diagram.{}'.format(filename, file_format))
    
