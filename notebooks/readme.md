## Python Jupyter notebook to analyze blood flow velocity .txt files

### Running

Run this notebook from this folder with `jupyter notebook`.

### Create and activate a conda environment

```
conda create -y -n analyze-flow python=3.8 
conda activate analyze-flow
```

### Install Requirements

Python 3.7.x or greater

```
pip install tifffile
pip install jupyter
pip install pandas
pip install numpy
pip install plotly
pip install seaborn
```

To save/export images from plotly, the following is required

```
pip install -U kaleido
```

