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

def showScatterPlots(path = None):
    
    # path = '/home/cudmore/Sites/analyze-flow/exampleData/declan-analysis-20230124.csv'    
    # path = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230125-v0.csv'
    _path = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230127-v2.csv'
    _path = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230206_v2 (1).xlsx'

    if path is None:
        path = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230216-rhc-v2.csv'
 
    # if not os.path.isfile(path):
    #     logger.error(f'did not find path: {path}')
    #     return
    
    # if path.endswith('.csv'):
    #     df = pd.read_csv(path)
    # elif path.endswith('.xlsx'):
    #     df = pd.read_excel(path)
    # else:
    #     _path, _ext = os.path.splitext(path)
    #     logger.info(f'Did not understnd file with extension "{_ext}"')
    #     return
    # print(df.head())

    # df['parentFolder'] = df.parentFolder.astype('str')

    import analyzeflow
    from analyzeflow.bScatterPlotWidget2 import bScatterPlotMainWindow
    interfaceDefaults = {'Y Statistic': 'meanVel',
                        'X Statistic': 'fileIndex',
                        'Hue': 'Sex',
                        'Group By': 'Sex'}

    # parentFolder is condition (saline, fst, morphine)
    # grandParentFolder is date of imaging
    categoricalList = ['Sex', 'Age', 'Surgery Type', 'parentFolder', 'reject']
    #hueTypes = ['Sex', 'Age', 'Surgery Type', 'parentFolder']  # not used???
    hueTypes = None  # not used any more ???
    analysisName = 'Sex'  # 'uniqueFile'
    sortOrder = ['parentFolder', 'dateIndex']
    spw = bScatterPlotMainWindow(path, categoricalList, hueTypes, analysisName,
                sortOrder=sortOrder,
                masterDf=None,
                interfaceDefaults=interfaceDefaults)
    # connect user click of point in scatter to oligoInterface (select a row in table)
    #spw.signalSelectFromPlot.connect(oi.slot_selectFromPlot)
    spw.show()

    return spw

def run0():
    app = QtWidgets.QApplication(sys.argv)
	
    ok = showScatterPlots()

    if ok is not None:
        sys.exit(app.exec_())

if __name__ == '__main__':
    run0()
