import os
import sys
from datetime import datetime
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

        # self._dateAnalyzed = None
        # self._timeAnalyzed = None

        # load tif data
        self._tifPath = tifPath
        self._tifData = None
        if loadTif:
            self._tifData = tifffile.imread(tifPath)

        # don't rotate, only for plot, see getTifCopy()
        #self._tifData = np.rot90(self._tifData)  # for plot

        # load header from txt file
        self._header = analyzeflow.kymFlowUtil._readOlympusHeader(tifPath)

        # load analysis if it exists (this is a csv with one line per line scan)
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
        
        This generates a pd.DataFrame, one row per line scan.
        This is what we save.

        Args:
            windowSize: must be multiple of 4
        
        Note:
            the speed scales with window size, larger window size is faster
        """

        _analysisVerion = 0.2
        
        # TODO:
        # self._dateAnalyzed = datetime.today().strftime('%Y%m%d')
        # self._timeAnalyzed = datetime.today().strftime('%H:%M:%S')

        delx = self.delx()
        delt = self.delt()
        tifData = self._tifData

        logger.info(f'calling mpAnalyzeFlow() for {self.getFileName()}')
        thetas,the_t,spread_matrix = analyzeflow.kymFlowRadon.mpAnalyzeFlow(tifData,
                                    windowSize,
                                    startPixel=startPixel,
                                    stopPixel=stopPixel)
        
        doDebugVar = False
        # need to figure out how to use variance to reject individual velocity measurements
        if doDebugVar:
            logger.info('=== DEBUG spread_matrix:')
            print('  shape:', spread_matrix.shape, 'dtype:', spread_matrix.dtype)
            
            # normalize spread matrix?
            spread_matrix_mean = np.mean(spread_matrix, axis=1)
            spread_matrix = spread_matrix / spread_matrix_mean[:,None]

            minSpread = np.min(spread_matrix, axis=1)
            maxSpread = np.max(spread_matrix, axis=1)
            print('  minSpread.shape:', minSpread.shape)
            print('  maxSpread.shape:', maxSpread.shape)
            print('    min of minSpread:', np.min(minSpread))
            print('    min of maxSpread:', np.min(maxSpread))

            import matplotlib.pyplot as plt
            fig, axs = plt.subplots(2, sharex=True)
            
            axs[0].plot(the_t * delt, minSpread, 'o')
            axs[0].set(ylabel='min spead')
            
            axs[1].plot(the_t * delt, maxSpread, 'o')
            axs[1].set(ylabel='max spead')
            
            plt.show()
            sys.exit(1)

        # convert to physical units
        drewTime = the_t * delt
        
        # convert radians to angle
        _rad = np.deg2rad(thetas)
        drewVelocity = (delx/delt) * np.tan(_rad)
        drewVelocity = drewVelocity / 1000  # mm/s

        # debug, count inf and 0 tan
        # numZeros = np.count_nonzero(drewVelocity==0)
        # logger.info(f'  1) numZeros:{numZeros}')

        # remove inf and 0 tan()
        # np.tan(90 deg) is returning 1e16 rather than inf
        tan90or0 = (drewVelocity > 1e6) | (drewVelocity == 0)
        drewVelocity[tan90or0] = float('nan')

        # debug, count inf and 0 tan
        # numZeros = np.count_nonzero(drewVelocity==0)
        # logger.info(f'  2) numZeros:{numZeros}')

        # don't do this here, do it when we call getVelocity() in getReport()
        # 20230125, check if we have both pos/neg valocities
        # do this after removing outliers
        # in our main analysis we have already removed artifacts from usnig tan, e.g. (1e6, 0)
        # velocityDrew_no_outliers = self.getVelocity(removeOutliers=True, medianFilter=5)
        # _minVelSign = np.sign(np.nanmin(velocityDrew_no_outliers))
        # _maxVelSign = np.sign(np.nanmax(velocityDrew_no_outliers))
        # if _minVelSign != _maxVelSign:
        #     logger.error(f'  VELOCITY HAS BOTH POS AND NEGATIVE')
        #     logger.error(f'    file:{self.getFileName()}')
        #     logger.error(f'    minVel:{np.nanmin(velocityDrew_no_outliers)} maxVel:{np.nanmax(velocityDrew_no_outliers)}')
        # if self.checkPosNeg():
        #     logger.warning('')

        # feb 6, order matters
        #velocityDrew_no_outliers = self.getVelocity(removeOutliers=True, medianFilter=5)

        logger.info(f'  ')
        
        # create a df (saved in saveAnalysis())
        df = pd.DataFrame()
        df['time'] = drewTime
        df['velocity'] = drewVelocity
        # df['cleanVelocity'] = velocityDrew_no_outliers
        # df['absVelocity'] = np.abs(velocityDrew_no_outliers)
        df['parentFolder'] = analyzeflow.kymFlowUtil._getFolderName(self._tifPath)
        df['file'] = self.getFileName()
        df['algorithm'] = 'mpRadon'
        df['delx'] = delx
        df['delt'] = delt
        df['numLines'] = self.numLines()
        df['pntsPerLine'] = self.pntsPerLine()

        self._df = df

        # feb 6, order matters
        velocityDrew_no_outliers = self.getVelocity(removeOutliers=True, medianFilter=5)
        self._df['cleanVelocity'] = velocityDrew_no_outliers
        self._df['absVelocity'] = np.abs(velocityDrew_no_outliers)

    def checkPosNeg(self):
        """Check for both positive and negative vel AFTER removing outliers
        """
        # 20230125, check if we have both pos/neg valocities
        # we really need to do this after removing outliers
        velocityDrew = self.getVelocity(removeOutliers=True, medianFilter=0)
        _minVelSign = np.sign(np.nanmin(velocityDrew))
        _maxVelSign = np.sign(np.nanmax(velocityDrew))
        if _minVelSign != _maxVelSign:
            logger.warning(f'VELOCITY HAS BOTH POS AND NEGATIVE')
            logger.warning(f'  file:{self.getFileName()}')
            logger.warning(f'  minVel:{np.nanmin(velocityDrew)} maxVel:{np.nanmax(velocityDrew)}')
            return True
        else:
            return False

    def getVelocity(self,
                        removeZero : bool = False,
                        removeOutliers : bool = False,
                        medianFilter : int = 0,
                        absValue : bool = True) -> np.ndarray:
        """Get velocity from analysis.
        """
        velocityDrew = self._df[ self._df['algorithm']=='mpRadon' ]['velocity'].to_numpy()
        
        if removeZero:
            velocityDrew[velocityDrew==0] = np.nan

        if removeOutliers:
            # logger.info(f'  before removeOutliers: {velocityDrew.shape}')
            velocityDrew = analyzeflow.kymFlowUtil._removeOutliers(velocityDrew)
            # logger.info(f'    after removeOutliers: {velocityDrew.shape}')

        if medianFilter>0:
            velocityDrew = scipy.signal.medfilt(velocityDrew, medianFilter)

        if absValue:
            velocityDrew = np.abs(velocityDrew)

        return velocityDrew

    def getTime(self):
        """Get time from analysis.
        
        Different than time of line scan.
        """
        timeDrew = self._df[ self._df['algorithm']=='mpRadon' ]['time'].to_numpy()
        return timeDrew
        
    #def getReport(self, removeOutliers=True, removeZeros=True, medianFilter=0) -> dict:
    def getReport(self, removeOutliers=True, medianFilter=0) -> dict:
        """
        """

        # image intensity stats
        tifData = self._tifData
        meanInt = np.mean(tifData)
        minInt = np.min(tifData)
        maxInt = np.max(tifData)
        rangeInt = maxInt - minInt  # new 20230125

        # refine analysis per file
        # if timeLimitDict is not None and file in timeLimitDict.keys():
        #     # time-limit the df
        #     print(' . time limiting', file, timeLimitDict[file])
        #     minTime = timeLimitDict[file]['minTime']
        #     maxTime = timeLimitDict[file]['maxTime']
        #     oneDf = oneDf[ (oneDf['time'] >= minTime) & (oneDf['time'] <= maxTime)]  # seconds

        # count the number of nan in original analysis (nan is from tan of 1e6 or 0)
        velRaw = self.getVelocity(removeOutliers=False, medianFilter=0)
        nNanTan = np.count_nonzero(np.isnan(velRaw))

        vel_no_zero = self.getVelocity(removeZero=True, removeOutliers=True, medianFilter=medianFilter)
        meanVelNoZero = np.nanmean(vel_no_zero)

        vel_no_abs = self.getVelocity(removeOutliers=removeOutliers, medianFilter=medianFilter, absValue=False)
        meanVel_no_abs = np.nanmean(vel_no_abs)
        signMeanVel = np.sign(meanVel_no_abs)


        vel = self.getVelocity(removeOutliers=removeOutliers, medianFilter=medianFilter)

        # count the number of zeros and set them to nan
        # Jan 2023, now that we remove both tan 1e6 and 0, we should never have zeros
        numZeros = np.count_nonzero(vel==0)

        minVel = np.nanmin(vel)
        maxVel = np.nanmax(vel)
        rangeVel = maxVel - minVel
        meanVel = np.nanmean(vel)
        medianVel = np.nanmedian(vel)
        stdVel = np.nanstd(vel)
        nTotal = len(vel)

        # if we have both positive and negative flow (after removing outliers)
        # we should not have this if we have removed outliers
        signMin = np.sign(minVel)  # 0 vel will return 0
        signMax = np.sign(maxVel)
        #bothPosAndNegative = (signMin != signMax) | not (signMin==0 | signMax==0)
        if (signMin==0 or signMax==0):
            bothPosAndNegative = 0
        elif signMin != signMax:
            bothPosAndNegative = 1
        else:
            bothPosAndNegative = 0

        # remember, we use np.nan when tan(theta) goes to either inf or 0, e.g. >1e6 or ==0
        # nNan represent both inf and 0 results from tan(theta)
        nNonNan = np.count_nonzero(~np.isnan(vel))  # after removing outliers
        
        # sum of nan from tan and remove outliers
        nNanFinal = np.count_nonzero(np.isnan(vel))

        nNanOutliers = nNanFinal - nNanTan
    
        # make a column with parentFolder+'/'+file
        parentFolder = analyzeflow.kymFlowUtil._getFolderName(self._tifPath)

        oneDict = {
            # 'dateAnalyzed': self._dateAnalyzed,
            # 'timeAnalyzed': self._timeAnalyzed,

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
            'rangeInt': rangeInt,  # new 20230125
            
            'signMeanVel': signMeanVel,  # new 20230125, sign of the mean velocity (pos/neg is 1/-1)
            'posNegVel': bothPosAndNegative,  # new 20230125
            'minVel': minVel,
            'maxVel': maxVel,
            'rangeVel': rangeVel,
            'meanVel': meanVel,
            'medianVel': medianVel,  # added 20230125
            'stdVel': stdVel,
            'meanVelNoZero': meanVelNoZero,  # added 20230125, mean velocity after remove zero and remove outlier
            'nTotal': nTotal,
            'nNonNan': nNonNan,
            'nNanTan': nNanTan,  # added 20230125, number of nan from tan()
            'nNanOutliers': nNanOutliers,  # added 20230125, number of nans generated in remove outliers
            'nNanFinal': nNanFinal,
            'percentNanFinal': round(nNanFinal / nTotal * 100, 2),
            'percentGoodFinal': round(nNonNan / nTotal * 100, 2),
            'nZero': numZeros,  # added 20230125, will have 0 when (i) the image goes dark or (2) there is actually no flow
            
        }
        return oneDict

    def saveAnalysis(self):
        """Save analysis to csv.
        
        This is one row per line scan.
        """
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
        """Load corresponding csv from python radon analysis

        This is one line per line-scan
        """

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