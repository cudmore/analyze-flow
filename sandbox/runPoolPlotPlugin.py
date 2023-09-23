"""
Run SanPy pool plot plugin on a folder of folders of kym flow analysis.
"""
import os
import sys
import glob

import pandas as pd

from PyQt5 import QtCore, QtWidgets, QtGui

import analyzeflow

import sanpy

from sanpy.sanpyLogger import get_logger
logger = get_logger(__name__)

def getMasterDf(path, rosettaDatabase = None):
    """Given a folder of raw data, get a master pandas dataframe, one row per tif file.
    """
    
    # database with declans markings like:
    """
    Surgery Type
    Genotype
    Sex
    Age
    Order
    Direction
    Depth
    Quality
    """
    dfRosetta = None
    if rosettaDatabase is not None:
        dfRosetta = pd.read_csv(rosettaDatabase)
        print('dfRosetta is:')
        print(dfRosetta)
    
    files = glob.glob(os.path.join(path, "**/*.tif"))
    logger.info(f'num files: {len(files)}')
    
    dfMaster = pd.DataFrame()

    numFoundInRosetta = 0
    for idx, file in enumerate(files):
        ba = sanpy.bAnalysis(file)
        
        kff = analyzeflow.kymFlowFile(ba=ba, loadTif=False)
        
        oneDict = kff.getReport()
        oneDf = pd.DataFrame([oneDict])  # dataframe from dict, keys are columns
        
        oneDf['File Number'] = idx
        
        # parentFolder = oneDf['parentFolder']
        # file = oneDf['file']
        # _uniqueName = parentFolder + '/' + file
          
        oneDf['Unique Name'] = oneDf['uniqueFile']
        
        # look up in rosetta and get Colins markings
        if dfRosetta is not None:
            uniqueFile = oneDf.at[0, 'uniqueFile']
            #print(f'looking for uniqueFile: {uniqueFile}')
            # rosetta row is a dataframe
            rosettaRow = dfRosetta.loc[dfRosetta['uniqueFile'] == uniqueFile]
            if len(rosettaRow) > 1:
                logger.error('{idx} got more than two rows for {uniqueFile} in rosetta !!!')
                continue
            if len(rosettaRow) == 0:
                # logger.error(f'{idx} did not find {uniqueFile} in rosetta !!!')
                oneDf['Include'] = 'no'
            
            else:
                _genotype = rosettaRow.iloc[0]['Genotype']  # iloc[0] to get first row in DataFrame
                oneDf['Genotype'] = _genotype
                
                _sex = rosettaRow.iloc[0]['Sex']  # iloc[0] to get first row in DataFrame
                oneDf['Sex'] = _sex
                
                _age = rosettaRow.iloc[0]['Age']  # iloc[0] to get first row in DataFrame
                oneDf['Age'] = _age
                
                numFoundInRosetta += 1
            
            # print('idx:', idx, '_genotype:', _genotype, type(_genotype))
            # sys.exit(1)
            
        #
        # append is depreciated
        # dfMaster = dfMaster.append(oneReporDict, ignore_index=True)
        dfMaster = pd.concat([dfMaster, oneDf], ignore_index=True)
    
    logger.info(f'found {numFoundInRosetta} out of {len(files)} in rosetta')
        
    return dfMaster

# need to define like in sanpy.bAnalysisUtil
def getFlowStatList():
    statList = {}  #OrderedDict()
    statList["Points Per Line"] = {
        "name": "pntsPerLine"
    }
    statList["Num Lines"] = {
        "name": "numLines"
    }
    statList["Seconds Per Line Line"] = {
        "name": "delt"
    }
    statList["um Per Point"] = {
        "name": "delx"
    }
    statList["Total Dur (s)"] = {
        "name": "Total Dur (s)"
    }
    statList["Line Length (um)"] = {
        "name": "Line Length (um)"
    }
    # image stats
    statList["Mean Image Intensity"] = {
        "name": "meanInt"
    }
    statList["Min Image Intensity"] = {
        "name": "minInt"
    }
    statList["Max Image Intensity"] = {
        "name": "maxInt"
    }
    statList["Range Image Intensity"] = {
        "name": "rangeInt"
    }
    # velocity
    statList["Mean Velocity"] = {
        "name": "meanVel"
    }
    statList["Min Velocity"] = {
        "name": "minVel"
    }
    statList["Max Velocity"] = {
        "name": "maxVel"
    }
    statList["STD Velocity"] = {
        "name": "stdVel"
    }
    statList["CV Velocity"] = {
        "name": "cvVel"
    }
    statList["Median Velocity"] = {
        "name": "medianVel"
    }
    statList["Sign Mean Velocity"] = {
        "name": "signMeanVel"
    }
    statList["Pos and Neg Velocity"] = {
        "name": "posNegVel"
    }

    #
    return statList

if __name__ == '__main__':
    
    path = '/media/cudmore/data/Dropbox/data/declan/data20230916'
    rosettaDatabase = '/media/cudmore/data/Dropbox/data/declan/data20230916/Baseline_Bloodflow_Master_Rosetta.csv'
    dfMaster = getMasterDf(path, rosettaDatabase)
        
    logger.info(f'df master columns are:')
    print(dfMaster.columns)

    # run sanpy pool plot plugin !!!!
    import sanpy
    from sanpy.interface import bScatterPlotMainWindow
    
    import sys
    app = QtWidgets.QApplication([])
    
    # this needs work, in particular how it is grabbing AP stats (not needed here) !!!
    # ptp = plotToolPool(tmpMasterDf=dfMaster)
    # ptp.show()

    categoricalList = sanpy.MetaData.getMetaDataDict().keys()
    categoricalList = list(categoricalList)
    categoricalList.append('File Number')
    categoricalList.append('Unique Name')

    sortOrder = ["Sex", "Condition1", "Condition2", "Unique Name"]
    statListDict = getFlowStatList()
    # limitToCol = ["epoch"]
    
    interfaceDefaults = {
        "Y Statistic": "Mean Velocity",
        "X Statistic": "CV Velocity",
        # "Hue": "region",
        # "Group By": "File Number",
    }
    
    path = ''
    mainWidget2 = sanpy.interface.bScatterPlotMainWindow(
            path,
            categoricalList,
            # hueTypes,
            # analysisName,  # used for group by
            sortOrder=sortOrder,
            statListDict=statListDict,
            interfaceDefaults=interfaceDefaults,
            masterDf=dfMaster,
            # limitToCol=limitToCol,
            # interfaceDefaults=interfaceDefaults,
        )
    mainWidget2.show()
    
    sys.exit(app.exec_())

