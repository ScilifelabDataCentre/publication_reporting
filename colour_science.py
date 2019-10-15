#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This is used in the 2018_IAB_plots.py script to handle colours

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
SCILIFE_COLOURS = ["#80C41C", "#1E3F32", "#AECE53", "#AEC69C", "#4D4D4D", "#B1B0B1", "#01646B", "#378CAF", "#87B0AB", "#468365"]
SCILIFE_COLOURS_NOGREY = ["#80C41C", "#1E3F32", "#AECE53", "#AEC69C", "#01646B", "#378CAF", "#87B0AB", "#468365"]
SCILIFE_COLOURS_GREYS = ["#4D4D4D", "#B1B0B1"]

FACILITY_USER_AFFILIATION_COLOUR_OFFICIAL = {
	u"Chalmers University of Technology": "#006C5C", #https://www.chalmers.se/SiteCollectionDocuments/om%20chalmers%20dokument/Grafisk%20profil/Chalmers_visuella_identitet_1.0_2018.pdf
	u"Karolinska Institutet": "#870052", #https://ki.se/medarbetare/farger-i-kis-grafiska-profil
	u"KTH Royal Institute of Technology": "#1954A6", #https://intra.kth.se/administration/kommunikation/grafiskprofil/profilfarger-for-print-1.845077
	u"Linköping University": "#00B9E7", #https://insidan.liu.se/kommunikationsstod/grafiskprofil/start/1.635075/LiU_Grafisk_manual_171117.pdf
	u"Lund University": "#9C6114", #https://www.medarbetarwebben.lu.se/sites/medarbetarwebben.lu.se/files/lu-grafisk-manual150820.pdf
	u"Stockholm University": "#002F5F", #https://www.su.se/medarbetare/kommunikation/grafisk-manual/f%C3%A4rger-1.362110
	u"Swedish University of Agricultural Sciences": "#00664F", #https://internt.slu.se/riktat/malgrupp/kommunikator/varumarkesmanual/visuell-identitet/farger/identitetsfarger/
	u"Umeå University": "#2A4765", #https://www.aurora.umu.se/stod-och-service/kommunikation/grafisk-profil/
	u"University of Gothenburg": "#004B89", #https://medarbetarportalen.gu.se/Kommunikation/visuell-identitet/grundprofil/farger/
	u"Uppsala University": "#990000", #https://mp.uu.se/documents/432512/911394/Grafiska+riktlinjerokt2018.pdf/b4c90d05-2cc7-d59e-b0af-c357fb33c84b

	u"Naturhistoriska Riksmuséet": "#408EBF", # NOT official I pulled it from the logo at http://www.nrm.se/

	u"Healthcare": "#FF99DD", #pink
	u"Industry": "#9FA1A3", #grey
	u"International University": "#91D88C", #light green
	u"Other international organization": "#FFFF99", #yellow
	u"Other Swedish organization": "#B15928", #burnt orange
	u"Other Swedish University": "#FF7C5B" #red orange
}

#Author of colour gradient stuff: Ben Southgate https://bsou.io/posts/color-gradients-with-python

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