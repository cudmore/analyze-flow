## Install

Cone the repository

```
git clone xxx
```

Create a conda environment

```
conda create -y -n flow-env python=3.9
```

Activate conda environment

```
conda activate flow-env
```

Install the `analyzeflow` package locally

```
pip install -e .
```

## Browse raw data and analysis in a Jupyter notebook

```
jupyter notebook
```

## Perform analysis

```
tifPath = '/Users/cudmore/Dropbox/data/declan//20221102/Capillary5_0001.tif'
kff = kymFlowFile(tifPath)

kff.analyzeFlowWithRadon()  # do actual kym radon analysis
kff.saveAnalysis()  # save result to csv
```
