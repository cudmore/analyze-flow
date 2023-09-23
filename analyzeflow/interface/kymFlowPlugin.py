from PyQt5 import QtCore, QtWidgets, QtGui

import pyqtgraph as pg

import sanpy
from sanpy.interface.plugins import sanpyPlugin

import analyzeflow

from sanpy.sanpyLogger import get_logger
logger = get_logger(__name__)

class kymFlowWidget(QtWidgets.QMainWindow):
    """Widget to show
        - kymographWidget
        - control bar
        - velocity plot
    """
    def __init__(self, ba : sanpy.bAnalysis):
        super().__init__()
        
        self._ba = ba

        # todo: add API to create kymFlowFile from ba
        # v1
        # self._kymFlow = analyzeflow.kymFlowFile(ba.fileLoader.filepath)
        # v2
        self._kymFlow = analyzeflow.kymFlowFile(ba=ba)

        _report = self._kymFlow.getReport()
        for k,v in _report.items():
            logger.info(f'  {k}: {v}')
            
        self._buildUI()

    def _on_slider_changed(self, value : int = None):
        """Respond to user changing the "Line Scan" slider.

        Args:
            value: The line profile number
        """
        if self._ba is None:
            return

        if value is None:
            value = self._currentLineNumber
        else:
            self._currentLineNumber = value

        # logger.info(f"value:{value}")

        xScale = self._ba.fileLoader.tifHeader["secondsPerLine"]

        secondsValue = value * xScale

        # update vertical lines on top of plots
        for line in self._sliceLinesList:
            line.setValue(secondsValue)

    def doVelocityAnalysis(self):
        # todo, add interface with (window, start, stop)
        self._kymFlow.analyzeFlowWithRadon(windowSize = 16, startPixel=None, stopPixel=None)
        
        # update interface
        self.refreshVelocityPlot()
        
    def saveVelocityAnalysis(self):
        self._kymFlow.saveAnalysis()
        
    def _buttonCallback(self, name):
        logger.info(name)
        
        if name == 'Analyze':
            self.doVelocityAnalysis()
        elif name == 'Save':
            self.saveVelocityAnalysis()
        else:
            logger.info(f'did not understand name "{name}"')
            
    def _buildControlBar(self):
        hLayout = QtWidgets.QHBoxLayout()
        
        buttonName = 'Analyze'
        aButton = QtWidgets.QPushButton(buttonName)
        aButton.clicked.connect(
            lambda state, name=buttonName: self._buttonCallback(name)
        )
        hLayout.addWidget(aButton)
    
        buttonName = 'Save'
        aButton = QtWidgets.QPushButton(buttonName)
        aButton.clicked.connect(
            lambda state, name=buttonName: self._buttonCallback(name)
        )
        hLayout.addWidget(aButton)

        return hLayout
    
    def _buildUI(self):
        _mainWidget = QtWidgets.QWidget()
        vBoxLayout = QtWidgets.QVBoxLayout()
        _mainWidget.setLayout(vBoxLayout)
        self.setCentralWidget(_mainWidget)

        # kymograph widget from main interface
        self._kymWidgetMain = sanpy.interface.kymographWidget(self._ba)  # will handle ba is None
        self._kymWidgetMain.signalLineSliderChanged.connect(self._on_slider_changed)

        # v2 in a dock
        self.fileDock = QtWidgets.QDockWidget('Kymograph Image',self)
        self.fileDock.setWidget(self._kymWidgetMain)
        self.fileDock.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures | \
                                  QtWidgets.QDockWidget.DockWidgetVerticalTitleBar)
        self.fileDock.setFloating(False)
        self.fileDock.setTitleBarWidget(QtWidgets.QWidget())
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, self.fileDock)

        # controls
        _controlBar = self._buildControlBar()
        vBoxLayout.addLayout(_controlBar)
        
        # velocity plot
        self.velocityPlotItem = pg.PlotWidget()
        self.velocityPlotItem.setLabel("left", "Velocity", units="")
        self.velocityPlot = self.velocityPlotItem.plot(
                                name="velocityPlot",
                                pen=pg.mkPen('c', width=1)
                                )
        self.velocityPlot.setData([], [], connect="finite")  # fill with nan
        # link to kymographWidget plot of the image
        self.velocityPlotItem.setXLink(self._kymWidgetMain.kymographPlot)

        # vertical line to show "Line Profile"
        self._sliceLinesList = []
        sliceLine = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('y', width=2),)
        self._sliceLinesList.append(
            sliceLine
        )  # keep a list of vertical slice lines so we can update all at once
        self.velocityPlotItem.addItem(sliceLine)

        vBoxLayout.addWidget(self.velocityPlotItem)
        
        # important to get x-axis zoomed correctly
        self._kymWidgetMain._resetZoom()
        self.refreshVelocityPlot()
        
    def refreshVelocityPlot(self):
        if self._ba is None:
            return

        xTime = self._kymFlow.getTime()
        yVelocity = self._kymFlow.getVelocity()
        self.velocityPlot.setData(xTime, yVelocity, connect="finite")

class kymFlowPlugin(sanpyPlugin):
    myHumanName = "Kymograph Flow"

    def __init__(self, ba : sanpy.bAnalysis):
        """Kymograph flow plugin.
        """
        super().__init__(ba=ba)
        
        self._kymWidget = kymFlowWidget(ba)
    
        self.getVBoxLayout().addWidget(self._kymWidget)

        self.show()

    def replot(self):
        if self._kymWidget is None:
            self._kymWidget = sanpy.interface.kymographPlugin2(self.ba)
        self._kymWidget.slotSwitchFile(self.ba)

def testKymFlowPlugin():
    path = '/media/cudmore/data/Dropbox/data/declan/data/20221102/Capillary1_0001.tif'
    ba = sanpy.bAnalysis(path)

    import sys
    app = QtWidgets.QApplication([])
    
    kf = kymFlowPlugin(ba)

    sys.exit(app.exec_())

if __name__ == '__main__':
    testKymFlowPlugin()