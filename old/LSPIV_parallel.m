% LSPIV with parallel processing enabled.
%
% For additional information, please see corresponding manuscript:
%
% 'Line-Scanning Particle Image Velocimetry: an Optical Approach for
% Quantifying a Wide Range of Blood Flow Speeds in Live Animals'
% by Tyson N. Kim, Patrick W. Goodwill, Yeni Chen, Steven M. Conolly, Chris
% B. Schaffer, Dorian Liepmann, Rong A. Wang
% 
%
% abb 201904
% shiftamt: seems very important, for synthetic data, shiftamt=5 (capillary) or
% shiftamt=1 (artery) results in different velocities!!!!
% windowsize: just used to flag 'bad' points?
%
% made it so we create new plots on each run and do not recyle. This allows
% us to see output of multiple runs on same daya with different parameters

% abb, removed
% PWG 3/28/2012
%close all

numWorkers    = 12;  % number of workers on this machine.  
                     % depends on number of processors in your machine
                     % A safe starting point is typically 4,
                     % MATLAB supports up to 12 local workers in 
                     % R2011b.
                     %
                     % If you have trouble, you can access parpool
                     % directly: e.g. try typing "parpool 12" for 12
                     % workers.
numWorkers    = 6; % abb on my mac mini
numWorkers    = 4; % abb on my mac home
                     
% Parameters to improve fits
maxGaussWidth = 100;  % maximum width of peak during peak fitting

% Judge correctness of fit
numstd        = 3;  %num of stdard deviation from the mean before flagging
windowsize    = 2600; %in # scans, this w ill be converted to velocity points
                      %if one scan is 1/2600 s, then windowsize=2600 means
                      %a 1 second moving window.  Choose the window size
                      %according to experiment.

%%  settings
% Ask user for setting 
str = {'capillary', 'artery', 'user'};
[speedSetting,v] = listdlg('PromptString','Select a configuration',...
                'SelectionMode','single',...
                'ListString',str);
if v == 0; beep; disp('Cancelled'); return; end

if speedSetting == 1   % CAPILLARY SETTING
    numavgs       = 100;  %up to 100 (or more) for noisy or slow data
    skipamt       = 25;   %if it is 2, it skips every other point.  3 = skips 2/3rds of points, etc.
    shiftamt      = 5;
elseif speedSetting == 2   % ARTERY SETTING
    numavgs       = 100;  %up to 100 (or more) for noisy or slow data
    skipamt       = 25;   %if it is 2, it skips every other point.  3 = skips 2/3rds of points, etc.
    shiftamt      = 1;
elseif speedSetting == 3   % USER SETTING
    disp('settings are hard coded in the script, see script!');
    numavgs       = 100;  %up to 200 (or more) for troublesome data. However
                          %you will lose some of the info in the peaks and
                          %troughs
    skipamt       = 10;   %if it is 2, it skips every other point.  3 = skips 2/3rds of points, etc.
    shiftamt      = 1;
end

% abb, path to folder with this file
% cd /Users/cudmore/Dropbox/linescan/kim_et_al_2012

% abb, redirect uigetfile to a data folder for user selection
%myPath = '/Volumes/fourt0/Dropbox/data';
myPath = '';

%% Import the data from a multi-frame tif and make into a single array
%  The goal is a file format that is one single array,
%  so modify this section to accomodate your raw data format.
%
%  This particular file format assumes
disp('import raw data');
% abb updated to point to raw data path 'myPath'
%[fname,pathname]=uigetfile(myPath, '*.TIF','pick a linescan file');%loads file
[fname,pathname]=uigetfile(fullfile(myPath,'*.tif'),'pick a linescan file');%loads file
% abb, replaced 'break' with 'return'
if fname == 0; beep; disp('Cancelled'); return; end
imageLines = imimportTif([pathname fname])'; % abb, imimportTif() is a .m file !!!
%%
    
% abb
disp(['abb size(imageLines): ', num2str(size(imageLines))])

%% choose where in the image to process
% abb, added 'figure' to always display imagesc in new figure
figure
imagesc(imageLines(1:size(imageLines,2),:)) % imagesc is image 'scaled colors'
colormap('gray')

% abb
%title('Select the boundaries of the region of interest 1/2');
title('Click the left/min point along x-axis to start analysis');
[X1,Y1] = ginput(1);
line([X1 X1],[1 size(imageLines,2)]);

% abb
%title('Select the boundaries of the region of interest 2/2');
title('Click the right/max point along x-axis to start analysis');
[X2,Y2] = ginput(1);
line([X2 X2],[1 size(imageLines,2)]);
refresh
pause(.01);

startColumn   = round(min(X1, X2));      % Defines what part of the image we perform LSPIV on.
endColumn     = round(max(X1, X2));

disp(['abb analyzing line scan from pnt: ', num2str(startColumn), ' to pnt ', num2str(endColumn)])

%% startup parallel processing
% abb removed
%if parpool('size') == 0
% abb added
%if isempty(parpool)
if isempty(gcp('nocreate'))
    parpool('local',numWorkers)
else
    disp('parpool Already Detected');
end

tic

%% minus out background signal (PWG 6/4/2009)
disp('DC correction')
DCoffset = sum(imageLines,1) / size(imageLines,1);
imageLinesDC = imageLines - repmat(DCoffset,size(imageLines,1),1);

%% do LSPIV correlation
disp('LSPIV begin');

scene_fft  = fft(imageLinesDC(1:end-shiftamt,:),[],2);
test_img   = zeros(size(scene_fft));
test_img(:,startColumn:endColumn)   = imageLinesDC(shiftamt+1:end, startColumn:endColumn);
test_fft   = fft(test_img,[],2);
W      = 1./sqrt(abs(scene_fft)) ./ sqrt(abs(test_fft)); % phase only

LSPIVresultFFT      = scene_fft .* conj(test_fft) .* W; 
LSPIVresult         = ifft(LSPIVresultFFT,[],2);
disp('LSPIV complete');

toc

%% find shift amounts
disp('Find the peaks');
velocity = [];
maxpxlshift = round(size(imageLines,2)/2)-1;


index_vals = skipamt:skipamt:(size(LSPIVresult,1) - numavgs);
numpixels = size(LSPIVresult,2);
velocity  = nan(size(index_vals));
amps      = nan(size(index_vals));
sigmas    = nan(size(index_vals));
goodness  = nan(size(index_vals));

disp(['starting parfor loop for ', num2str(max(index_vals)), ' index_vals'])

%% iterate through
parfor index = 1:length(index_vals)
    
    % abb, changed from 100 to 400
    if mod(index_vals(index),400) == 0
        fprintf('   parfor line: %d\n',index_vals(index))
    end
    
    LSPIVresult_AVG   = fftshift(sum(LSPIVresult(index_vals(index):index_vals(index)+numavgs,:),1)) ...
                                      / max(sum(LSPIVresult(index_vals(index):index_vals(index)+numavgs,:),1));
    
    % find a good guess for the center
    c = zeros(1, numpixels);
    c(numpixels/2-maxpxlshift:numpixels/2+maxpxlshift) = ...
        LSPIVresult_AVG(numpixels/2-maxpxlshift:numpixels/2+maxpxlshift);
    [maxval, maxindex] = max(c);
    
    % fit a guassian to the xcorrelation to get a subpixel shift
    options = fitoptions('gauss1');
    options.Lower      = [0    numpixels/2-maxpxlshift   0            0];
    options.Upper      = [1e9  numpixels/2+maxpxlshift  maxGaussWidth 1];
    options.StartPoint = [1 maxindex 10 .1];
    [q,good] = fit((1:length(LSPIVresult_AVG))',LSPIVresult_AVG','a1*exp(-((x-b1)/c1)^2) + d1',options);
    
    %save the data
    if 1
        % abb, added '-1 *' to flip sign of velocity to match Chhatbar algorithm
        velocity(index)  = -1 * (q.b1 - size(LSPIVresult,2)/2 - 1)/shiftamt;
        amps(index)      = q.a1;
        sigmas(index)    = q.c1;
        goodness(index)  = good.rsquare;
    end
    
end

%% find possible bad fits
toc

% abb, convert pixels/scan to mm/sec
% chhatbar fig9im.tif
delx = 0.47; %um
delt = 1; %ms
% drew synthetic
%delx = 1.0e-3;
%delt = 2.05e-3;
mmPerSec = delx/delt;
velocity = velocity * mmPerSec;

% Find bad velocity points using a moving window 
pixel_windowsize = round(windowsize / skipamt);

badpixels = zeros(size(velocity));
for index = 1:1:length(velocity)-pixel_windowsize
    pmean = mean(velocity(index:index+pixel_windowsize-1)); %partial window mean
    pstd  = std(velocity(index:index+pixel_windowsize-1));  %partial std 
    
    pbadpts = find((velocity(index:index+pixel_windowsize-1) > pmean + pstd*numstd) | ...
                   (velocity(index:index+pixel_windowsize-1) < pmean - pstd*numstd));

    badpixels(index+pbadpts-1) = badpixels(index+pbadpts-1) + 1; %running sum of bad pts
end
badvals  = find(badpixels > 0); % turn pixels into indicies
goodvals = find(badpixels == 0);

meanvel  = mean(velocity(goodvals)); %overall mean
stdvel   = std(velocity(goodvals));  %overall std

% abb, save results to a text file
outFileName = fname(1:length(fname)-4);
outFilePath = [pathname outFileName '_kim.txt']

myFileID = fopen(outFilePath,'w');
fprintf(myFileID, 'LSPIV_parallel.m\n');
fprintf(myFileID, 'fname=%s\n', fname);
fprintf(myFileID, 'pathname=%s\n', pathname);
fprintf(myFileID, 'numavgs=%f\n', numavgs);
fprintf(myFileID, 'skipamt=%f\n', skipamt);
fprintf(myFileID, 'shiftamt=%f\n', shiftamt);
fprintf(myFileID, 'time,velocity,amp,sigma,r_2\n')
for i = 1:length(velocity)
    fprintf(myFileID, '%f,%f,%f,%f\n', velocity(i), amps(i), sigmas(i), goodness(i));
end    
fclose(myFileID);

% show results
% abb
%figure(2)
figure
subplot(3,1,1)
imgtmp = zeros([size(imageLines(:,startColumn:endColumn),2) size(imageLines(:,startColumn:endColumn),1) 3]); % to enable BW and color simultaneously
imgtmp(:,:,1) = imageLines(:,startColumn:endColumn)'; imgtmp(:,:,2) = imageLines(:,startColumn:endColumn)'; imgtmp(:,:,3) = imageLines(:,startColumn:endColumn)';
imagesc(imgtmp/max(max(max(imgtmp))))
title('Raw Data');
ylabel('[pixels]');
%colormap('gray');

subplot(3,1,2)
imagesc(index_vals,-numpixels/2:numpixels/2,fftshift(LSPIVresult(:,:),2)');
title('LSPIV xcorr');
ylabel({'displacement'; '[pixels/scan]'});


subplot(3,1,3)
% abb, added 'MarkerSize'
plot(index_vals, velocity,'.', 'MarkerSize', 15);
hold all
plot(index_vals(badvals), velocity(badvals), 'ro');
hold off
xlim([index_vals(1) index_vals(end)]);
ylim([meanvel-stdvel*4 meanvel+stdvel*4]);
title('Fitted Pixel Displacement');
ylabel({'displacement'; '[pixels/scan]'});
xlabel('index [pixel]');

h = line([index_vals(1) index_vals(end)], [meanvel meanvel]);
set(h, 'LineStyle','--','Color','k');
h = line([index_vals(1) index_vals(end)], [meanvel+stdvel meanvel+stdvel]);
set(h, 'LineStyle','--','Color',[.5 .5 .5]);
h = line([index_vals(1) index_vals(end)], [meanvel-stdvel meanvel-stdvel]);
set(h, 'LineStyle','--','Color',[.5 .5 .5]);

fprintf('\nMean  Velocity %0.2f [pixels/scan]\n', meanvel);
fprintf('Stdev Velocity %0.2f [pixels/scan]\n', stdvel);




