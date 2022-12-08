from datetime import datetime
import os
import pathlib
import platform
import sys

from qtpy import QtCore, QtWidgets, QtGui
import qdarkstyle

from analyzeflow import get_logger
logger = get_logger(__name__)

class FlowWindow(QtWidgets.QMainWindow):
    def __init__(self, path=None, parent=None):
        super().__init__(parent)

def main():
    logger.info(f'Starting sanpy_app.py in __main__()')

    date_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f'    {date_time_str}')

    logger.info(f'    Python version is {platform.python_version()}')
    #logger.info(f'    PyQt version is {QtCore.QT_VERSION_STR}')
    logger.info(f'    PyQt version is {QtCore.__version__}')

    # bundle_dir = sanpy._util.getBundledDir()
    # logger.info(f'    bundle_dir is "{bundle_dir}"')

    import analyzeflow
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

    w = FlowWindow()

    w.show()

    # to debug the meber function openLog()
    #w.openLog()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()