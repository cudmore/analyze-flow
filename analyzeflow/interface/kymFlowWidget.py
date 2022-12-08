import os

import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import ipywidgets as widgets
from IPython.display import display, clear_output

import analyzeflow

"""A Jupyter ipythonwidget to display kymograph/analysis for tif files in a folder.
"""

def saveAnalysisImages(folderPath : str):
    """Plot all flow analysis and save figures to folder 'python-figures'.
    
    Use this to just make an overview of all python analysis
    """
    print('saveAnalysisImages:', folderPath)
    
    removeOutliers = True
    medianFilter = 5

    # make output img folder
    imgFolder = os.path.join(folderPath, 'python-figures')
    if not os.path.isdir(imgFolder):
        os.mkdir(imgFolder)
    files = os.listdir(folderPath)
    files = sorted(files)

    for file in files:
        if not file.endswith('.tif'):
            continue
        oneFilePath = os.path.join(folderPath, file)

        print('  generating figure for file', file)
        fig = plotFlowAnalysis_v3(oneFilePath,
                    removeOutliers=removeOutliers,
                    medianFilter=medianFilter)

        saveFile = os.path.splitext(file)[0] + '.pdf'
        savePath = os.path.join(imgFolder, saveFile)
        print('    saving to', savePath)
        fig.write_image(savePath)
    
    # export table
    df = analyzeflow.kymFlowUtil.makeSummaryTable_v3(folderPath)
    summaryFile = os.path.split(folderPath)[1]
    summaryFile = summaryFile + '_summary.csv'
    summaryPath = os.path.join(imgFolder, summaryFile)
    print('  saving summary table to:', summaryPath)
    df.to_csv(summaryPath)

    print('done exporting figure to:', imgFolder)

def plotFlowAnalysis_Update(fig, tifPath):
    # load tif data
    tifData = tifffile.imread(tifPath)
    tifData = np.rot90(tifData)
    print('plotFlowAnalysis_Update() loaded tifData:', tifData.shape)  # (38, 30000)
    
    # load corresponding csv
    analysisFolderPath = _getAnalysisPath(tifPath)
    baseFile, _ext = os.path.splitext(tifPath)
    csvFile = baseFile + '_combined.csv'
    csvPath = os.path.join(analysisFolderPath, csvFile)
    df = pd.read_csv(csvPath)

    delt = df.loc[0, 'delt']
    #print('delt:', delt)
    _numLines = tifData.shape[1]
    _numPnts = tifData.shape[0]

    _kymFlow = kymFlow(tifPath)
    tifData = _kymFlow.getTif()
    _numLines = _kymFlow.numLines()
    _numPnts = kymFlow.pntsPerLine()
    delt = _kymFlow.delt()

    figImage = px.imshow(tifData,
                x=np.arange(_numLines)*delt,
                y=np.arange(_numPnts))
    #fig.data[0]: <class 'plotly.graph_objs._heatmap.Heatmap'>
    # figImage.data[0] is plotly.graph_objs._heatmap.Heatmap
    
    # 'tuple' object does not support item assignment
    print('fig.data[0]:', type(fig.data[0]))
    print('figImage.data[0]:', type(figImage.data[0]))
    #fig.data[0] = figImage.data[0]

    # oldImage = fig.data[0]
    # oldImage = figImage.data[0]

    #fig.data[0].z = figImage.data[0].z
    # see: https://community.plotly.com/t/how-to-update-trace-of-imshow/35665
    fig['data'][0].update(z=figImage.data[0].z)

    fig.layout.title.text = 'This is a new title'

def plotFlowAnalysis_v3(tifPath, removeOutliers=True, medianFilter=0):
    """
    Load tif
    Load csv
    
    Plot kym, vel drew, vel chhatbar

    Args:
        medianFiler: if 0 then none, otherwise must be odd
    """

    # construct a kymFlow from file and grab params for plot
    _kymFlow = analyzeflow.kymFlowFile(tifPath)
    tifData = _kymFlow.getTifCopy(doRotate=True)
    filename = _kymFlow.getFileName()
    _numLines = _kymFlow.numLines()
    _numPnts = _kymFlow.pntsPerLine()
    delt = _kymFlow.delt()
    timeDrew = _kymFlow.getTime()
    velocityDrew = _kymFlow.getVelocity(removeOutliers=removeOutliers, medianFilter=medianFilter)
    
    fig = make_subplots(rows=3, cols=1,
                    subplot_titles=(filename,  'Drew Python', ''),
                    shared_xaxes=True,
                    shared_yaxes=False,
                    vertical_spacing=0.08,
                    specs=[[{"type": "heatmap"}],
                        [{"type": "scatter"}],
                        [{"type": "table"}],
                        ]
                    )
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(showlegend=False)
    fig['layout'].update(height=700, width=1000)

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

class kymFlowWidget():
    def __init__(self, folderPath):

        self._folderPath = folderPath

        # make a list of tif files
        self._files = os.listdir(folderPath)
        self._files = sorted(self._files)
        self._fileList = []
        for file in self._files:
            if not file.endswith('.tif'):
                continue
            self._fileList.append(file)

        self._removeOutliers = True
        self._medianFilter = 5
            
        self._folderPathLabel = widgets.Label(self._folderPath)
        
        self._myDropdown = widgets.Dropdown(
            options=self._fileList,
            #value='2',
            description='File:',
            disabled=False,
        )
        self._myDropdown.observe(self.dropdown_eventhandler, names='value')

        self._myRemoveOutliers = widgets.Checkbox(
            value=True,
            description='Remove Outliers',
            disabled=False
        )
        self._myRemoveOutliers.observe(self.removeOutliers_eventhandler, names='value')


        # plot the first file
        self._plottedFileName = None
        
        tifFileName = self._fileList[0]
        self._replot(tifFileName)
        
    def dropdown_eventhandler(self, change):
        """
        change: traitlets.utils.bunch.Bunch
        """
        
        clear_output(wait=True)

        # replot
        tifFileName = change.new
        self._replot(tifFileName)

    def removeOutliers_eventhandler(self, change):
        self._removeOutliers = change.new
        self._replot()

    def _replot(self, tifFileName=None):
        if tifFileName is not None:
            self._plottedFileName = tifFileName
        
        tifFileName = self._plottedFileName

        clear_output(wait=True)

        tifPath = os.path.join(self._folderPath, tifFileName)

        hbox = widgets.HBox([self._folderPathLabel,
                                self._myDropdown,
                                self._myRemoveOutliers])
        display(hbox)

        # display(self._myDropdown)
        # display(self._myRemoveOutliers)

        fig = plotFlowAnalysis_v3(tifPath,
                        removeOutliers=self._removeOutliers,
                        medianFilter=self._medianFilter)
        figWidget = go.FigureWidget(fig)
        figWidget.show()

if __name__ == '__main__':
    folderPath = '/Users/cudmore/Dropbox/data/declan/20221102'
    saveAnalysisImages(folderPath)