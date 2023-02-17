

## 20230210
	Going through Declan notes in summary xls file

	TODO: plot image int range to see if it predicts bad velocity?
	
## 20230125

### TODO (speaking with Declan)

	1) remove vel near 0

	2) add pos/neg flag to summary

	3) check that vel does not start as both pos and neg

	4) add new columns to summary
		- analysisDate
		- analysisTime
		- analysisVersion

	5) after radon analysis save a single row csv (or json) with summary like:
		basically all columns we put into the summary csv (across lots of kymographs)

### Raw data has a particular structure (REQUIRED)

Inside the data folder, we have all the `date` folders with the yyyymmdd format. Each date folder has raw tif/txt files (not shown).

```
../declan-flow-analysis-shared/data
├── 20221102
├── 20221202
├── 20221206
├── 20221216
├── 20230105
├── 20230110
├── 20230112
├── 20230117
├── 20230119
├── 20230124
└── 20230125
```

### Updates

- updated the kymograph browser in jupyter notebook to:
	- show a popup of date folder
	- added 'Abs Vel' checkbox to show raw or abs() values of velocity
	- added 'Remove Zero' checkbox to show/hide 0 velocity

- in the summary csv we now have:

	signMeanVel: +1 for positive velocity, -1 for negative velocity
	posNegVel: 0 is we only see one direction, 1 if we see both (after remove outliers)
 
- I checked for flow reversals in each kymograph be looking for both positive and negative velocity. We do not see this after we remove outliers. Before we remove outliers, we do see it but it is just one-off single line scan 'pops' that generally get removed in the remove outliers.

- We can now optionally remove 0's from velocity. Zero velocity usually occurs when (i) the region of the image is artifically dark and (ii) the flow actually stops. This is not as common as (i)


- We now set both tan() of 1e6 and tan() of 0 to np.nan. Previoulsy we only set tan() of 1e6 to np.nan. This was introducing false 0 velocity. Velocity can be 0 when there is no bright/dark band in the image

- Expanded the file we save after velocity detection with radon. Added columns that strip outliers and 0's
	Each tif has a csv with one row per line scan. Columns are:
		time:
		velocity:
		cleanVelocity
		absVelocity
		noZeroVelocity

### Fixed plotly bug when plotting isolated values surrounded by nan

Fix is to just use plotly==5.12.0. Previously we had plotly==5.11.0

see: https://github.com/plotly/plotly.py/issues/4026