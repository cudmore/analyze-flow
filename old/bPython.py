# Robert H Cudmore
# 20190618

"""
Purpose: Open output blood flow analysis .txt files and analyze/plot the results
"""

import sys, os

import pandas as pd
import numpy as np

folderPath = '/Users/cudmore/box/data/nathan/20190613/Converted'

for file in os.listdir(folderPath):
	if file.endswith('_combined.txt'):
		filePath = os.path.join(folderPath, file)
		df = pd.read_csv(filePath)
		print(df)
