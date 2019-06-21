tifPath = 'exampleData/drew_synthetic.tif';
% image parameters
delx = 1.0e-3;
delt = 2.05e-3;
% chhatbar parameters
hi = 100;
lineskip = 25;

% x range (pixels) along line to analyze
xMin = 1;
xMax = 60;

showOutput=1;
saveimg = 0;
[time,velocity,angle,utheta,uvar] = hybridvel(tifPath,showOutput,saveimg,delx,delt,hi,lineskip,xMin,xMax);

