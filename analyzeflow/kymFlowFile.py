import os
import sys
import tifffile
import numpy as np
import pandas as pd
import scipy.signal

import analyzeflow.kymFlowUtil
import analyzeflow.kymFlowRadon

from analyzeflow import get_logger
logger = get_logger(__name__)

class kymFlowFile():
    """Class to hold a kym for flow analysis.
        - tif data
        - tif header
        - analysis results (from radon)
    """
    def __init__(self, tifPath : str, loadTif=True):
        # load tif data
        self._tifPath = tifPath
        self._tifData = None
        if loadTif:
            self._tifData = tifffile.imread(tifPath)

        # don't rotate, only for plot, see getTifCopy()
        #self._tifData = np.rot90(self._tifData)  # for plot

        # load header from txt file
        self._header = analyzeflow.kymFlowUtil._readOlympusHeader(tifPath)

        # load analysis if it exists
        self._df = None
        self.loadAnalysis()

        self._dfMatlab = None
        self.loadMatlabAnalysis()

    def getTifCopy(self, doRotate=False):
        if self._tifData is None:
            logger.warning(f'no tif data {self._tifPath}')
            return
        tifCopy = self._tifData.copy()
        if doRotate:
            tifCopy = np.rot90(tifCopy)
        return tifCopy

    def getFileName(self):
        return os.path.split(self._tifPath)[1]
    
    def numLines(self):
        #return self._tifData.shape[0]
        return self._header['numLines']

    def pntsPerLine(self):
        #return self._tifData.shape[1]
        return self._header['pixelsPerLine']

    def delx(self):
        return self._header['umPerPixel']

    def delt(self):
        return self._header['secondsPerLine']

    def analyzeFlowWithRadon(self, windowSize : int = 16,
                    startPixel : int = None,
                    stopPixel : int = None,
                    ):
        """Analyze flow using Radon transform.
        
        Args:
            windowSize: must be multiple of 4
        
        Note:
            the speed scales with window size, larger window size is faster
        """

        delx = self.delx()
        delt = self.delt()
        tifData = self._tifData

        thetas,the_t,spread_matrix = analyzeflow.kymFlowRadon.mpAnalyzeFlow(tifData,
                                    windowSize,
                                    startPixel=startPixel,
                                    stopPixel=stopPixel)
        
        # convert to physical units
        drewTime = the_t * delt
        
        _rad = np.deg2rad(thetas)
        drewVelocity = (delx/delt) * np.tan(_rad)
        drewVelocity = drewVelocity / 1000  # mm/s

        # np.tan(90 deg) is returning 1e16 rather than inf
        tan90 = drewVelocity > 1e6
        drewVelocity[tan90] = float('nan')

        # create a df
        df = pd.DataFrame()
        df['time'] = drewTime
        df['velocity'] = drewVelocity
        df['parentFolder'] = analyzeflow.kymFlowUtil._getFolderName(self._tifPath)
        df['file'] = self.getFileName()
        df['algorithm'] = 'mpRadon'
        df['delx'] = delx
        df['delt'] = delt
        df['numLines'] = self.numLines()
        df['pntsPerLine'] = self.pntsPerLine()

        self._df = df

    def getVelocity(self, removeOutliers=False, medianFilter : int = 0):
        """Get velocity from analysis.
        """
        velocityDrew = self._df[ self._df['algorithm']=='mpRadon' ]['velocity'].to_numpy()
        
        velocityDrew = np.abs(velocityDrew)
        
        if removeOutliers:
            #print('removeOutliers', np.nanmean(velocityDrew))
            velocityDrew = analyzeflow.kymFlowUtil._removeOutliers(velocityDrew)
            #print('  after', np.nanmean(velocityDrew))
        if medianFilter>0:
            velocityDrew = scipy.signal.medfilt(velocityDrew, medianFilter)
        return velocityDrew

    def getTime(self):
        """Get time from analysis.
        
        Different than time of line scan.
        """
        timeDrew = self._df[ self._df['algorithm']=='mpRadon' ]['time'].to_numpy()
        return timeDrew

    def getReport(self, removeOutliers=True, medianFilter=0) -> dict:

        # load tif and get intensity stats
        tifData = self._tifData
        meanInt = np.mean(tifData)
        minInt = np.min(tifData)
        maxInt = np.max(tifData)

        # refine analysis per file
        # if timeLimitDict is not None and file in timeLimitDict.keys():
        #     # time-limit the df
        #     print(' . time limiting', file, timeLimitDict[file])
        #     minTime = timeLimitDict[file]['minTime']
        #     maxTime = timeLimitDict[file]['maxTime']
        #     oneDf = oneDf[ (oneDf['time'] >= minTime) & (oneDf['time'] <= maxTime)]  # seconds


        vel = self.getVelocity(removeOutliers=removeOutliers,medianFilter=medianFilter)
        minVel = np.nanmin(vel)
        maxVel = np.nanmax(vel)
        rangeVel = maxVel - minVel
        meanVel = np.nanmean(vel)
        stdVel = np.nanstd(vel)
        nTotal = len(vel)
        nNonNan = np.count_nonzero(~np.isnan(vel))
        nNan = np.count_nonzero(np.isnan(vel))

        # make a column with parentFolder+'/'+file
        parentFolder = analyzeflow.kymFlowUtil._getFolderName(self._tifPath)
        oneDict = {
            'parentFolder': parentFolder,
            'file': self.getFileName(),
            'uniqueFile': parentFolder + '/' + self.getFileName(),

            'pntsPerLine': self.pntsPerLine(),
            'numLines': self.numLines(),
            'delx': self.delx(),
            'delt': self.delt(),

            'Total Dur (s)': self.numLines() * self.delt(),
            'Line Length (um)': self.pntsPerLine() * self.delx(),

            'meanInt': meanInt,
            'minInt': minInt,
            'maxInt': maxInt,
            
            'minVel': minVel,
            'maxVel': maxVel,
            'rangeVel': rangeVel,
            'meanVel': meanVel,
            'stdVel': stdVel,
            'nTotal': nTotal,
            'nNonNan': nNonNan,
            'nNan': nNan,
        }
        return oneDict

    def saveAnalysis(self):
        if self._df is None:
            logger.info('no analysis to save')
            return
        savePath = analyzeflow.kymFlowUtil._getAnalysisPath_v2(self._tifPath)
        if not os.path.isdir(savePath):
            os.mkdir(savePath)
        csvFileName = self.getFileName()
        csvFileName = os.path.splitext(csvFileName)[0] + '.csv'
        saveFilePath = os.path.join(savePath, csvFileName)
        logger.info(f'saving: {saveFilePath}')
        self._df.to_csv(saveFilePath)

    def loadAnalysis(self):
        # load corresponding csv from python radon analysis
        tifPath = self._tifPath
        loadPath = analyzeflow.kymFlowUtil._getAnalysisPath_v2(tifPath)
        csvFileName = self.getFileName()
        csvFileName = os.path.splitext(csvFileName)[0] + '.csv'
        loadFilePath = os.path.join(loadPath, csvFileName)
        if os.path.isfile(loadFilePath):
            self._df = pd.read_csv(loadFilePath)
        else:
            logger.info(f'no analysis to load: {loadFilePath}')

    def loadMatlabAnalysis(self):
        csvFile = analyzeflow.kymFlowUtil._getCsvFile(self._tifPath)
        if os.path.isfile(csvFile):
            self._dfMatlab = pd.read_csv(csvFile)
        else:
            #logger.info(f'no matlab analysis to load: {csvFile}')
            pass

if __name__ == '__main__':
    tifPath = '/Users/cudmore/Dropbox/data/declan/Bloodflow TIFs nov 23/20221102/Capillary1_0001.tif'
    tifPath = '/Users/cudmore/Dropbox/data/declan//20221102/Capillary5_0001.tif'
    kff = kymFlowFile(tifPath)

    kff.analyzeFlowWithRadon()  # do actual kym radon analysis
    kff.saveAnalysis()  # save result to csv
    sys.exit(1)

    from pprint import pprint
    #pprint(kff._header)

    df = kff.getReport()
    pprint(df)