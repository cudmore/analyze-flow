function [myTime,velocity] = bKim(tifPath, showOutput, delx, delt, numavgs, skipamt, shiftamt, X1, X2)

% Purpose:
%    Run Kim et al (2012) blood flow analysis on given lin scan .tif image
%
% Input Parameters:
%    tifPath: full path to .tif file
%    showOutput: 
%    delx: 
%    delt: 
%    numavgs: 
%    skipamt: 
%    shiftamt: 
%    X1: 
%    X2: 
%
% Output Paramets:
%    myTime: time in seconds
%    velocity: blood flow velocity 

    tic

    disp(['*** kim anaysis' tifPath]);
    
    if nargin==7
        getx = 1;
    else
        getx = 0;
    end
    
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
   
    imageLines = imimportTif(tifPath)'; % abb, imimportTif() is a .m file !!!

    if getx==1
        [X1,X2] = bGetLineStartStop(tifPath);
        disp(['User selected X1=' X1 'X2=' X2])
        
        if 0
            %% choose where in the image to process
            figure
            imagesc(imageLines(1:size(imageLines,2),:)) % imagesc is image 'scaled colors'
            colormap('gray')

            % abb
            title('Click the left (min) point along x-axis to start analysis');
            [X1,Y1] = ginput(1);
            line([X1 X1],[1 size(imageLines,2)]);

            % abb
            %title('Select the boundaries of the region of interest 2/2');
            title('Click the right (max) point along x-axis to start analysis');
            [X2,Y2] = ginput(1);
            line([X2 X2],[1 size(imageLines,2)]);
            refresh
            pause(.01);
        end
    end
    
    startColumn   = round(min(X1, X2));      % Defines what part of the image we perform LSPIV on.
    endColumn     = round(max(X1, X2));

    disp(['   analyzing line scan from pnt: ', num2str(startColumn), ' to pnt ', num2str(endColumn)])

    if isempty(gcp('nocreate'))
        parpool('local',numWorkers)
    else
        disp('   parpool Already Detected');
    end
    
    %% minus out background signal (PWG 6/4/2009)
    %disp('DC correction')
    DCoffset = sum(imageLines,1) / size(imageLines,1);
    imageLinesDC = imageLines - repmat(DCoffset,size(imageLines,1),1);

    %% do LSPIV correlation
    %disp('LSPIV begin');

    scene_fft = fft(imageLinesDC(1:end-shiftamt,:),[],2);
    test_img = zeros(size(scene_fft));
    test_img(:,startColumn:endColumn) = imageLinesDC(shiftamt+1:end, startColumn:endColumn);
    test_fft = fft(test_img,[],2);
    W = 1./sqrt(abs(scene_fft)) ./ sqrt(abs(test_fft)); % phase only

    LSPIVresultFFT = scene_fft .* conj(test_fft) .* W; 
    LSPIVresult = ifft(LSPIVresultFFT,[],2);
    %disp('LSPIV complete');

    %% find shift amounts
    %disp('Find the peaks');
    velocity = [];
    maxpxlshift = round(size(imageLines,2)/2)-1;


    index_vals = skipamt:skipamt:(size(LSPIVresult,1) - numavgs);
    numpixels = size(LSPIVresult,2);
    myTime  = nan(size(index_vals));
    myTimeSeconds  = nan(size(index_vals));
    velocity  = nan(size(index_vals));
    amps      = nan(size(index_vals));
    sigmas    = nan(size(index_vals));
    goodness  = nan(size(index_vals));

    disp(['   starting parfor loop for ', num2str(max(index_vals)), ' index_vals'])

    % IF THERE ARE ERRORS IN HERE, SWITCH 'parfor' to 'for'
    parfor index = 1:length(index_vals)

        %disp(['index:' index])
        
        % abb, changed from 100 to 400 to 1000
        if mod(index_vals(index),1000) == 0
            fprintf('      parfor line: %d\n',index_vals(index))
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
        % abb, added '-1 *' to flip sign of velocity to match Chhatbar algorithm
        myTime(index) = index_vals(index)*delt; % ms
        myTimeSeconds(index) = myTime(index) / 1000; % seconds
        velocity(index)  = -1 * (q.b1 - size(LSPIVresult,2)/2 - 1)/shiftamt;
        amps(index)      = q.a1;
        sigmas(index)    = q.c1;
        goodness(index)  = good.rsquare;

    end

    %% find possible bad fits

    % abb, convert pixels/scan to mm/sec
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

    %
    % abb, save results to a text file
    doSave = 0;
    if doSave
        [filePath, fileName, fileExt] = fileparts(tifPath);
        outFileName = [fileName '_kim.txt'];
        outFilePath = fullfile(filePath, outFileName);

        disp(['   saving kim: ' outFilePath])
        myFileID = fopen(outFilePath,'w');
        fprintf(myFileID, 'algorithm=Kim LSPIV_parallel;');
        fprintf(myFileID, 'tifPath=%s;', tifPath);
        fprintf(myFileID, 'delx=%f;', delx);
        fprintf(myFileID, 'delt=%f;', delt);
        fprintf(myFileID, 'numavgs=%d;', numavgs);
        fprintf(myFileID, 'skipamt=%d;', skipamt);
        fprintf(myFileID, 'shiftamt=%d;', shiftamt);
        fprintf(myFileID, 'xMin=%d;', X1);
        fprintf(myFileID, 'xMax=%d;', X2);
        fprintf(myFileID, '\n');
        fprintf(myFileID, 'time,velocity,amp,sigma,r_2\n');
        for fuckThisi = 1:length(velocity)
            fprintf(myFileID, '%f,%f,%f,%f,%f\n', myTime(fuckThisi), velocity(fuckThisi), amps(fuckThisi), sigmas(fuckThisi), goodness(fuckThisi));
        end    
        fclose(myFileID);
    end
    
    if showOutput
        % show results
        % abb
        %figure(2)
        figKim = figure;
        movegui(figKim, [200 300]); % specifies distance from bottom left of screen [x,y] ???
        
        subplot(3,1,1);
        imgtmp = zeros([size(imageLines(:,startColumn:endColumn),2) size(imageLines(:,startColumn:endColumn),1) 3]); % to enable BW and color simultaneously
        imgtmp(:,:,1) = imageLines(:,startColumn:endColumn)'; imgtmp(:,:,2) = imageLines(:,startColumn:endColumn)';
        imgtmp(:,:,3) = imageLines(:,startColumn:endColumn)';
        imagesc(imgtmp/max(max(max(imgtmp))));
        title('Raw Data');
        ylabel('[pixels]');
        %colormap('gray');

        subplot(3,1,2);
        imagesc(index_vals,-numpixels/2:numpixels/2,fftshift(LSPIVresult(:,:),2)');
        title('LSPIV xcorr');
        ylabel({'displacement'; '[pixels/scan]'});


        subplot(3,1,3);
        % abb, added 'MarkerSize'
        %plot(index_vals, velocity,'.', 'MarkerSize', 15);
        %hold all;
        %plot(index_vals(badvals), velocity(badvals), 'ro');
        %hold off;
        %xlim([index_vals(1) index_vals(end)]);

        plot(myTimeSeconds, velocity,'.', 'MarkerSize', 15);
        hold all;
        plot(myTimeSeconds(badvals), velocity(badvals), 'ro');
        hold off;
        xlim([myTimeSeconds(1) myTimeSeconds(end)]);

        ylim([meanvel-stdvel*4 meanvel+stdvel*4]);
        title('Fitted Pixel Displacement');
        ylabel({'displacement'; '[pixels/scan]'});
        %xlabel('index [pixel]');
        xlabel('Time (seconds)');

        h = line([index_vals(1) index_vals(end)], [meanvel meanvel]);
        set(h, 'LineStyle','--','Color','k');
        h = line([index_vals(1) index_vals(end)], [meanvel+stdvel meanvel+stdvel]);
        set(h, 'LineStyle','--','Color',[.5 .5 .5]);
        h = line([index_vals(1) index_vals(end)], [meanvel-stdvel meanvel-stdvel]);
        set(h, 'LineStyle','--','Color',[.5 .5 .5]);

        fprintf('   Mean  Velocity %0.2f [pixels/scan]\n', meanvel);
        fprintf('   Stdev Velocity %0.2f [pixels/scan]\n', stdvel);
    end
    
    toc


end