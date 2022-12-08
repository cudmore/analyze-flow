## This repository has code to analyze blood flow from line-scan kymographs. It is split into two parts, (i) Python and (ii) Matlab.

What follows is instructions for the Python version. For  the matlab version, see [readme-matlab.md](readme-matlab.md).

## Install

We will install a local copy of the code in a conda environment named `flow-env`.

1) Clone the repository

```
git clone git@github.com:cudmore/analyze-flow.git
```

2) Create a conda environment

```
conda create -y -n flow-env python=3.9
```

3) Activate conda environment

```
conda activate flow-env
```

4) Install the `analyzeflow` package locally

```
pip install -e .
```

## Browse raw data and analysis in a Jupyter notebook

```
jupyter notebook
```

**Note:** make sure the `flow-env` conda environment is activate with `conda activate flow-env`.

## Perform analysis on raw tif kymographs

From a Python prompt like ipython or in a Jupyter notebook.

Perform analysis on one tif file.

```python
from analyzeflow import kymFlowFile

tifPath = '/Users/cudmore/Dropbox/data/declan//20221102/Capillary5_0001.tif'

kff = kymFlowFile(tifPath)

# do actual kym radon analysis
kff.analyzeFlowWithRadon()

# save result to csv
kff.saveAnalysis()
```

Perform analysis on a folder of tif files

```python
from analyzeflow import batchAnalyzeFolder

folderPath = '/Users/cudmore/Dropbox/data/declan/20221206'

batchAnalyzeFolder(folderPath)

```