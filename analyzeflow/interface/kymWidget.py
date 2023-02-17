"""
Display a tif kymograph and allow user to modify a rect roi

Used by main SanPy interface and kymograph plugin
"""

import sys
import numpy as np
from functools import partial

from PyQt5 import QtCore, QtWidgets, QtGui
import pyqtgraph as pg

# import sanpy
# from sanpy.sanpyLogger import get_logger

from analyzeflow import get_logger
logger = get_logger(__name__)

class myCustomDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Set Kymograph Scale!")

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        hLayout = QtWidgets.QHBoxLayout()

        xScaleLabel = QtWidgets.QLabel('Seconds/Line')
        self.xScale = QtWidgets.QDoubleSpinBox()
        self.xScale.setDecimals(4)

        yScaleLabel = QtWidgets.QLabel('Microns/Pixel')
        self.yScale = QtWidgets.QDoubleSpinBox()
        self.yScale.setDecimals(4)

        hLayout.addWidget(xScaleLabel)
        hLayout.addWidget(self.xScale)

        hLayout.addWidget(yScaleLabel)
        hLayout.addWidget(self.yScale)

        self.layout = QtWidgets.QVBoxLayout()
        #message = QtWidgets.QLabel("Set Kymograph Scale")
        #self.layout.addWidget(message)
        
        self.layout.addLayout(hLayout)
        
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def getResults(self) -> dict:
        """Get values from user input.
        """
        xScale = self.xScale.value()
        yScale = self.yScale.value()
        retDict = {
            'secondsPerLine': xScale,
            'umPerPixel': yScale,
        }
        return retDict

def showdialog():
    d = QtWidgets.QDialog()
    b1 = QtWidgets.QPushButton("ok", d)
    b1.move(50,50)
    d.setWindowTitle("Set Kymograph Scale")
    d.setWindowModality(QtCore.Qt.ApplicationModal)
    d.exec_()

class VelocityPlots(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self._sweepX = None
        
        self._buildUI()

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self._resetZoom()

    def _resetZoom(self):
        self._velPlot.autoRange()

    def slot_setVelPlot(self, x, y):
        """Set the velocity"""
        logger.info(f'x:{len(x)} y:{len(y)}')
        self._sweepX = x
        self._velPlotItem.setData(x=x, y=y) # start empty
        
        # only auto range when we set file
        # self._velPlot.autoRange()

    def slot_setLineSlider(self, lineNumber : int, lineSeconds : float):
        """Respond to user setting line slider.
        
        Plots have x-axis (_sweepX) in seconds, the length is less
            than number of line scans in kymograph because we have a sliding window
        """        
        # _sweepX is from analysis, has fewer points than kym image (line scans)
        x = np.argwhere(self._sweepX >= lineSeconds)
        if len(x) > 0:
            x = x[0][0]
        else:
            x = len(self._sweepX) - 1
        x = self._sweepX[x]
        self._sliceLine.setValue(x)

    def _buildUI(self):
        self.myVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.myVBoxLayout.setAlignment(QtCore.Qt.AlignTop)

        # _flowContorls = self._buildFlowControls()
        # self.myVBoxLayout.addLayout(_flowContorls)

        self.view = pg.GraphicsLayoutWidget()

        # plot flow
        rowSpan = 1
        colSpan = 1
        row = 1
        self._velPlot = self.view.addPlot(row=row, col=0, rowSpan=rowSpan, colSpan=colSpan)  # pyqtgraph.graphicsItems.PlotItem
        self._velPlot.setMouseEnabled(x=True, y=False)

        self._velPlotItem = pg.PlotDataItem(connect='finite')
        self._velPlot.addItem(self._velPlotItem)

        # I want y-axis to auto-range, not x ???
        # self._velPlot.enableAutoRange()

        # link x-axis between plots
        #velPlot.setXLink(self.kymographPlot)

        # TODO: add show/hide, we do not want this in the main interface
        # vertical line to show selected line scan (adjusted/changed with slider)
        self._sliceLine = pg.InfiniteLine(pos=0, angle=90)
        #self._sliceLinesList.append(sliceLine) # keep a list of vertical slice lines so we can update all at once
        self._velPlot.addItem(self._sliceLine)

        self.myVBoxLayout.addWidget(self.view)

class kymographImage(pg.ImageItem):
    """
    Utility class to inherit and redefine some functions.
    """
    def mouseClickEvent(self, event):
        #print("Click", event.pos())
        x = event.pos().x()
        y = event.pos().y()

    def mouseDragEvent(self, event):
        return

        if event.isStart():
            print("Start drag", event.pos())
        elif event.isFinish():
            print("Stop drag", event.pos())
        else:
            print("Drag", event.pos())

    def old_hoverEvent(self, event):
        logger.info('')
        if not event.isExit():
            # the mouse is hovering over the image; make sure no other items
            # will receive left click/drag events from here.
            event.acceptDrags(pg.QtCore.Qt.LeftButton)
            event.acceptClicks(pg.QtCore.Qt.LeftButton)

def _buildColorLut():
    """Build standard color lookup tables (LUT).
    """
    _colorLutDict = {}

    pos = np.array([0.0, 0.5, 1.0])
    #
    grayColor = np.array([[0,0,0,255], [128,128,128,255], [255,255,255,255]], dtype=np.ubyte)
    map = pg.ColorMap(pos, grayColor)
    lut = map.getLookupTable(0.0, 1.0, 256)
    _colorLutDict['gray'] = lut

    grayColor_r = np.array([[255,255,255,255], [128,128,128,255], [0,0,0,255]], dtype=np.ubyte)
    map = pg.ColorMap(pos, grayColor_r)
    lut = map.getLookupTable(0.0, 1.0, 256)
    _colorLutDict['gray_r'] = lut

    greenColor = np.array([[0,0,0,255], [0,128,0,255], [0,255,0,255]], dtype=np.ubyte)
    map = pg.ColorMap(pos, greenColor)
    lut = map.getLookupTable(0.0, 1.0, 256)
    _colorLutDict['green'] = lut
    _colorLutDict['g'] = lut

    redColor = np.array([[0,0,0,255], [128,0,0,255], [255,0,0,255]], dtype=np.ubyte)
    map = pg.ColorMap(pos, redColor)
    lut = map.getLookupTable(0.0, 1.0, 256)
    _colorLutDict['red'] = lut
    _colorLutDict['r'] = lut

    blueColor = np.array([[0,0,0,255], [0,0,128,255], [0,0,266,255]], dtype=np.ubyte)
    map = pg.ColorMap(pos, blueColor)
    lut = map.getLookupTable(0.0, 1.0, 256)
    _colorLutDict['blue'] = lut
    _colorLutDict['b'] = lut

    return _colorLutDict

class kymographWidget(QtWidgets.QWidget):
    """Display a kymograph with contrast controls.
    """
    signalKymographRoiChanged = QtCore.pyqtSignal(object)  # list of [l, t, r, b]
    old_signalSwitchToMolar = QtCore.pyqtSignal(object, object, object)  # (boolean, kd, caConc)
    #signalScaleChanged = QtCore.pyqtSignal(object)  # dict with x/y scale
    signalLineSliderChanged = QtCore.pyqtSignal(int, float)  # (line number, seconds), new line selected

    def __init__(self, tifData : np.ndarray,
                        secondsPerLine : float = 0.001,
                        umPerPixel : float = 0.1,
                        filename : str = '',
                        parent=None):
        """A widget to display a kymograph image.

        Args:
            tifData:
        """
        super().__init__(parent)
        
        bitDepth = 8
        self._minContrast = 0
        self._maxContrast = 2**bitDepth - 1

        #self.ba = ba  # feb 2023, converted from bAnalysis to primitive types (tifData, dx, dy)

        self._stateDict = {
            'showRoiInterface': False,
        }

        self._setImage(tifData, secondsPerLine, umPerPixel, filename)
        # self._tifData = tifData
        # self._sweepX = np.arange(self.numLineScans)
        # self._secondsPerLine = secondsPerLine
        # self._umPerPixel = umPerPixel
        # self._filename : str = filename

        self.myImageItem : kymographImage = None  # kymographImage
        self.myLineRoi = None
        self.myLineRoiBackground = None
        self.myColorBarItem = None

        self._colorLut : dict = _buildColorLut()

        self._buildUI()
        self._replot()

    def _showRoiInterface(self):
        return self._stateDict['showRoiInterface']
    
    def _setImage(self, tifData, secondsPerLine, umPerPixel, filename):
        self._tifData = tifData
        #self._sweepX = np.arange(self.numLineScans)
        self._secondsPerLine = secondsPerLine
        self._umPerPixel = umPerPixel
        self._filename : str = filename
    
    def slot_switchFile(self, tifData, secondsPerLine: float = 0.001, umPerPixel : float = 0.1, filename = ''):
        
        self._setImage(tifData, secondsPerLine, umPerPixel, filename)

        #self._updateRoiMinMax(theRect)
        self._replot()

        # update line scan slider
        _numLineScans = self.numLineScans - 1
        self._profileSlider.setMaximum(_numLineScans)

        # update filename
        self._fileNameLabel.setText(filename)

        # update x/y pixels
        yPixels, xPixels = self.tifData.shape
        self.xPixelLabel.setText(str(xPixels))
        self.yPixelLabel.setText(str(yPixels))

        # update scale
        _msPerLine = self.secondsPerLine * 1000
        _msPerLine = round(_msPerLine,2)
        self.xScaleLabel.setText(str(_msPerLine))
        self.yScaleLabel.setText(str(self.umPerPixel))

        # update line slider
        self._profileSlider.setMaximum(self.numLineScans)
        self._profileSlider.setValue(0)  # reset to first line (might trigger signal?)

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self._resetZoom()

    def _resetZoom(self):

        # _rect = self.getKymographImageRect()
        # logger.info(f'_rect:{_rect}')
        
        # bot these work but image is not updated
        #self.myImageItem.setOpts(update=True, rect=_rect)  # [x,y,w,h] in physical units
        #self.myImageItem.setRect(_rect)  # [x,y,w,h] in physical units
        #self.myImageItem.update()

        self.kymographPlot.autoRange()

    def on_button_click(self, name):
        logger.info(name)
        if name == 'Reset ROI':
            logger.info('IMPLEMENT THIS')
            #newRect = self.ba.fileLoader.resetKymographRect()
            # self._replot()
            # self.signalKymographRoiChanged.emit(newRect)  # underlying _abf has new rect

        else:
            logger.info(f'Case not taken: {name}')

    def old_on_convert_to_nm_clicked(self, value):
        onOff = value==2
        #self.detectionWidget.toggleCrosshair(onOff)
        self.signalSwitchToMolar.emit(onOff)

    def old_buildMolarLayout(self):
        """Layout to conver sum intensity (for each line scan) into molar.
       
        Seems a bit silly.
        """
        molarLayout = QtWidgets.QHBoxLayout()

        # todo: add checkbox to turn kn/rest calculation on off
        #            need signal
        convertToMolarCheckBox = QtWidgets.QCheckBox('Convert to Molar')
        convertToMolarCheckBox.setChecked(False)
        convertToMolarCheckBox.stateChanged.connect(self.on_convert_to_nm_clicked)
        convertToMolarCheckBox.setDisabled(True)
        molarLayout.addWidget(convertToMolarCheckBox)

        #
        # kd
        kdLabel = QtWidgets.QLabel('kd')
        molarLayout.addWidget(kdLabel)

        kdDefault = 22.1
        self.kdSpinBox = QtWidgets.QDoubleSpinBox()
        self.kdSpinBox.setMinimum(0)
        self.kdSpinBox.setMaximum(+1e6)
        self.kdSpinBox.setValue(kdDefault)
        self.kdSpinBox.setDisabled(True)
        #self.kdSpinBox.setSpecialValueText("None")
        molarLayout.addWidget(self.kdSpinBox)

        #
        # resting Ca
        restingCaLabel = QtWidgets.QLabel('Resting Ca')
        molarLayout.addWidget(restingCaLabel)

        restingCaDefault = 113.7
        self.restingCaSpinBox = QtWidgets.QDoubleSpinBox()
        self.restingCaSpinBox.setMinimum(0)
        self.restingCaSpinBox.setMaximum(+1e6)
        self.restingCaSpinBox.setValue(restingCaDefault)
        self.restingCaSpinBox.setDisabled(True)
        #self.kdSpinBox.setSpecialValueText("None")
        molarLayout.addWidget(self.restingCaSpinBox)

        return molarLayout

    @property
    def tifData(self):
        return self._tifData

    # @property
    # def sweepX(self):
    #     return self._sweepX

    @property
    def numLineScans(self):
        return self.tifData.shape[1]

    @property
    def numPntsInLine(self):
        return self.tifData.shape[0]

    @property
    def secondsPerLine(self):
        return self._secondsPerLine
        
    @property
    def umPerPixel(self):
        return self._umPerPixel
    
    @property
    def filename(self):
        return self._filename

    def _buildControlBarLayout(self):

        xScale = self.secondsPerLine
        yScale = self.umPerPixel
        yPixels, xPixels = self.tifData.shape  # numpy order is (y,x)

        controlBarLayout = QtWidgets.QHBoxLayout()

        self._fileNameLabel = QtWidgets.QLabel(f'{self.filename}')
        controlBarLayout.addWidget(self._fileNameLabel, alignment=QtCore.Qt.AlignLeft)

        # pixels
        
        aLabel = QtWidgets.QLabel(f'Pixels X:')
        controlBarLayout.addWidget(aLabel, alignment=QtCore.Qt.AlignLeft)

        self.xPixelLabel = QtWidgets.QLabel(f'{xPixels}')
        controlBarLayout.addWidget(self.xPixelLabel, alignment=QtCore.Qt.AlignLeft)

        aLabel = QtWidgets.QLabel(f'Y:')
        controlBarLayout.addWidget(aLabel, alignment=QtCore.Qt.AlignLeft)

        self.yPixelLabel = QtWidgets.QLabel(f'{yPixels}')
        controlBarLayout.addWidget(self.yPixelLabel, alignment=QtCore.Qt.AlignLeft)

        # scale
        
        aLabel = QtWidgets.QLabel(f'Scale ms/line')
        controlBarLayout.addWidget(aLabel, alignment=QtCore.Qt.AlignLeft)

        self.xScaleLabel = QtWidgets.QLabel(f'{xScale}')
        controlBarLayout.addWidget(self.xScaleLabel, alignment=QtCore.Qt.AlignLeft)

        aLabel = QtWidgets.QLabel(f'um/pixel')
        controlBarLayout.addWidget(aLabel, alignment=QtCore.Qt.AlignLeft)

        self.yScaleLabel = QtWidgets.QLabel(f'{yScale}')
        controlBarLayout.addWidget(self.yScaleLabel, alignment=QtCore.Qt.AlignLeft)

        # reset
        
        buttonName = 'Reset ROI'
        button = QtWidgets.QPushButton(buttonName)
        #button.setToolTip('Detect spikes using dV/dt threshold.')
        button.clicked.connect(partial(self.on_button_click,buttonName))
        button.setVisible(self._showRoiInterface())
        controlBarLayout.addWidget(button, alignment=QtCore.Qt.AlignLeft)

        self.tifCursorLabel = QtWidgets.QLabel('Intensity:')
        controlBarLayout.addWidget(self.tifCursorLabel, alignment=QtCore.Qt.AlignRight)

        controlBarLayout.addStretch()

        return controlBarLayout


    def _buildUI(self):
        # one row of controls and then kymograph image
        self.myVBoxLayout = QtWidgets.QVBoxLayout(self)
        self.myVBoxLayout.setAlignment(QtCore.Qt.AlignTop)

        if 0:
            molarLayout = self._buildMolarLayout()
            self.myVBoxLayout.addLayout(molarLayout) #

        #
        controlBarLayout = self._buildControlBarLayout()
        self.myVBoxLayout.addLayout(controlBarLayout) #

        #
        # contrast sliders
        bitDepth = 8

        # min
        minContrastLayout = QtWidgets.QHBoxLayout()

        minLabel = QtWidgets.QLabel('Min')
        minContrastLayout.addWidget(minLabel)

        self.minContrastSpinBox = QtWidgets.QSpinBox()
        self.minContrastSpinBox.setMinimum(0)
        self.minContrastSpinBox.setMaximum(2**bitDepth)
        minContrastLayout.addWidget(self.minContrastSpinBox)

        minContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        minContrastSlider.setMinimum(0)
        minContrastSlider.setMaximum(2**bitDepth)
        minContrastSlider.setValue(0)
        #myLambda = lambda chk, item=canvasName: self._userSelectCanvas(chk, item)
        minContrastSlider.valueChanged.connect(lambda val,name='min': self._onContrastSliderChanged(val, name))
        minContrastLayout.addWidget(minContrastSlider)

        # image min
        self.tifMinLabel = QtWidgets.QLabel('Int Min:')
        minContrastLayout.addWidget(self.tifMinLabel)

        # roi min
        self.roiMinLabel = QtWidgets.QLabel('ROI Min:')
        self.roiMinLabel.setVisible(self._showRoiInterface())
        minContrastLayout.addWidget(self.roiMinLabel)

        self.myVBoxLayout.addLayout(minContrastLayout) #

        # max
        maxContrastLayout = QtWidgets.QHBoxLayout()

        maxLabel = QtWidgets.QLabel('Int Max')
        maxContrastLayout.addWidget(maxLabel)

        self.maxContrastSpinBox = QtWidgets.QSpinBox()
        self.maxContrastSpinBox.setMinimum(0)
        self.maxContrastSpinBox.setMaximum(2**bitDepth)
        self.maxContrastSpinBox.setValue(2**bitDepth)
        maxContrastLayout.addWidget(self.maxContrastSpinBox)

        maxContrastSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        maxContrastSlider.setMinimum(0)
        maxContrastSlider.setMaximum(2**bitDepth)
        maxContrastSlider.setValue(2**bitDepth)
        maxContrastSlider.valueChanged.connect(lambda val,name='max': self._onContrastSliderChanged(val, name))
        maxContrastLayout.addWidget(maxContrastSlider)

        # image max
        self.tifMaxLabel = QtWidgets.QLabel('Max:')
        maxContrastLayout.addWidget(self.tifMaxLabel)

        # roi max
        self.roiMaxLabel = QtWidgets.QLabel('ROI Max:')
        self.roiMaxLabel.setVisible(self._showRoiInterface())
        maxContrastLayout.addWidget(self.roiMaxLabel)

        self.myVBoxLayout.addLayout(maxContrastLayout) #

        #
        # kymograph
        self.view = pg.GraphicsLayoutWidget()
        #self.view.show()
        #self.kymographWindow = pg.PlotWidget()

        row = 0
        colSpan = 1
        rowSpan = 1
        self.kymographPlot = self.view.addPlot(row=row, col=0, rowSpan=rowSpan, colSpan=colSpan)  # pyqtgraph.graphicsItems.PlotItem
        self.kymographPlot.enableAutoRange()
        # turn off x/y dragging of deriv and vm
        self.kymographPlot.setMouseEnabled(x=True, y=False)
        # hide the little 'A' button to rescale axis
        self.kymographPlot.hideButtons()
        # turn off right-click menu
        self.kymographPlot.setMenuEnabled(False)
        # hide by default
        #self.kymographPlot.hide()  # show in _replot() if self.ba.isKymograph()

        # TODO: add show/hide, we do not want this in the main interface
        # vertical line to show selected line scan (adjusted/changed with slider)
        self._sliceLine = pg.InfiniteLine(pos=0, angle=90)
        #self._sliceLinesList.append(sliceLine) # keep a list of vertical slice lines so we can update all at once
        self.kymographPlot.addItem(self._sliceLine)

        #
        # # add scatter plot for rising/falling diameter detection
        # color = 'g'
        # symbol = 'o'
        # leftDiamScatterPlot = pg.PlotDataItem(pen=None, symbol=symbol, symbolSize=6, symbolPen=None, symbolBrush=color)
        # leftDiamScatterPlot.setData(x=[], y=[]) # start empty

        # color = 'r'
        # symbol = 'o'
        # rightDiamScatterPlot = pg.PlotDataItem(pen=None, symbol=symbol, symbolSize=6, symbolPen=None, symbolBrush=color)
        # rightDiamScatterPlot.setData(x=[], y=[]) # start empty

        # self.kymographPlot.addItem(leftDiamScatterPlot)
        # self.kymographPlot.addItem(rightDiamScatterPlot)

        #
        # 1.5) slider to step through "Line Profile"
        self._profileSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._profileSlider.setMinimum(0)
        self._profileSlider.setMaximum(self.numLineScans)
        self._profileSlider.valueChanged.connect(self._on_line_slider_changed)
        self.myVBoxLayout.addWidget(self._profileSlider)

        # _velPlotWidget = VelocityPlots()
        # _velPlotWidget._velPlot.setXLink(self.kymographPlot)
        # self.myVBoxLayout.addWidget(_velPlotWidget)

        # flow controls
        # _flowControlsLayout = self._buildFlowControls()
        # self.myVBoxLayout.addLayout(_flowControlsLayout)

        # plot flow
        self.myVBoxLayout.addWidget(self.view)

    def showLineSlider(self, visible):
        """Toggle line slider and vertical line (on image) on/off.
        """
        self._profileSlider.setVisible(visible)

    def _on_line_slider_changed(self, lineNumber :int):
        """Respond to user dragging the line slider.
        
        Args:
            lineNumber: Int line number, needs to be converted to 'seconds'
        """

        lineSeconds = lineNumber * self.secondsPerLine

        logger.info(f'lineNumber:{lineNumber} lineSeconds:{lineSeconds}')

        # set the vertical line
        self._sliceLine.setValue(lineSeconds)

        self.signalLineSliderChanged.emit(lineNumber, lineSeconds)
    
    def _onContrastSliderChanged(self, val:int, name:str):
        """Respond to either the min or max contrast slider.
        
        Args:
            val: new value
            name: Name of slider, in ('min', 'max')
        """
        logger.info(f'{name} {val}')
        if name == 'min':
            self._minContrast = val
            self.minContrastSpinBox.setValue(val)
        elif name == 'max':
            self._maxContrast = val
            self.maxContrastSpinBox.setValue(val)
        self._replot()

    def getContrastEnhance(self, theMin=None, theMax=None):
        """Get contrast enhanced image.
        """
        _tifData = self.tifData

        logger.info(f'{_tifData.shape} {_tifData.dtype} shape:{_tifData.shape} max:{np.max(_tifData)}')
        
        bitDepth = 16
        
        if theMin is None:
            theMin = self._minContrast
        if theMax is None:
            theMax = self._maxContrast
        
        lut = np.arange(2**bitDepth-1, dtype='uint8')
        lut = self._getContrastedImage(lut, theMin, theMax) # get a copy of the image
        logger.info(f'  lut: {type(lut)} {lut.dtype} shape:{lut.shape} max:{np.max(lut)}')
        theRet = np.take(lut, _tifData)
        return theRet

    def _getContrastedImage(self, image, display_min, display_max): # copied from Bi Rico
        # Here I set copy=True in order to ensure the original image is not
        # modified. If you don't mind modifying the original image, you can
        # set copy=False or skip this step.
        bitDepth = 8
        
        image = np.array(image, dtype=np.uint8, copy=True)
        image.clip(display_min, display_max, out=image)
        image -= display_min
        np.floor_divide(image, (display_max - display_min + 1) / (2**bitDepth), out=image, casting='unsafe')
        #np.floor_divide(image, (display_max - display_min + 1) / 256,
        #                out=image, casting='unsafe')
        #return image.astype(np.uint8)
        return image

    def _replot(self, startSec=None, stopSec=None):
        logger.info('')

        self.kymographPlot.clear()
        self.kymographPlot.show()

        myTif = self.getContrastEnhance()
        
        logger.info(f'  startSec:{startSec} stopSec:{stopSec} myTif.shape:{myTif.shape}')  # like (519, 10000)
        
        #self.myImageItem = pg.ImageItem(myTif, axisOrder='row-major')
        #  TODO: set height to micro-meters
        axisOrder='row-major'
        
        # todo: get from tifHeader
        umLength = self.numPntsInLine * self.umPerPixel
        recordingDurSec = self.numLineScans * self.secondsPerLine
        rect=[0,0, recordingDurSec, umLength]  # x, y, w, h
        
        if self.myImageItem is None:
            # first time build
            self.myImageItem : pg.imageItem = kymographImage(myTif, axisOrder=axisOrder,
                            rect=rect)
            # redirect hover to self (to display intensity
            self.myImageItem.hoverEvent = self.hoverEvent
        else:
            # second time update
            myTif = self.getContrastEnhance()
            self.myImageItem.setImage(myTif, axisOrder=axisOrder,
                            rect=rect)

        colorKey = 'green'
        _lut = self._colorLut[colorKey]
        self.myImageItem.setLookupTable(_lut, update=True)

        self.kymographPlot.addItem(self.myImageItem)
        
        padding = 0
        if startSec is not None and stopSec is not None:
            self.kymographPlot.setXRange(startSec, stopSec, padding=padding)  # row major is different

        # re-add the vertical line
        self.kymographPlot.addItem(self._sliceLine)

        #
        # plot of diameter detection
        self._leftFitScatter = pg.ScatterPlotItem(
                                size=3, brush=pg.mkBrush(50, 255, 50, 120))
        _xFake = []  # self.sweepX
        _yFake = []  # [200 for x in self.sweepX]
        self._leftFitScatter.setData(_xFake, _yFake)
        self.kymographPlot.addItem(self._leftFitScatter)
            
        self._rightFitScatter = pg.ScatterPlotItem(
                                size=3, brush=pg.mkBrush(255, 50, 50, 120))
        _xFake = []  # self.sweepX
        _yFake = []  # [350 for x in self.sweepX]
        self._rightFitScatter.setData(_xFake, _yFake)
        self.kymographPlot.addItem(self._rightFitScatter)

        #
        # color bar with contrast !!!
        if myTif.dtype == np.dtype('uint8'):
            bitDepth = 8
        elif myTif.dtype == np.dtype('uint16'):
            bitDepth = 16
        else:
            bitDepth = 16
            logger.error(f'Did not recognize tif dtype: {myTif.dtype}')

        cm = pg.colormap.get('Greens_r', source='matplotlib') # prepare a linear color map
        #values = (0, 2**bitDepth)
        #values = (0, maxTif)
        values = (0, 2**12)
        limits = (0, 2**12)
        #logger.info(f'color bar bit depth is {bitDepth} with values in {values}')
        doColorBar = False
        if doColorBar:
            if self.myColorBarItem == None:
                self.myColorBarItem = pg.ColorBarItem( values=values, limits=limits,
                                                interactive=True,
                                                label='', cmap=cm, orientation='horizontal' )
            # Have ColorBarItem control colors of img and appear in 'plot':
            self.myColorBarItem.setImageItem( self.myImageItem, insert_in=self.kymographPlot )
            self.myColorBarItem.setLevels(values=values)

        doRectRoi = False
        kymographRect = self.getKymographRect()
        if doRectRoi and kymographRect is not None:
            # TODO: I guess we always have a rect, o.w. this would be a runtime error
            xRoiPos = kymographRect[0]
            yRoiPos = kymographRect[3]
            top = kymographRect[1]
            right = kymographRect[2]
            bottom = kymographRect[3]
            widthRoi = right - xRoiPos + 1
            #heightRoi = bottom - yRoiPos + 1
            heightRoi = top - yRoiPos + 1

            # TODO: get this out of replot, recreating the ROI is causing runtime error
            # update the rect roi
            pos = (xRoiPos,yRoiPos)
            size = (widthRoi,heightRoi)
            if self.myLineRoi is None:
                movable = False
                self.myLineRoi = pg.ROI(pos=pos, size=size,
                                        parent=self.myImageItem,
                                        movable=movable)
                #self.myLineRoi.addScaleHandle((0,0), (1,1), name='topleft')  # at origin
                self.myLineRoi.addScaleHandle((0.5,0), (0.5,1), name='top center')  # top center
                self.myLineRoi.addScaleHandle((0.5,1), (0.5,0), name='bottom center')  # bottom center
                self.myLineRoi.addScaleHandle((0,0.5), (1,0.5), name='left center')  # left center
                self.myLineRoi.addScaleHandle((1,0.5), (0,0.5), name='right center')  # right center
                #self.myLineRoi.addScaleHandle((1,1), (0,0), name='bottomright')  # bottom right
                self.myLineRoi.sigRegionChangeFinished.connect(self.kymographChanged)
            else:
                self.myLineRoi.setPos(pos, finish=False)
                self.myLineRoi.setSize(size, finish=False)

            self._updateRoiMinMax(kymographRect)

        #
        # background kymograph ROI
        backgroundRect = self.getKymographBackgroundRect()  # keep this in the backend
        if backgroundRect is not None:
            xRoiPos = backgroundRect[0]
            yRoiPos = backgroundRect[3]
            top = backgroundRect[1]
            right = backgroundRect[2]
            bottom = backgroundRect[3]
            widthRoi = right - xRoiPos + 1
            #heightRoi = bottom - yRoiPos + 1
            heightRoi = top - yRoiPos + 1

            pos = (xRoiPos,yRoiPos)
            size = (widthRoi,heightRoi)

            self._updateBackgroundRoiMinMax(backgroundRect)

        if 0:
            if self.myLineRoiBackground is None:
                # TODO: get this out of replot, recreating the ROI is causing runtime error
                self.myLineRoiBackground = pg.ROI(pos=pos, size=size, parent=self.myImageItem)
            else:
                self.myLineRoiBackground.setPos(pos, finish=False)
                self.myLineRoiBackground.setSize(size, finish=False)
        
        # update min/max labels
        # TODO: only set this once on switch file
        myTifOrig = self.tifData
        minTif = np.nanmin(myTifOrig)
        maxTif = np.nanmax(myTifOrig)
        #print(type(dtype), dtype)  # <class 'numpy.dtype[uint16]'> uint16
        self.tifMinLabel.setText(f'Int Min:{minTif}')
        self.tifMaxLabel.setText(f'Int Max:{maxTif}')

        # update min/max displayed to user
        # self._updateRoiMinMax(kymographRect)
        # self._updateBackgroundRoiMinMax(backgroundRect)

    def getKymographImageRect(self):
        umLength = self.numPntsInLine * self.umPerPixel
        recordingDurSec = self.numLineScans * self.secondsPerLine
        _rect = [0, 0, recordingDurSec, umLength]  # x, y, w, h
        return _rect

    def getKymographRect(self):
        """Get a full ractangle enclosing the kymograph.
        
        Args:
            getWidthHeight: If False (default) then return [l,t,r,b] otherwise return [x,y,w,h]
        """
        _rect = [0, self.numPntsInLine, self.numLineScans, 0]  # l, t, r, b
        return _rect

    def getKymographBackgroundRect(Self):
        return None
        
    def updateLeftRightFit(self, yLeft, yRight, visible=True):
        """
        
        """
    
        self._leftFitScatter.setVisible(visible)
        self._rightFitScatter.setVisible(visible)

        if visible:
            x = self.sweepX
            #TODO: check that len(y) == len(x)
            self._leftFitScatter.setData(x, yLeft)
            self._rightFitScatter.setData(x, yRight)
    
    def _updateBackgroundRoiMinMax(self, backgroundRect=None):
        """
        update background roi

        TODO: Add getBackGroundStats()

        """
        logger.warning(f'Need to add interface for user to adjust background roi')
        return
        
        if backgroundRect is None:
            backgroundRect = self.getKymographBackgroundRect()

        left = backgroundRect[0]
        top = backgroundRect[1]
        right = backgroundRect[2]
        bottom = backgroundRect[3]

        myTif = self.tifData
        tifClip = myTif[bottom:top, left:right]

        roiMin = np.nanmin(tifClip)
        roiMax = np.nanmax(tifClip)

        # self.backgroundRoiMinLabel.setText(f'Background Min:{roiMin}')
        # self.backgroundRoiMaxLabel.setText(f'Background Max:{roiMax}')

    def _updateRoiMinMax(self, theRect):
        left = theRect[0]
        top = theRect[1]
        right = theRect[2]
        bottom = theRect[3]

        logger.info(f'left:{left} top:{top} right:{right} bottom:{bottom}')
        
        myTif = self.tifData
        tifClip = myTif[bottom:top, left:right]

        roiMin = np.nanmin(tifClip)
        roiMax = np.nanmax(tifClip)

        self.roiMinLabel.setText(f'ROI Min:{roiMin}')
        self.roiMaxLabel.setText(f'ROI Max:{roiMax}')

    def kymographChanged(self, event):
        """
        User finished dragging the ROI

        Args:
            event (pyqtgraph.graphicsItems.ROI.ROI)
        """

        _kymographRect = self.getKymographRect()  # (l, t, r, b)

        logger.info(f'_kymographRect:{_kymographRect}')

        left = _kymographRect[0]
        top = _kymographRect[1]
        right = _kymographRect[2]
        bottom = _kymographRect[3]
        
        handles = event.getSceneHandlePositions()
        for _idx, handle in enumerate(handles):
            # logger.info(f'{_idx} handle: {handle}')
            # logger.info(f'  handle[0]:{handle[0]}')
            if handle[0] is not None:
                #imagePos = self.myImageItem.mapFromScene(handle[1])
                imagePos = self.myImageItem.mapFromScene(handle[1])
                x = imagePos.x()
                y = imagePos.y()
                if handle[0] == 'top center':
                    top = y
                elif handle[0] == 'bottom center':
                    bottom = y
                elif handle[0] == 'left center':
                    left = x
                elif handle[0] == 'right center':
                    right = x
                else:
                    logger.error(f'did not understand handle[0] name "{handle[0]}"')
        #
        left = int(left)
        top = int(top)
        right = int(right)
        bottom = int(bottom)

        if left<0:
            left = 0
        if bottom<0:
            bottom = 0

        # force left and right
        # _kymographRect = self.getKymographRect()  # (l, t, r, b)
        # left = 0
        # right = _kymographRect[2]

        logger.info(f'  left:{left} top:{top} right:{right} bottom:{bottom}')

        #  cludge
        if bottom > top:
            logger.warning(f'fixing bad top/bottom with top:{top} bottom{bottom}')
            tmp = top
            top = bottom
            bottom = tmp

        theRect = [left, top, right, bottom]

        self._updateRoiMinMax(theRect)

        # TODO: detection widget needs a slot to (i) analyze and then replot
        #self.ba._updateTifRoi(theRect)
        #self._replot(startSec=None, stopSec=None, userUpdate=True)
        #self.signalDetect.emit(self.ba)  # underlying _abf has new rect
        
        # feb 2023, put back in?
        # self.ba.fileLoader._updateTifRoi(theRect)
        
        self.signalKymographRoiChanged.emit(theRect)  # underlying _abf has new rect

    def hoverEvent(self, event):
        if event.isExit():
            return

        xPos = event.pos().x()
        yPos = event.pos().y()

        xPos = int(xPos)
        yPos = int(yPos)

        try:
            intensity = self.tifData[yPos, xPos]  # flipped
        except (IndexError) as e:
            pass
        else:
            self.tifCursorLabel.setText(f'Intensity:{intensity}')
            self.tifCursorLabel.update()

    def old_slot_setVelPlot(self, x, y):
        """Set the velocity"""
        self._velPlotItem.setData(x=x, y=y) # start empty

    def showLineSlider(self, visible):
        """Toggle line slider and vertical line (on image) on/off.
        """
        self._sliceLine.setVisible(visible)

def run():
    app = QtWidgets.QApplication(sys.argv)

    if 1:
        path = '/media/cudmore/data/rabbit-ca-transient/jan-12-2022/Control/220110n_0003.tif.frames/220110n_0003.tif'
        #path = '/Users/cudmore/data/rosie/test-data/filter median 1 C2-0-255 Cell 2 CTRL  2_5_21 female wt old.tif'
        

        import tifffile
        tifData = tifffile.imread(path)
        tifData = np.rot90(tifData)
        kw = kymographWidget(tifData, secondsPerLine=0.001, umPerPixel=0.15)
        kw.show()

        import analyzeflow
        path = '/home/cudmore/Sites/declan-flow-analysis-shared/data/20221202/Capillary4.tif'
        flowFile = analyzeflow.kymFlowFile(path)
        tifData = flowFile.tifData
        tifData = np.rot90(tifData)
        secondsPerLine = flowFile.delt()
        umPerPixel = flowFile.delx()
        filename = flowFile.getFileName()
        kw.slot_switchFile(tifData, secondsPerLine=secondsPerLine, umPerPixel=umPerPixel, filename=filename)

        removeZero = True
        removeOutliers = True
        medianFilter = 5
        absValue = False
        x = flowFile.getTime()
        y = flowFile.getVelocity(removeZero=removeZero, removeOutliers=removeOutliers, medianFilter=medianFilter, absValue=absValue)
        
        #kw.slot_setVelPlot(x, y)

    # test dialog
    if 0:
        mcd = myCustomDialog()
        if mcd.exec():
            scaleDict = mcd.getResults()
            print(scaleDict)
        else:
            print('user did not hit "ok"')

    sys.exit(app.exec_())

if __name__ == '__main__':
    run()