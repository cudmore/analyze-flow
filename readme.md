
## Blood flow analysis from line scans

This code is designed to analyze repetitive line scans to extract blood flow. It proceeds in two steps.

 1. In Matlab, extract flow from raw .tif line scan files and save velocity to .txt files.
 2. In Python, analyze resultant velocity measurements in .txt files across any number of analyzed files.

## Algorithms

Using algorithms and code from these two references:

 - [Kim TN, Goodwill PW, Chen Y, Conolly SM, Schaffer CB, Liepmann D, Wang RA (2012) Line-Scanning Particle Image Velocimetry: An Optical Approach for Quantifying a Wide Range of Blood Flow Speeds in Live Animals. PLoS One 7:e38590.][kim-et-al-2012]
 - [Chhatbar PY, Kara P (2013) Improved blood velocity measurements with a hybrid image filtering and iterative Radon transform algorithm. Front Neurosci 7:106.][chhatbar-and-kara-2013]

[kim-et-al-2012]: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0038590
[chhatbar-and-kara-2013]: https://www.frontiersin.org/articles/10.3389/fnins.2013.00106/full

## Requirements

 1. Matlab 2016b. May work with other versions as well.

   - The Kim et al algorithm requires the xxx and yyy toolboxes.
   - The Chhatbar and Kara algoithm requires the zzz toolbox.

 2. Source line scan files need to be .tif

 3. We need to read two acquisition parameters from each .tif file, the x voxel size along a line scan (delx, um/pixel) and the speed of each line scan (delt, ms/scan). The matlab code assumes you have done this with the Fiji script 'bFolder2MapManager.v0.2_.py'.

## Running the analysis

Before running matlab code, make sure the output .txt files of Fiji script are all contained in a folder named **oir_headers** inside the folder with the raw .tif files.

At the Matlab prompt, you need to `cd` into the folder with this code, something like

```
cd /Users/cudmore/dropbox/flowanalysis
```

### AnalyzeFlow Matlab script

Run the `AnalyzeFlow` script from the Matlab command prompt to analyze one .tif file.

 1. Prompt for a tif file.
 2. Displays the Tiff and asks user to click start and then stop of analysis along the scanned line (X1, X2).
 3. Asks if it is an Artery (Vein) or capillary. This choice will modify one parameter for the Kim algorithm. Arteries/Veins are fast (shiftamt=1), while capillaries are slow (shiftamt=5).
 4. Perform both Kim and Chhatbar analysis.
 5. Save all analysis into .txt files.

### AnalyzeFlowFolder Matlab script

Run the `AnalyzeFlowFolder` script from the Matlab command prompt to analyze all .tif files in a selected folder.

 1. Prompts for a folder of .tif files
 2. Calls **AnalyzeFlow** for each .tif in the folder

### AnalyzeFlow Python Jupter notebook

Open the `AnalyzeFlow.ipynb` in Python's Jupyter to analyze entire folders of saved velocty .txt files.


## AnalyzeFlow Interface

 1. Run `AnalyzeFlow` at Matlab command prompt
 2. Select a .tif image to analyze.
 3. `AnalyzeFlow` will display the image. On the left is the full image, in the center is the first 1000 lines, and on the right are the last 1000 lines. Use the mouse pointer and cursors to click the start and then stop points along the x-axis. The position along the y-axis is ignored.

 <IMG SRC="img/analyze-flow-image.png" width=600>
 4. Select either 'capillary' or 'artery/vein'. This will set the `shiftamt` parameter for the Kim algorithm. In general arteries have fast flow and capillaries have slow flow.
 
 <IMG SRC="img/analyze-flow-artery-capillary.png" width=300>

 5. The flow analysis is saved as a `_combined.txt` file in the same folder as the original .tif file.

## AnalyzeFlow output .txt files

The save .txt file looks like the example below. Note, we are only showing 7 velocity measurements from both the Kim and Chhatbar algorithms, there will actually be many more.

These files are easy to load and parse in a number of analysis programs. See the [python/](python]) folder for examples.

| filepath                                                             | file               | acqDate    | acqTime            | analysisDate | analysisTime | pntsPerLine | numLines | delx     | delt     | x1 | x2 | algorithm | k_numavgs | k_skipamt | k_shiftamt | c_hi | c_lineskip | time        | velocity  | 
|----------------------------------------------------------------------|--------------------|------------|--------------------|--------------|--------------|-------------|----------|----------|----------|----|----|-----------|-----------|-----------|------------|------|------------|-------------|-----------| 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 38.250000   | -0.672911 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 76.500000   | -0.637624 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 114.750000  | -0.601160 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 153.000000  | -0.579518 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 191.250000  | -0.583120 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 229.500000  | -0.581488 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | kim       | 100       | 25        | 1          | NaN  | NaN        | 267.750000  | -0.592656 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 1799.280000 | -0.552622 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 1837.530000 | -0.553482 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 1875.780000 | -0.531908 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 1914.030000 | -0.547489 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 1952.280000 | -0.572237 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 1990.530000 | -0.617104 | 
| /Users/cudmore/box/data/nathan/20190613/Converted/20190613__0020.tif | 20190613__0020.tif | 2019-06-13 | 13:12:57.221-07:00 | 20190619     | 12:27:55     | 42          | 10000    | 0.994369 | 1.530000 | 6  | 37 | chhatbar  | NaN       | NaN       | NaN        | 100  | 25         | 2028.780000 | -0.618527 | 

## Assumptions and important parameters

This analysis assumes that both the scan speed of each line (delt) and the voxel size of each pixel (delx) is known. We use Fiji scripts to read native scope file formats, in particular Olympus OIR files, to extract this information into a .txt file where Matlab cen then read it. The code can be modified to do otherwise.

The Kim algorithm has parameters and **shiftamt** has to be set for slow (capillaries) and fast (arteries and veins)

```
numavgs = 100;
skipamt = 25;
shiftamt = 5; % capillary (slow)
%shiftamt = 1; % artery (fast)
```

The Chhatbar algorithm has parameters but everything seems to work with default parameters.

```
hi = 100;
lineskip = 25;
```

## exampleData

 - Example tif files

## To Do

 - Remove outliers. Do this by apending a 'reject' column on load. Then, set 'reject =True' if > 2*SD. When plotting, don't plot reject. When taking mean, don't use reject.
 - Update matlab code with interface to select art/vein or cap (sets one parameter)
 - Get b/w kim and chhatbar stats working
 - Get start/stop stats for trial working (both t-test and % change)
 - Figure out how to get more info in analysis (trial grouping, flag a file as bad, ...)
 
 - Get stats working. There seem to be some bad values? Maybe the nan I set when removing outliers (which will be removed in future in preference for 'reject' column.
 
 ```
     /usr/local/lib/python3.7/site-packages/scipy/stats/morestats.py:2781: RuntimeWarning:

    invalid value encountered in greater

    /usr/local/lib/python3.7/site-packages/scipy/stats/morestats.py:2782: RuntimeWarning:

    invalid value encountered in less

    /usr/local/lib/python3.7/site-packages/scipy/stats/morestats.py:2778: UserWarning:

    Warning: sample size too small for normal approximation.
```

 - Need to bypass reading Tiff header info from bImPy (too hard to install)
  
  - 1) revamp Fiji code to read stack headers
  - 2) in Matlab make a 'cheatsheet.csv' for each folder, each row is a .tif file with (delx, delt, date, time, etc)
  
[bImPy]: https://github.com/cudmore/bImPy
