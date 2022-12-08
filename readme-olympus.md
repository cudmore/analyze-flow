## This is a recipe to analyze blood flow kymographs acquired on the Olympus 2-P scope.

1)

Using the Olympus software, export each kymograph oir to a tif file.

This will result in a .tif file and a .txt file. If your original image is kymograph6.oir, this will export something like `kymograph6_0001.tif` and `kymograph6_0001.txt`.

2)

In Matlab, run `AnalyzeFlow` and select your exported kymograph .tif file (e.g. kymograph6_0001.tif)

Keep an eye on the Matlab command prompt. If there are any errors, pay attention to them and email rhcudmore@ucdavis.edu with the full output in the Matlab command prompt.

IF all works as expected, this will generate a csv text file with the flow for each line scan for both the Drew and Chhatbar algorithms.

File is named `Capillary6_0001_combined.csv`


## Try the official Olympus oir Fiji plugin

It would be noce to be able to open kymographs directly from the original oir file, skipping the export to tif/txt step.

Botom line, **it does not work**. It loads the reference image the same way dragging/dropping an oir file onto Fiji does (using Bio-Formats) and the same way as opening the oir file in Python aics-io.

See: https://imagej.net/formats/olympus

Download link is broken, needs https. On that page right-click to download.



