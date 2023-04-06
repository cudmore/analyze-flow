import os
import sys
import numpy as np
import pandas as pd
import tifffile

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

#from analyzeflow import kymFlowFile
import analyzeflow

#from analyzeflow import mpAnalyzeFlow
from analyzeflow import get_logger
logger = get_logger(__name__)

def _removeOutliers(y : np.ndarray) -> np.ndarray:
    """Nan out values +/- 2*std.
    """
    
    # trying to fix plotly refresh bug
    #_y = y.copy()
    _y = y

    _mean = np.nanmean(_y)
    _std = np.nanstd(_y)
    
    _greater = _y > (_mean + 2*_std)
    _y[_greater] = np.nan #float('nan')
    
    _less = _y < (_mean - 2*_std)
    _y[_less] = np.nan #float('nan')

    # _greaterLess = (_y > (_mean + 2*_std)) | (_y < (_mean - 2*_std))
    # _y[_greaterLess] = np.nan #float('nan')

    return _y

def old_makeSummaryTable(folderPath : str,
                    timeLimitDict = None,
                    removeOutliers = True) -> pd.DataFrame:
    """Given a folder path, load each flow analysis (csv)
        and make a summary table.
    """
    parentFolder = os.path.split(folderPath)[1]
    
    files = os.listdir(folderPath)
    files = sorted(files)

    dictList = []

    for file in files:
        if not file.endswith('.tif'):
            continue
        oneTifPath = os.path.join(folderPath, file)
        oneCsvPath =  _getCsvFile(oneTifPath)
        oneDf = pd.read_csv(oneCsvPath)

        if timeLimitDict is not None and file in timeLimitDict.keys():
            # time-limit the df
            print(' . time limiting', file, timeLimitDict[file])
            minTime = timeLimitDict[file]['minTime']
            maxTime = timeLimitDict[file]['maxTime']
            oneDf = oneDf[ (oneDf['time'] >= minTime) & (oneDf['time'] <= maxTime)]  # seconds

        # get pntPerLine, numLines from first row
        # assuming is the same for entire file (which is true)
        pntsPerLine = oneDf.loc[0, 'pntsPerLine']
        numLines = oneDf.loc[0, 'numLines']
        delx = oneDf.loc[0, 'delx']
        delt = oneDf.loc[0, 'delt']

        velDrew = oneDf[ oneDf['algorithm']=='drew' ]['velocity']
        velDrew = np.abs(velDrew)
        if removeOutliers:
            velDrew = _removeOutliers(velDrew)
        meanVelDrew = np.nanmean(velDrew)
        stdVelDrew = np.nanstd(velDrew)
        nDrew = np.count_nonzero(~np.isnan(velDrew))
        nDrewNan = np.count_nonzero(np.isnan(velDrew))

        velChhatbar = oneDf[ oneDf['algorithm']=='chhatbar' ]['velocity']
        velChhatbar = np.abs(velChhatbar)
        if removeOutliers:
            velChhatbar = _removeOutliers(velChhatbar)
        meanVelChhatbar = np.nanmean(velChhatbar)
        stdVelChhatbar = np.nanstd(velChhatbar)
        nChhatbar = np.count_nonzero(~np.isnan(velChhatbar))
        nChhatbarNan = np.count_nonzero(np.isnan(velChhatbar))
        
        oneDict = {
            'parentFolder': parentFolder,
            'file': file,

            'pntsPerLine': pntsPerLine,
            'numLines': numLines,
            'delx': delx,
            'delt': delt,

            'Total Dur (s)': numLines * delt,
            'Line Length (um)': pntsPerLine * delx,

            'meanVelDrew': meanVelDrew,
            'stdVelDrew': stdVelDrew,
            'nDrew': nDrew,
            'nDrewNan': nDrewNan,
            'meanVelChhatbar': meanVelChhatbar,
            'stdVelChhatbar': stdVelChhatbar,
            'nChhatbar': nChhatbar,
            'nChhatbarNan': nChhatbarNan,
        }
        dictList.append(oneDict)
        
    dfSummary = pd.DataFrame(dictList)
    #display(dfSummary)
    return dfSummary

def makeSummaryTable_v3(folderPath : str,
                    timeLimitDict = None,
                    removeOutliers = True,
                    medianFilter = 0,
                    master_db_file = None) -> pd.DataFrame:
    """Given a folder, make a summary of all flow analysis.

    One row per file
    
    First column is the unique index (dateIndex) for this folder.
    
    Args:
        master_db_file: full path to master db file. We will pull some columns from here (age, sex, genotype, reject)
    """    
    
    # copy these columns from master_db_file (one row, e.g. file,  at a time)
    masterCols = ['Surgery Type', 'Genotype', 'Sex', 'Age',
                    'Order', 'Direction', 'Depth',
                    'Quality', 'declanFile',
                    'startSec', 'stopSec',
                    'cudmore_notes',
                    'reject']
    if master_db_file is not None:
        dfMaster = pd.read_excel(master_db_file)
    else:
        dfMaster = None

    files = os.listdir(folderPath)
    files = sorted(files)
    dictList = []
    for file in files:
        if not file.endswith('.tif'):
            continue
        
        # load the file and analysis
        oneTifPath = os.path.join(folderPath, file)
        kff = analyzeflow.kymFlowFile(oneTifPath)
        
        # feb 2023, THIS IS NOT WORKING !!!!!!!!!!!!!!!!!!!!!!!!!!
        # for the report, we need to use startSec/stopSec columns in dfMaster
        _startSec = None
        _stopSec = None
        if dfMaster is not None:
            _fileName = file
            _folder = os.path.split(folderPath)[1]
            _uniqueFile = _folder + '/' + _fileName
            _oneFileRow = dfMaster.loc[dfMaster['uniqueFile'] == _uniqueFile]
            _oneFileRow = _oneFileRow.reset_index()
            _startSec = _oneFileRow.at[0, 'startSec']  # either np.float64 or np.nan
            _stopSec = _oneFileRow.at[0, 'stopSec']
            if np.isnan(_startSec):
                _startSec = None
            if np.isnan(_stopSec):
                _stopSec = None
            #print(_fileName, '  _startSec:', _startSec, type(_startSec), '_stopSec:', _stopSec, type(_stopSec))

        # generate report
        oneDict = kff.getReport(removeOutliers=removeOutliers,
                        medianFilter=medianFilter,
                        startSec=_startSec,
                        stopSec=_stopSec)
        
        # new feb 2023
        # look into our master db for additional columns
        if dfMaster is not None:
            uniqueFile = oneDict['uniqueFile']
            oneFileRow = dfMaster.loc[dfMaster['uniqueFile'] == uniqueFile]
            oneFileRow = oneFileRow.reset_index()
            #print('oneFileRow:', oneFileRow)
            for _col in masterCols:
                # print(_col, oneFileRow.at[0, _col])
                try:
                    _currVal = oneFileRow.at[0, _col]
                    if _col == 'reject':
                        if str(_currVal) == 'nan':
                            _currVal = 'No'
                        _currVal = str(_currVal)
                        #print(f'"{_currVal}" {type(_currVal)}')

                    oneDict[_col] = _currVal  # 0 is row label (NOT ROW NUMBER/INDEX)
                except (KeyError) as e:
                    #logger.error(oneTifPath)
                    logger.error(f'uniqueFile:{uniqueFile}')
                    logger.error(f'  did not find key "{_col}" column')

        dictList.append(oneDict)
    
    dfSummary = pd.DataFrame(dictList)
    
    # insert a column counting files within  this folder
    dfSummary.insert(loc=0, column='dateIndex', value=range(len(dictList)))

    return dfSummary


def old_makeSummaryTable_v2(folderPath : str,
                    timeLimitDict = None,
                    removeOutliers = True) -> pd.DataFrame:
    """Given a folder path, load each flow analysis (csv)
        and make a summary table.
    
        Returns:
            pd.DataFrame with the summary
    """
    parentFolder = os.path.split(folderPath)[1]
    
    files = os.listdir(folderPath)
    files = sorted(files)

    dictList = []

    for file in files:
        if not file.endswith('.tif'):
            continue
        oneTifPath = os.path.join(folderPath, file)
        
        oneCsvPath =  _getCsvFile_v2(oneTifPath)
        oneDf = pd.read_csv(oneCsvPath)

        # load tif and get intensity stats
        tifData = tifffile.imread(oneTifPath)
        meanInt = np.mean(tifData)
        minInt = np.min(tifData)
        maxInt = np.max(tifData)

        # refine analysis per file
        if timeLimitDict is not None and file in timeLimitDict.keys():
            # time-limit the df
            print(' . time limiting', file, timeLimitDict[file])
            minTime = timeLimitDict[file]['minTime']
            maxTime = timeLimitDict[file]['maxTime']
            oneDf = oneDf[ (oneDf['time'] >= minTime) & (oneDf['time'] <= maxTime)]  # seconds

        # get pntPerLine, numLines from first row
        # assuming is the same for entire file (which is true)
        pntsPerLine = oneDf.loc[0, 'pntsPerLine']
        numLines = oneDf.loc[0, 'numLines']
        delx = oneDf.loc[0, 'delx']
        delt = oneDf.loc[0, 'delt']

        vel = oneDf['velocity']
        vel = np.abs(vel)
        if removeOutliers:
            vel = _removeOutliers(vel)
        minVel = np.nanmin(vel)
        maxVel = np.nanmax(vel)
        meanVel = np.nanmean(vel)
        stdVel = np.nanstd(vel)
        nTotal = len(vel)
        nNonNan = np.count_nonzero(~np.isnan(vel))
        nNan = np.count_nonzero(np.isnan(vel))

        # make a column with parentFolder+'/'+file
        oneDict = {
            'parentFolder': parentFolder,
            'file': file,
            'uniqueFile': parentFolder + '/' + file,

            'pntsPerLine': pntsPerLine,
            'numLines': numLines,
            'delx': delx,
            'delt': delt,

            'Total Dur (s)': numLines * delt,
            'Line Length (um)': pntsPerLine * delx,

            'meanInt': meanInt,
            'minInt': minInt,
            'maxInt': maxInt,
            
            'minVel': minVel,
            'maxVel': maxVel,
            'meanVel': meanVel,
            'stdVel': stdVel,
            'nTotal': nTotal,
            'nNonNan': nNonNan,
            'nNan': nNan,
        }
        dictList.append(oneDict)
        
    dfSummary = pd.DataFrame(dictList)
    #display(dfSummary)
    return dfSummary

def _readOlympusHeader(tifPath):
    """Read the Olympus header from exported txt file.

        Return:
            dx:
            dt:

        The important Olympus txt header lines are:
            "Date"	"11/02/2022 12:54:17.359 PM"
            "File Version"	"2.1.2.3"
            "System Version"	"2.3.2.169"

            "X Dimension"	"38, 0.0 - 10.796 [um], 0.284 [um/pixel]"
            "T Dimension"	"1, 0.000 - 35.099 [s], Interval FreeRun"
            "Image Size"	"38 * 30000 [pixel]"

            "Bits/Pixel"	"12 [bits]"
    """

    txtPath = os.path.splitext(tifPath)[0] + '.txt'
    if not os.path.isfile(txtPath):
        logger.error(f'error: did not find Olympus header: {txtPath}')
        return
    
    retDict = {
        'dateStr': None,
        'timeStr': None,
        'umPerPixel': None,
        'secondsPerLine': None,
        'durImage_sec': None,
        'pixelsPerLine': None,
        'numLines': None,
        'bitsPerPixel': None,
        }
    
    pixelsPerLine = None
    
    with open(txtPath) as f:
        for line in f:
            line = line.strip()
            
            # "X Dimension"	"38, 0.0 - 10.796 [um], 0.284 [um/pixel]"
            if line.startswith('"X Dimension"'):
                oneLine = line.split()
                umPerPixel = oneLine[7]  # um/pixel
                # print('umPerPixel:', umPerPixel)
                retDict['umPerPixel'] = float(umPerPixel)

            # "T Dimension"	"1, 0.000 - 35.099 [s], Interval FreeRun"
            if line.startswith('"T Dimension"'):
                oneLine = line.split()
                durImage_sec = oneLine[5]  # imaging duration
                # print('durImage_sec:', durImage_sec)
                retDict['durImage_sec'] = float(durImage_sec)

            # "Image Size"	"38 * 30000 [pixel]"
            if line.startswith('"Image Size"'):
                if pixelsPerLine is None:
                    oneLine = line.split()
                    pixelsPerLine = oneLine[2].replace('"', '')
                    numLines = oneLine[4].replace('"', '')
                    # print('pixelsPerLine:', pixelsPerLine)
                    # print('numLines:', numLines)
                    retDict['pixelsPerLine'] = int(pixelsPerLine)
                    retDict['numLines'] = int(numLines)

            # "Date"	"11/02/2022 12:54:17.359 PM"
            if line.startswith('"Date"'):
                oneLine = line.split()
                dateStr = oneLine[1].replace('"', '')
                timeStr = oneLine[2]
                dotIndex = timeStr.find('.')
                if dotIndex != -1:
                    timeStr = timeStr[0:dotIndex]
                # print('dateStr:', dateStr)
                # print('timeStr:', timeStr)
                retDict['dateStr'] = dateStr
                retDict['timeStr'] = timeStr

            # "Bits/Pixel"	"12 [bits]"
            if line.startswith('"Bits/Pixel"'):
                oneLine = line.split()
                bitsPerPixel = oneLine[1].replace('"', '')
                # print('bitsPerPixel:', bitsPerPixel)
                retDict['bitsPerPixel'] = int(bitsPerPixel)

    retDict['secondsPerLine'] = retDict['durImage_sec'] / retDict['numLines']

    return retDict

def _getFolderName(filePath : str) -> str:
    """Given a file path, get the folder name.
    """
    folder = os.path.split(filePath)[0]
    folderName = os.path.split(folder)[1]
    return folderName

def _getAnalysisPath(tifPath):
    """Get folder path for matlab analysis.
    """
    folder, tifFile = os.path.split(tifPath)
    folderName = os.path.split(folder)[1]
    analysisFolderName = folderName + '-matlab-analysis'
    analysisPath = os.path.join(folder, analysisFolderName)
    #print('analysisPath:', analysisPath)
    return analysisPath

def _getAnalysisPath_v2(tifPath):
    """Get folder path for python analysis.
    """
    folder, tifFile = os.path.split(tifPath)
    folderName = os.path.split(folder)[1]
    analysisFolderName = folderName + '-analysis'
    analysisPath = os.path.join(folder, analysisFolderName)
    #print('analysisPath:', analysisPath)
    return analysisPath

def _getCsvFile(tifPath) -> str:
    # load corresponding csv from matlab analysis
    analysisFolderPath = _getAnalysisPath(tifPath)
    baseFile = os.path.split(tifPath)[1]
    baseFile, _ext = os.path.splitext(baseFile)
    csvFileName = baseFile + '_combined.csv'
    csvPath = os.path.join(analysisFolderPath, csvFileName)
    return csvPath

def _getCsvFile_v2(tifPath) -> str:
    # load corresponding csv from python analysis
    analysisFolderPath = _getAnalysisPath_v2(tifPath)
    baseFile = os.path.split(tifPath)[1]
    baseFile, _ext = os.path.splitext(baseFile)
    csvFileName = baseFile + '.csv'
    csvPath = os.path.join(analysisFolderPath, csvFileName)
    return csvPath

def old_plotFlowAnalysis(tifPath):
    """
    Load tif
    Load csv
    
    Plot kym, vel drew, vel chhatbar
    """
        
    # load tif data
    tifData = tifffile.imread(tifPath)
    tifData = np.rot90(tifData)
    #print('tifData:', tifData.shape)  # (38, 30000)
    
    # load corresponding csv
    # analysisFolderPath = _getAnalysisPath(tifPath)
    # baseFile = os.path.split(tifPath)[1]
    # baseFile, _ext = os.path.splitext(baseFile)
    # csvFileName = baseFile + '_combined.csv'
    # csvPath = os.path.join(analysisFolderPath, csvFileName)
    csvPath = _getCsvFile(tifPath)
    df = pd.read_csv(csvPath)
        
    filename = os.path.split(tifPath)[1]
    fig = make_subplots(rows=4, cols=1,
                    subplot_titles=(filename,  'Drew', 'Chhatbar', ''),
                    shared_xaxes=True,
                    shared_yaxes=False,
                    vertical_spacing=0.05,
                    specs=[[{"type": "heatmap"}],
                        [{"type": "scatter"}],
                        [{"type": "scatter"}],
                        [{"type": "table"}],
                        ]
                    )
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(showlegend=False)
    fig['layout'].update(height=1000, width=800)

    delt = df.loc[0, 'delt']
    #print('delt:', delt)
    _numLines = tifData.shape[1]
    _numPnts = tifData.shape[0]
    figm = px.imshow(tifData,
                x=np.arange(_numLines)*delt,
                y=np.arange(_numPnts))
    fig.add_trace(figm.data[0], row=1, col=1)

    fig['layout']['yaxis']['title']='Distance (um)'

    #
    # Drew
    timeDrew = df[ df['algorithm']=='drew' ]['time'].to_numpy()
    velocityDrew = df[ df['algorithm']=='drew' ]['velocity'].to_numpy()
    # remove outliers
    velocityDrew = _removeOutliers(velocityDrew)
    fig.add_trace(
        go.Scatter(x=timeDrew, y=velocityDrew,
                    marker_color='rgba(0, 0, 0, 1.0)',
                    ),
        row=2, col=1
    )
    # super bad how plotly gives axes to subplot labels as 'xxx'
    fig['layout']['yaxis2']['title']='Velocity (mm/s)'

    # plot mean +/- std
    velDrewMean = np.nanmean(velocityDrew)
    velDrewStd = np.nanstd(velocityDrew)
    nDrew = np.count_nonzero(~np.isnan(velocityDrew))
    fig.add_trace(
        go.Scatter(x=[timeDrew[0],timeDrew[-1]],
                        y=[velDrewMean,velDrewMean],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=[timeDrew[0],timeDrew[-1]],
                        y=[velDrewMean+2*velDrewStd,velDrewMean+2*velDrewStd],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=[timeDrew[0],timeDrew[-1]],
                        y=[velDrewMean-2*velDrewStd,velDrewMean-2*velDrewStd],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=2, col=1
    )

    #
    # Chhatbar
    timeChhatbar = df[ df['algorithm']=='chhatbar' ]['time'].to_numpy()
    velocityChhatbar = df[ df['algorithm']=='chhatbar' ]['velocity'].to_numpy()
    # remove outliers
    velocityChhatbar = _removeOutliers(velocityChhatbar)
    fig.add_trace(
        go.Scatter(x=timeChhatbar, y=velocityChhatbar,
                            marker_color='rgba(0, 0, 0, 1.0)',
                            ),
        row=3, col=1
    )
    fig['layout']['yaxis3']['title']='Velocity (mm/s)'
    fig['layout']['xaxis3']['title']='Time (s)'

    # plot mean +/- std
    velChhatbarMean = np.nanmean(velocityChhatbar)
    velChhatbarStd = np.nanstd(velocityChhatbar)
    nChhatbar = np.count_nonzero(~np.isnan(velocityChhatbar))
    fig.add_trace(
        go.Scatter(x=[timeChhatbar[0],timeChhatbar[-1]],
                        y=[velChhatbarMean,velChhatbarMean],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=[timeChhatbar[0],timeChhatbar[-1]],
                        y=[velChhatbarMean+2*velChhatbarStd,velChhatbarMean+2*velChhatbarStd],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=[timeChhatbar[0],timeChhatbar[-1]],
                        y=[velChhatbarMean-2*velChhatbarStd,velChhatbarMean-2*velChhatbarStd],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=3, col=1
    )

    # Add dropdown
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=["type", "surface", [0]],  # [0] refers to the first subplot
                        label="3D Surface",
                        method="restyle"
                    ),
                    dict(
                        args=["type", "heatmap", [0]],
                        label="Heatmap",
                        method="restyle"
                    )
                ]),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )

    velDrewMean = np.nanmean(velocityDrew)
    velDrewStd = np.nanstd(velocityDrew)
    nDrew = np.count_nonzero(~np.isnan(velocityDrew))

    _velDrewMean = round(velDrewMean,2)
    _velDrewStd = round(velDrewStd,2)
    _velChhatbarMean = round(velChhatbarMean,2)
    _velChhatbarStd = round(velChhatbarStd,2)

    # add summary table
    #dfTmp = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/Mining-BTC-180.csv")
    fig.add_trace(
        go.Table(
            header=dict(
                values=['Algorithm', 'Mean Velocity<br>(mm/s)', 'Std', 'n'],
                font=dict(size=10),
                align="left"
            ),
            cells=dict(
                #values=[dfTmp[k].tolist() for k in dfTmp.columns[1:]],
                values = [
                    ['Drew', 'Chhatbar'],
                    [_velDrewMean, _velChhatbarMean], # mean
                    [_velDrewStd, _velChhatbarStd], # std
                    [nDrew, nChhatbar], # n
                ],
                align = "left")
        ),
        row=4, col=1
    )

    #
    return fig

def old_plotFlowAnalysis_v2(tifPath, removeOutliers=True, medianFilter=0):
    """
    Load tif
    Load csv
    
    Plot kym, vel drew, vel chhatbar

    Args:
        medianFiler: if 0 then none, otherwise must be odd
    """
        
    # load tif data
    # tifData = tifffile.imread(tifPath)
    # tifData = np.rot90(tifData)
    # #print('tifData:', tifData.shape)  # (38, 30000)
    
    # # load corresponding csv

    # csvPath = _getCsvFile_v2(tifPath)
    # df = pd.read_csv(csvPath)
        
    # filename = os.path.split(tifPath)[1]

    # construct a kymFlow from file and grab params for plot
    _kymFlow = analyzeflow.kymFlowFile(tifPath)
    tifData = _kymFlow.getTifCopy(doRotate=True)
    filename = _kymFlow.getFileName()
    _numLines = _kymFlow.numLines()
    _numPnts = _kymFlow.pntsPerLine()
    delt = _kymFlow.delt()
    #df = _kymFlow._df
    timeDrew = _kymFlow.getTime()
    velocityDrew = _kymFlow.getVelocity(removeOutliers=removeOutliers, medianFilter=medianFilter)
    
    fig = make_subplots(rows=3, cols=1,
                    subplot_titles=(filename,  'Drew Python', ''),
                    shared_xaxes=True,
                    shared_yaxes=False,
                    vertical_spacing=0.05,
                    specs=[[{"type": "heatmap"}],
                        [{"type": "scatter"}],
                        [{"type": "table"}],
                        ]
                    )
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(showlegend=False)
    fig['layout'].update(height=1000, width=800)

    #delt = df.loc[0, 'delt']
    #print('delt:', delt)
    #_numLines = tifData.shape[1]
    #_numPnts = tifData.shape[0]
    figm = px.imshow(tifData,
                x=np.arange(_numLines)*delt,
                y=np.arange(_numPnts))
    fig.add_trace(figm.data[0], row=1, col=1)

    fig['layout']['yaxis']['title']='Distance (um)'

    #
    # Drew
    # timeDrew = df[ df['algorithm']=='mpRadon' ]['time'].to_numpy()
    # velocityDrew = df[ df['algorithm']=='mpRadon' ]['velocity'].to_numpy()
    # # remove outliers
    # if removeOutliers:
    #     velocityDrew = _removeOutliers(velocityDrew)
    # if medianFilter>0:
    #     velocityDrew = scipy.signal.medfilt(velocityDrew, medianFilter)
    fig.add_trace(
        go.Scatter(x=timeDrew, y=velocityDrew,
                    marker_color='rgba(0, 0, 0, 1.0)',
                    ),
        row=2, col=1
    )
    # super bad how plotly gives axes to subplot labels as 'xxx'
    fig['layout']['yaxis2']['title']='Velocity (mm/s)'

    # plot mean +/- std
    velDrewMean = np.nanmean(velocityDrew)
    velDrewStd = np.nanstd(velocityDrew)
    nDrew = np.count_nonzero(~np.isnan(velocityDrew))
    fig.add_trace(
        go.Scatter(x=[timeDrew[0],timeDrew[-1]],
                        y=[velDrewMean,velDrewMean],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=[timeDrew[0],timeDrew[-1]],
                        y=[velDrewMean+2*velDrewStd,velDrewMean+2*velDrewStd],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=[timeDrew[0],timeDrew[-1]],
                        y=[velDrewMean-2*velDrewStd,velDrewMean-2*velDrewStd],
                        marker_color='rgba(255, 0, 0, 1.0)',
                        mode='lines'),
        row=2, col=1
    )

    fig['layout']['yaxis2']['title']='Velocity (mm/s)'
    fig['layout']['xaxis2']['title']='Time (s)'

    # #
    # # Chhatbar
    # timeChhatbar = df[ df['algorithm']=='chhatbar' ]['time'].to_numpy()
    # velocityChhatbar = df[ df['algorithm']=='chhatbar' ]['velocity'].to_numpy()
    # # remove outliers
    # velocityChhatbar = _removeOutliers(velocityChhatbar)
    # fig.add_trace(
    #     go.Scatter(x=timeChhatbar, y=velocityChhatbar,
    #                         marker_color='rgba(0, 0, 0, 1.0)',
    #                         ),
    #     row=3, col=1
    # )
    # fig['layout']['yaxis3']['title']='Velocity (mm/s)'
    # fig['layout']['xaxis3']['title']='Time (s)'

    # # plot mean +/- std
    # velChhatbarMean = np.nanmean(velocityChhatbar)
    # velChhatbarStd = np.nanstd(velocityChhatbar)
    # nChhatbar = np.count_nonzero(~np.isnan(velocityChhatbar))
    # fig.add_trace(
    #     go.Scatter(x=[timeChhatbar[0],timeChhatbar[-1]],
    #                     y=[velChhatbarMean,velChhatbarMean],
    #                     marker_color='rgba(255, 0, 0, 1.0)',
    #                     mode='lines'),
    #     row=3, col=1
    # )
    # fig.add_trace(
    #     go.Scatter(x=[timeChhatbar[0],timeChhatbar[-1]],
    #                     y=[velChhatbarMean+2*velChhatbarStd,velChhatbarMean+2*velChhatbarStd],
    #                     marker_color='rgba(255, 0, 0, 1.0)',
    #                     mode='lines'),
    #     row=3, col=1
    # )
    # fig.add_trace(
    #     go.Scatter(x=[timeChhatbar[0],timeChhatbar[-1]],
    #                     y=[velChhatbarMean-2*velChhatbarStd,velChhatbarMean-2*velChhatbarStd],
    #                     marker_color='rgba(255, 0, 0, 1.0)',
    #                     mode='lines'),
    #     row=3, col=1
    # )

    # Add dropdown
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=["type", "surface", [0]],  # [0] refers to the first subplot
                        label="3D Surface",
                        method="restyle"
                    ),
                    dict(
                        args=["type", "heatmap", [0]],
                        label="Heatmap",
                        method="restyle"
                    )
                ]),
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.1,
                yanchor="top"
            ),
        ]
    )

    velDrewMean = np.nanmean(velocityDrew)
    velDrewStd = np.nanstd(velocityDrew)
    nDrew = np.count_nonzero(~np.isnan(velocityDrew))

    _velDrewMean = round(velDrewMean,2)
    _velDrewStd = round(velDrewStd,2)
    # _velChhatbarMean = round(velChhatbarMean,2)
    # _velChhatbarStd = round(velChhatbarStd,2)

    # add summary table
    #dfTmp = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/Mining-BTC-180.csv")
    fig.add_trace(
        go.Table(
            header=dict(
                values=['Algorithm', 'Mean Velocity<br>(mm/s)', 'Std', 'n'],
                font=dict(size=10),
                align="left"
            ),
            cells=dict(
                #values=[dfTmp[k].tolist() for k in dfTmp.columns[1:]],
                values = [
                    ['Drew'],
                    [_velDrewMean], # mean
                    [_velDrewStd], # std
                    [nDrew], # n
                ],
                align = "left")
        ),
        row=3, col=1
    )

    #
    return fig

def runPoolTest():

    dm_master_db_file = '../declan-flow-analysis-shared/flowSummary-20230206_v2 (1).xlsx'
    if not os.path.isfile(dm_master_db_file):
        print('ERROR: did not find master db file', dm_master_db_file)
        sys.exit(1)
        
    folderPath = '../declan-flow-analysis-shared/data/20230117'

    removeOutliers = True
    medianFilter = 5
    oneDf = analyzeflow.kymFlowUtil.makeSummaryTable_v3(folderPath,
                                removeOutliers=removeOutliers,
                                medianFilter=medianFilter,
                                master_db_file=dm_master_db_file)

if __name__ == '__main__':
    df = runPoolTest()
    sys.exit(1)
    
    folderPath = '/Users/cudmore/Dropbox/data/declan/20221102'
    dfFolder = makeSummaryTable_v3(folderPath)
    print(dfFolder)

    sys.exit()

    # folderPath = '/Users/cudmore/Dropbox/data/declan/20221102'
    # saveAnalysisImages(folderPath)

    # sys.exit(1)

    tifPath = '/Users/cudmore/Dropbox/data/declan/Bloodflow TIFs nov 23/20221102/Capillary1_0001.tif'
    tifPath = '/Users/cudmore/Dropbox/data/declan//20221102/Capillary5_0001.tif'
    
    headerDict = _readOlympusHeader(tifPath)
    print('headerDict:', headerDict)

    #sys.exit()

    oneFlowFig = plotFlowAnalysis(tifPath)
    
    oneFlowFig.show()