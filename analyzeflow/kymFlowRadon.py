"""
Code to convert original Drew Lab velocity in Matlab into Python.

See:
    https://www.drew-lab.org/code

Implementing MultiProcessing version of this. mp version takes 15 versus normal non-mp of 81 sec

Now 80 down to 11 seconds !!!
"""

import math
import os
import sys
import time
import numpy as np
from skimage.transform import radon
from multiprocessing import Pool

from analyzeflow import get_logger
logger = get_logger(__name__)

def old_non_mp_analyzeFlow(data : np.ndarray, windowsize : int):
    """Original Radon algorithm (slow)
    See: mpAnalyzeFlow().
    """
    startSec = time.time()
    
    stepsize = .25 * windowsize
    stepsize = int(stepsize)

    nlines = data.shape[0]
    npoints = data.shape[1]
    nsteps = math.floor(nlines/stepsize)-3
    
    # print(' .   windowsize:', windowsize)
    # print(' .   stepsize:', stepsize)
    # print(' .   nlines:', nlines)
    # print(' .   npoints:', npoints)
    # print(' .   nsteps:', nsteps)

    # find the edges
    angles = np.arange(180)
    #print(' .   angles:', angles.shape, len(angles))

    _step = 0.25
    angles_fine= np.arange(-2, 2+_step, _step)  # [start, stop), step
    #print(' .   angles_fine:', angles_fine.shape, len(angles_fine))

    spread_matrix = np.zeros( (nsteps,len(angles)) )
    spread_matrix_fine = np.zeros( (nsteps,len(angles_fine)) )
    #thetas = np.zeros( (nsteps,1) )
    thetas = np.zeros(nsteps)

    #hold_matrix = np.ones( (windowsize,npoints) )
    # blank_matrix = np.ones( (nsteps,len(angles)) )
    the_t = np.ones(nsteps) * float('nan')

    # print(' .   spread_matrix:', spread_matrix.shape)
    # print(' .   spread_matrix_fine:', spread_matrix_fine.shape)
    # print(' .   thetas:', thetas.shape)
    # print(' .   the_t:', the_t.shape)

    doDebug = False
    if doDebug:
        nsteps = 100 # debug
    
    print(f'analyzeFlow() for tif data {tifData.shape}, nsteps: {nsteps}')
    print(' . THIS IS SUPER SLOW !!!')

    for k in range(nsteps):
        if doDebug: print(' .   k:', k, 'of', nsteps)

        the_t[k] = 1 + k*stepsize + windowsize/2

        _start = k * stepsize
        _stop = k * stepsize + windowsize
        data_hold = data[_start:_stop,:]
        
        # subtract the mean
        _mean = np.mean(data_hold[:])
        data_hold = data_hold - _mean # * hold_matrix
        
        radon_hold = radon(data_hold, theta=angles, circle=False) # radon_hold will be (windowSize, num angles))
                
        #take variance (one variance per column)
        _var = np.var(radon_hold, axis=0)
        spread_matrix[k,:] = _var

        # find max variace
        the_theta = np.argmax(spread_matrix[k,:])
        thetas[k]= angles[the_theta]     
        
        # re-do radon with finer increments around first estimate of the maximum
        _fineAngles = thetas[k]+angles_fine
        radon_hold_fine = radon(data_hold, theta=_fineAngles, circle=False)

        _var = np.var(radon_hold_fine, axis=0)
        spread_matrix_fine[k,:] = _var
        the_theta = np.argmax(spread_matrix_fine[k,:])

        thetas[k] = thetas[k] + angles_fine[the_theta]
    
    #thetas=thetas-90; %rotate

    stopSec = time.time()
    print('analyzeFlow took', round(stopSec-startSec,3), 'seconds')
    
    return thetas,the_t,spread_matrix

#def radonWorker(k, data, stepsize, windowsize, angles, angles_fine):
def radonWorker(data_hold, angles, angles_fine):
    """Multiprocessing worker to calculate flow for one time step.

    TODO: pass in data_hold rather than full kymograph data.

    Args:
        data: full kymograph

    Return:
        All variables worker_
    """
    # do in main
    # the_t[k] = 1 + k*stepsize + windowsize/2

    # do in main
    # _start = k * stepsize
    # _stop = k * stepsize + windowsize
    # data_hold = data[_start:_stop,:]
    
    # subtract the mean
    _mean = np.mean(data_hold[:])
    data_hold = data_hold - _mean # * hold_matrix
    
    radon_hold = radon(data_hold, theta=angles, circle=False) # radon_hold will be (windowSize, num angles))
            
    #take variance (one variance per column)
    _var = np.var(radon_hold, axis=0)
    #spread_matrix[k,:] = _var
    worker_spread_matrix = _var # return

    # find max variace
    #the_theta = np.argmax(spread_matrix[k,:])
    the_theta = np.argmax(worker_spread_matrix)
    #thetas[k]= angles[the_theta]     
    worker_thetas = angles[the_theta]     
    
    # re-do radon with finer increments around first estimate of the maximum
    #_fineAngles = thetas[k]+angles_fine
    _fineAngles = worker_thetas + angles_fine
    radon_hold_fine = radon(data_hold, theta=_fineAngles, circle=False)

    _var = np.var(radon_hold_fine, axis=0)
    #spread_matrix_fine[k,:] = _var
    worker_spread_matrix_fine = _var
    #the_theta = np.argmax(spread_matrix_fine[k,:])
    the_theta = np.argmax(worker_spread_matrix_fine)

    #thetas[k] = thetas[k] + angles_fine[the_theta]
    worker_thetas = worker_thetas + angles_fine[the_theta]

    #return thetas,the_t,spread_matrix
    # return all worker_ variables
    return worker_thetas, worker_spread_matrix
    
def mpAnalyzeFlow(data : np.ndarray,
                    windowsize : int,
                    startPixel : int = None,
                    stopPixel : int = None):
    """Given a blood flow kymograph, calculate blood flow velocity.
    
    Args:
        data: 2-D numpy array kymograph with size (time, space)
        windowsize: Number of line scans to use in estimating velocity
            Must be a factor of 4
        startPixel:
        stopPixel:
    
    Algorithm:
        Calculates radon transform for a number of sliding windows.
        Adapted from Drew Lab Matlab code.
            See: 
    """
    startSec = time.time()
    
    stepsize = .25 * windowsize
    stepsize = int(stepsize)

    nlines = data.shape[0]
    npoints = data.shape[1]
    nsteps = math.floor(nlines/stepsize)-3
    
    # TODO: allow user to specify start/stop pixels (space)
    if startPixel is None:
        startPixel = 0
    if stopPixel is None:
        stopPixel = npoints

    # find the edges
    angles = np.arange(180)

    _step = 0.25
    angles_fine= np.arange(-2, 2+_step, _step)  # [start, stop), step

    spread_matrix = np.zeros( (nsteps,len(angles)) )
    #spread_matrix_fine = np.zeros( (nsteps,len(angles_fine)) )
    thetas = np.zeros(nsteps)

    #hold_matrix = np.ones( (windowsize,npoints) )
    # blank_matrix = np.ones( (nsteps,len(angles)) )
    the_t = np.ones(nsteps) * float('nan')

    doDebug = False
    if doDebug:
        nsteps = 100 # debug
    
    logger.info(f'tif data {data.shape}')
    logger.info(f'  windowsize: {windowsize}')
    logger.info(f'  startPixel: {startPixel}')
    logger.info(f'  stopPixel: {stopPixel}')
    logger.info(f'  nsteps: {nsteps}')


    result_objs = []
    with Pool(processes=os.cpu_count() - 1) as pool:

        for k in range(nsteps):

            the_t[k] = 1 + k*stepsize + windowsize/2

            _start = k * stepsize
            _stop = k * stepsize + windowsize
            #data_hold = data[_start:_stop,:]
            data_hold = data[_start:_stop, startPixel:stopPixel]

            #radonWorker(data, stepsize, windowsize, angles, angles_fine)
            #workerParams = (k, data, stepsize, windowsize, angles, angles_fine)
            workerParams = (data_hold, angles, angles_fine)
            result = pool.apply_async(radonWorker, workerParams)
            result_objs.append(result)

        results = [result.get() for result in result_objs]
        #print(len(results))

        # return worker_thetas, worker_spread_matrix
        for k, results in enumerate(results):
            # results is a tuple
            thetas[k] = results[0]
            spread_matrix[k] = results[1]

    stopSec = time.time()
    logger.info(f'  took {round(stopSec-startSec)} seconds')

    return thetas, the_t, spread_matrix

def compareMatlabPythonRadon():
    """Check if we get a similar answer in Python and Matlab.
    
    Yes, we do !!!

    See: https://www.mathworks.com/help/images/ref/radon.html
    """
    img = np.zeros((100,100))
    img[25:75, 25:75] = 1

    theta = range(180)
    rImg = radon(img,theta)

    # imshow(R,[],'Xdata',theta,'Ydata',xp,'InitialMagnification','fit')
    import matplotlib.pyplot as plt
    plt.imshow(rImg)
    plt.show()

def old_analyzeOne(tifPath):
    import pandas as pd
    import tifffile
    import flowUtil
    from flowUtil import _readOlympusHeader

    tifData = tifffile.imread(tifPath)
    print('tifData:', tifData.shape)  # (30000, 38)
    numLines = tifData.shape[0]
    pntsPerLine = tifData.shape[1]
    
    # load Olympus header from txt file
    headerDict = _readOlympusHeader(tifPath)
    delx = headerDict['umPerPixel']
    delt = headerDict['secondsPerLine']

    # the speed scales with window size, larger window size is faster
    windowSize = 16
    startPixel = None  #5  #
    stopPixel = None  #pntsPerLine - 5  #
    thetas,the_t,spread_matrix = mpAnalyzeFlow(tifData,
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

    # from flowUtil import _removeOutliers
    # drewVelocity = _removeOutliers(drewVelocity)

    # create a df
    df = pd.DataFrame()
    df['time'] = drewTime
    df['velocity'] = drewVelocity
    df['parentFolder'] = 'parentFolder'
    df['file'] = os.path.split(tifPath)[1]
    df['algorithm'] = 'mpRadon'
    df['delx'] = delx
    df['delt'] = delt
    df['numLines'] = numLines
    df['pntsPerLine'] = pntsPerLine

    doSave = True
    if doSave:
        savePath = flowUtil._getAnalysisPath_v2(tifPath)
        if not os.path.isdir(savePath):
            os.mkdir(savePath)
        csvFileName = os.path.split(tifPath)[1]
        csvFileName = os.path.splitext(csvFileName)[0] + '.csv'
        saveFilePath = os.path.join(savePath, csvFileName)
        print('saving:', saveFilePath)
        df.to_csv(saveFilePath)

    return df

def batchAnalyzeFolder(folderPath):
    """Analyze and save a folder of tif.
    """
    
    import analyzeflow
    
    files = os.listdir(folderPath)
    files = sorted(files)
    for file in files:
        if not file.endswith('.tif'):
            continue
        tifPath = os.path.join(folderPath, file)

        kff = analyzeflow.kymFlowFile(tifPath)

        kff.analyzeFlowWithRadon()  # do actual kym radon analysis
        kff.saveAnalysis()  # save result to csv


if __name__ == '__main__':
    # testRadon()
    # sys.exit(1)

    # compareAlg()
    # sys.exit(1)

    # compareStartStop()
    # sys.exit(1)

    folderPath = '/Users/cudmore/Dropbox/data/declan/Flow TIFs'
    folderPath = '/Users/cudmore/Dropbox/data/declan/20221102'
    folderPath = '/Users/cudmore/Dropbox/data/declan/20221206'
    batchAnalyzeFolder(folderPath)
    sys.exit(1)
    
    import tifffile
        
    tifPath = '/Users/cudmore/Dropbox/data/declan/Bloodflow TIFs nov 23/20221102/test-python/Capillary1_0001.tif'
    tifPath = '/Users/cudmore/Dropbox/data/declan/Bloodflow TIFs nov 23/20221102/Capillary5_0001.tif'
    tifPath = '/Users/cudmore/Dropbox/data/declan/Bloodflow TIFs nov 23/20221102/Capillary6_0001.tif'

    tifData = tifffile.imread(tifPath)
    print('tifData:', tifData.shape)  # (30000, 38)
    numLines = tifData.shape[0]
    pntsPerLine = tifData.shape[1]
    
    # units for this one .tif file
    from flowUtil import _readOlympusHeader
    headerDict = _readOlympusHeader(tifPath)
    delx = headerDict['umPerPixel']
    delt = headerDict['secondsPerLine']

    # the speed scales with window size, larger window size is faster
    windowSize = 16

    # single thread (slow)
    # if False:
    #     thetas,the_t,spread_matrix = analyzeFlow(tifData, windowSize)

    #     # convert to physical units
    #     drewTime = the_t * delt
        
    #     _rad = np.deg2rad(thetas)
    #     #drewVelocity = np.tan(thetas * math.pi / 180)
    #     drewVelocity = (delx/delt) * np.tan(_rad)
    #     drewVelocity = drewVelocity / 1000

    #     # np.tan(90 deg) is returning 1e16 rather than inf
    #     tan90 = drewVelocity > 1e6
    #     drewVelocity[tan90] = float('nan')

    #     # from flowUtil import _removeOutliers
    #     # drewVelocity = _removeOutliers(drewVelocity)

    #     # save as df
    #     import pandas as pd
    #     df = pd.DataFrame()
    #     df['time'] = drewTime
    #     df['velocity'] = drewVelocity
    #     df.to_csv('/Users/cudmore/Desktop/drewRadon.csv')

    # mp
    startPixel = 5  #
    stopPixel = pntsPerLine - 5  #
    thetas,the_t,spread_matrix = mpAnalyzeFlow(tifData,
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

    # from flowUtil import _removeOutliers
    # drewVelocity = _removeOutliers(drewVelocity)

    # save as df
    import pandas as pd
    df = pd.DataFrame()
    df['time'] = drewTime
    df['velocity'] = drewVelocity
    df['algorithm'] = 'mpRadon'
    df['delx'] = delx
    df['delt'] = delt
    df['numLines'] = numLines
    df['pntsPerLine'] = pntsPerLine

    savePath = '/Users/cudmore/Desktop'
    csvFileName = os.path.split(tifPath)[1]
    csvFileName = os.path.splitext(csvFileName)[0] + '.csv'
    saveFilePath = os.path.join(savePath, csvFileName)
    print('saving:', saveFilePath)
    df.to_csv(saveFilePath)

    # plot theta and velocity
    if 1:
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(2, sharex=True)
        axs[0].plot(drewTime, thetas, 'o')
        axs[1].plot(drewTime, drewVelocity, 'o')
        plt.show()

