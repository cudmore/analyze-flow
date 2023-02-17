from datetime import datetime
import os
import pathlib
import platform
import sys

import numpy as np

from qtpy import QtCore, QtWidgets, QtGui
import qdarkstyle

import analyzeflow
import analyzeflow.interface

from analyzeflow import get_logger
logger = get_logger(__name__)

class FlowWindow(QtWidgets.QMainWindow):
    def __init__(self, dbPath=None, dataPath=None, parent=None):
        """
        Args:
            dbPath: path to csv/xlsx of database summary
            dataPath: path to raw data folder
        """
        super().__init__(parent)

        self.dataPath = dataPath  #'/home/cudmore/Sites/declan-flow-analysis-shared/data'

        self._flowFile : analyzeflow.kymFlowFile = None

        self._controlStateDict = {
            'Remove Zero': True,
            'Remove Outliers': True,
            'Abs Value': False,
            'Median Filter': 5,
        }

        self._buildUI()  # kym image browser

        if dbPath is not None:
            self.scatterPlotWindow = analyzeflow.showScatterPlots(dbPath)  # scatter plots
            self.scatterPlotWindow.signalSelectFromPlot.connect(self.slot_selectFromScatter)

    def slot_selectFromScatter(self, selDict):
        """Received when a file is selected in scatter widget.
        """
        isShift = selDict['isShift']
        
        _folder, _file = selDict['path'].split('/')
        logger.info(f'isShift:{isShift} _folder: {_folder} _file:{_file}')

        tifPath = os.path.join(self.dataPath, _folder, _file)
        if not os.path.isfile(tifPath):
            logger.error(f'  did not find file')
            logger.error(f'  {tifPath}')
            return
        
        # load file
        flowFile = analyzeflow.kymFlowFile(tifPath)
        
        if isShift:
            # new window
            _newWindow = FlowWindow(dataPath=self.dataPath)
            _newWindow.slot_switchFile(flowFile)
            _newWindow.show()
        else:
            # one window we recycle for each scatter plot
            #self._kymFlowWidget.show()  # in case user closed it
            self.show()
            self.slot_switchFile(flowFile)

    def on_set_median_filter(self, value):
        if value % 2 == 0:
            value += 1  # value was even
        logger.info(f'{value}')
        self._controlStateDict['Median Filter'] = value
        self._replotVel()

    def on_check_clicked(self, state, name):
        logger.info(f'{name} {state}')
        state = state >= 1
        self._controlStateDict[name] = state
        self._replotVel()

    def _buildFlowControls(self) -> QtWidgets.QWidget:
        """Add a ctonrol bar to toggle flow plots.
        
        removeZero=removeZero, removeOutliers=removeOutliers, medianFilter=medianFilter, absValue=absValue
        """
        _removeZero = self._controlStateDict['Remove Zero']
        _removeOutliers = self._controlStateDict['Remove Outliers']
        _absValue = self._controlStateDict['Abs Value']
        _medianFilter = self._controlStateDict['Median Filter']

        hBoxLayout = QtWidgets.QHBoxLayout(self)

        _name = 'Remove Zero'
        aCheckbox = QtWidgets.QCheckBox(_name)
        aCheckbox.setChecked(_removeZero)
        _callbackFn = lambda state=None, name=_name: self.on_check_clicked(state, name)
        aCheckbox.stateChanged.connect(_callbackFn)
        hBoxLayout.addWidget(aCheckbox, alignment=QtCore.Qt.AlignLeft)

        _name = 'Remove Outliers'
        aCheckbox = QtWidgets.QCheckBox(_name)
        aCheckbox.setChecked(_removeOutliers)
        _callbackFn = lambda state=None, name=_name: self.on_check_clicked(state, name)
        aCheckbox.stateChanged.connect(_callbackFn)
        hBoxLayout.addWidget(aCheckbox, alignment=QtCore.Qt.AlignLeft)

        _name = 'Abs Value'
        aCheckbox = QtWidgets.QCheckBox(_name)
        aCheckbox.setChecked(_absValue)
        _callbackFn = lambda state=None, name=_name: self.on_check_clicked(state, name)
        aCheckbox.stateChanged.connect(_callbackFn)
        hBoxLayout.addWidget(aCheckbox, alignment=QtCore.Qt.AlignLeft)


        aLabel = QtWidgets.QLabel('Median Filter')
        hBoxLayout.addWidget(aLabel, alignment=QtCore.Qt.AlignLeft)

        aSpinBox = QtWidgets.QSpinBox()
        aSpinBox.setMinimum(0)
        aSpinBox.setMaximum(100)
        aSpinBox.setValue(_medianFilter)
        aSpinBox.setKeyboardTracking(False)
        aSpinBox.valueChanged.connect(self.on_set_median_filter)
        hBoxLayout.addWidget(aSpinBox)

        #
        hBoxLayout.addStretch()

        return hBoxLayout

    def _buildUI(self):
        self._centralWidget = QtWidgets.QWidget(self)
        _vLayout = QtWidgets.QVBoxLayout(self._centralWidget)

        #
        # kym image
        _fakeData = np.zeros((10,100)).astype(np.uint8)
        self._kymFlowWidget = analyzeflow.interface.kymographWidget(_fakeData)
        _vLayout.addWidget(self._kymFlowWidget)

        #
        # velocity controls
        _flowControls = self._buildFlowControls()
        _vLayout.addLayout(_flowControls)

        #
        # velocity plot
        self._velocityPlot = analyzeflow.interface.VelocityPlots()
        self._velocityPlot.slot_setVelPlot([], [])
        _vLayout.addWidget(self._velocityPlot)

        # connect x-axis of kym image widget with vel plot widget
        self._velocityPlot._velPlot.setXLink(self._kymFlowWidget.kymographPlot)

        # connect line slider
        self._kymFlowWidget.signalLineSliderChanged.connect(self._velocityPlot.slot_setLineSlider)
        
        self.setCentralWidget(self._centralWidget)

    def _replotVel(self):
        """Replot velocity with current state.
        """

        removeZero = self._controlStateDict['Remove Zero']
        removeOutliers = self._controlStateDict['Remove Outliers']
        absValue = self._controlStateDict['Abs Value']
        medianFilter = self._controlStateDict['Median Filter']

        yVel = self._flowFile.getVelocity(removeZero=removeZero,
                                        removeOutliers=removeOutliers,
                                        absValue=absValue,
                                        medianFilter=medianFilter)
        xVel = self._flowFile.getTime()
        
        self._velocityPlot.slot_setVelPlot(xVel, yVel)

    def closeEvent(self, event):
        """Caled when user closes window.
        """
        logger.info('')

    def slot_switchFile(self, flowFile : analyzeflow.kymFlowFile):
        """
        TODO: pass kymFlowFileInstead
        """
        #_flowFile = analyzeflow.kymFlowFile(path)
        self._flowFile = flowFile
        
        # update the image
        tifData = flowFile.tifData
        tifData = np.rot90(tifData)
        secondsPerLine = flowFile.delt()
        umPerPixel = flowFile.delx()
        filename = flowFile.getFileName()
        self._kymFlowWidget.slot_switchFile(tifData, secondsPerLine=secondsPerLine, umPerPixel=umPerPixel, filename=filename)

        # update the vel plot
        self._replotVel()
        # yVel = flowFile.getVelocity()
        # xVel = flowFile.getTime()
        # self._velocityPlot.slot_setVelPlot(xVel, yVel)
        
        # force rescaling (full view of kym)
        self._kymFlowWidget._resetZoom()
        self._velocityPlot._resetZoom()

        self.setWindowTitle(self._flowFile.getFileName())

def main(dbPath=None, dataPath=None):
    logger.info(f'Starting sanpy_app.py in __main__()')

    date_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'    {date_time_str}')

    logger.info(f'    Python version is {platform.python_version()}')
    #logger.info(f'    PyQt version is {QtCore.QT_VERSION_STR}')
    logger.info(f'    PyQt version is {QtCore.__version__}')

    # bundle_dir = sanpy._util.getBundledDir()
    # logger.info(f'    bundle_dir is "{bundle_dir}"')

    _logFilePath = analyzeflow._logger.getLoggerFile()
    logger.info(f'    logging to file {_logFilePath}')

    os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

    app = QtWidgets.QApplication(sys.argv)

    # appIconPath = pathlib.Path(bundle_dir) / 'interface' / 'icons' / 'sanpy_transparent.png'
    # appIconPathStr = str(appIconPath)
    # #logger.info(f'appIconPath is "{appIconPath}"')
    # if os.path.isfile(appIconPathStr):
    #     logger.info(f'    setting app window icon with: "{appIconPath}"')
    #     app.setWindowIcon(QtGui.QIcon(appIconPathStr))
    # else:
    #     logger.warning(f'    Did not find appIconPath: {appIconPathStr}')

    #app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api=os.environ['PYQTGRAPH_QT_LIB']))
    
    if dbPath is None:
        dbPath = '/home/cudmore/Sites/declan-flow-analysis-shared/flowSummary-20230216-rhc-v2.csv'
    if dataPath is None:
        dataPath = '/home/cudmore/Sites/declan-flow-analysis-shared/data'
    
    w = FlowWindow(dbPath=dbPath, dataPath=dataPath)

    # tmpPath = '/home/cudmore/Sites/declan-flow-analysis-shared/data/20221202/Capillary3.tif'
    # _flowFile = analyzeflow.kymFlowFile(tmpPath)
    # w.slot_switchFile(_flowFile)

    w.show()

    # to debug the meber function openLog()
    #w.openLog()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()