tifPath = 'exampleData/drew_synthetic.tif';
% image parameters
delx = 1.0e-3;
delt = 2.05e-3;

% kim parameters
numavgs = 100;
skipamt = 25;
shiftamt = 5; % capillary (slow)
%shiftamt = 1; % artery (fast)

% x range (pixels) along line to analyze
xMin = 1;
xMax = 60;

showOutput=1;

[myTime,velocity] = bKim(tifPath, showOutput, delx, delt, numavgs, skipamt, shiftamt, xMin, xMax);
