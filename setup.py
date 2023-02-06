from setuptools import setup, find_packages

#exec (open('bimpy/version.py').read())

setup(
    name='analyzeflow',
    version='0.0.2',  # Feb 06 2023
    description='Analyze blood flow from a kymograph line scan.',
    url='http://github.com/cudmore/Analyze-Flow',
    author='Robert H Cudmore',
    author_email='rhcudmore@ucdavis.edu',
    license='GNU GPLv3',
	packages=find_packages(include=['analyzeflow', 'analyzeflow.interface', 'analyzeflow.*']),
    #packages=['sanpy', 'sanpy.userAnalysis'],
	install_requires=[
        'numpy',
        'pandas',
        'tifffile',
        'matplotlib',
		'seaborn',
        'plotly',
        'kaleido',  # to save/export from plotly
        #'scipy',
		#'mplcursors',
		#'requests', #  to load from the cloud (for now github)
		#'tables',  # this fails on arm64, neeed 'conda install pytables'
        'scikit-image',
        #'h5py',
        #'pyqtgraph',
        #'PyQt5',
        #'qdarkstyle',
        'jupyter',
        'mplcursors',
    ],
    # use pip install .[gui]
    # on Big Sur use pip install .\[gui\]
	extras_require={
        'gui': [
			'pyqtgraph',
			'PyQt5',
			'qdarkstyle',
		],
        'dev': [
			'jupyter',
            'mkdocs',
			'mkdocs-material',
			'mkdocs-jupyter',
            'mkdocstrings',
            'tornado', # needed for pyinstaller
            'pyinstaller',
            'ipython',
		],
    },
    entry_points={
        'console_scripts': [
            'analyzeflow=analyzeflow.interface.analyzeflow_app:main',
        ]
    },
)
