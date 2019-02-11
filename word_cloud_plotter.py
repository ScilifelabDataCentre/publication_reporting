#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Adrian Lärkeryd <adrian.larkeryd@scilifelab.uu.se>

import os
import wordcloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

class Word_cloud_plotter(object):
	'''
	Class to handle word cloud plots.
	Should be extended to handle vector based plotting
	https://github.com/SalvaEB/mask_word_cloud maybe use this?? 
	'''
	def __init__(self, words, width=4000, height=2000, scale=10, dpi=2000):
		'''
		Sets up dimensions etc only, the cloud itself will depend on the shape
		and so it is set in the plotting functions
		'''
		self.width = width
		self.height = height
		self.words = words
		self.dict = type(words) is dict # need to handle both cases of string and dict words
		self.scale = scale
		self.dpi = dpi
	def plot_cloudshape(self, filename):
		'''
		Plot a word cloud in a cloud shaped mask
		The file cloud.png is needed to run this, 
		it is a simple cloud shape I drew in Illustrator
		'''
		cloud_mask = np.array(Image.open(os.path.dirname(os.path.realpath(__file__))+"/assets/cloud.png"))
		cloud = wordcloud.WordCloud(scale=self.scale, width=self.width, height=self.height, repeat=False, background_color="white", colormap="viridis", min_font_size=16,mask=cloud_mask)
		if self.dict:
			cloud.generate_from_frequencies(self.words)
		else:
			cloud.generate(self.words)
		plt.imshow(cloud, interpolation="bilinear")
		plt.axis("off")
		plt.savefig(filename+"_cloudshape_white_scale{}_dpi{}.png".format(self.scale, self.dpi), dpi=self.dpi, format="png")

	def plot_rectangle(self, filename):
		'''
		Plot a word cloud in a rectangle shape
		'''
		cloud = wordcloud.WordCloud(scale=self.scale, width=self.width, height=self.height, repeat=False, background_color="white", colormap="viridis", min_font_size=16)
		if self.dict:
			cloud.generate_from_frequencies(self.words)
		else:
			cloud.generate(self.words)
		plt.imshow(cloud, interpolation="bilinear")
		plt.axis("off")
		plt.savefig(filename+"_rectangle_white_scale{}_dpi{}.png".format(self.scale, self.dpi), dpi=self.dpi, format="png")

