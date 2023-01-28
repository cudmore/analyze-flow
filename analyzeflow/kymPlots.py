"""
Jan 2023

For now plotting scatter plots from master csv file
"""
import os
import sys

import pandas as pd

from PyQt5 import QtCore, QtGui, QtWidgets

from analyzeflow import get_logger
logger = get_logger(__name__)

def showScatterPlots():
    
    # path = '/home/cudmore/Sites/analyze-flow/exampleData/declan-analysis-20230124.csv'    
    # path = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230125-v0.csv'
    path = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230127-v2.csv'
    
    if not os.path.isfile(path):
        logger.error(f'did not find path: {path}')
        return
    
    df = pd.read_csv(path)
    # df = df[df.parentFolder != 'Adolescent']
    # df = df.reset_index()
    print(df.head())

    df['parentFolder'] = df.parentFolder.astype('str')

    from bScatterPlotWidget2 import bScatterPlotMainWindow
    interfaceDefaults = {'Y Statistic': 'meanVel',
                        'X Statistic': 'fileIndex',
                        'Hue': 'Sex',
                        'Group By': 'Sex'}

    # parentFolder is condition (saline, fst, morphine)
    # grandParentFolder is date of imaging
    categoricalList = ['Sex', 'Age', 'Surgery Type', 'parentFolder']
    #hueTypes = ['Sex', 'Age', 'Surgery Type', 'parentFolder']  # not used???
    hueTypes = None  # not used any more ???
    analysisName = 'Sex'  # 'uniqueFile'
    sortOrder = ['parentFolder', 'dateIndex']
    spw = bScatterPlotMainWindow(None, categoricalList, hueTypes, analysisName,
                sortOrder=sortOrder,
                masterDf=df,
                interfaceDefaults=interfaceDefaults)
    # connect user click of point in scatter to oligoInterface (select a row in table)
    #spw.signalSelectFromPlot.connect(oi.slot_selectFromPlot)
    spw.show()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
	
    showScatterPlots()

    sys.exit(app.exec_())
