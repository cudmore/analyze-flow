
function AnalyzeFlow(tifPath)
% AnalyzeFlow  Analyze blood flow from a line scan
%
% Function parameters
%    tifPath: Full path to .tif file to analyze, if not provided will
%    prompt for a .tif file.
%
% Analysis Parameters
%    delx = DeltaX, microns/pixel
%    delt = DeltaT, ms/line
%
%    Kim algorithm has a velocity dependent parameter
%        shiftamt = 5; % capillary (slow)
%        shiftamt = 1; % artery (fast)

    disp(' ');
    disp('====== Starting bAnalyzeFlow ======');

    showOutput = 1; % set to '1' to plot results of both Kim and Chhatbar
    doRealData = 1; % set to '1' for real data, set to 0 for synthetic/test data

    close all;  % close all figures

    %
    % synthetic/tst data
    if doRealData == 0
        tifPath = 'exampleData/drew_synthetic.tif';
        % image parameters
        delx = 0.15; % 1.0e-3;
        delt = 2.05e-3;
        % kim parameters
        numavgs = 100;
        skipamt = 25;
        shiftamt = 5; % capillary (slow)
        %shiftamt = 1; % artery (fast)

        % x range (pixels) along line to analyze
        %xMin = 1; 
        %xMax = 60;
        
        % The linescan image used in the Figure 9 of the paper named 'fig9im.tif'
        % is located in the same folder as this code. This image can be used as:
        % [angle,utheta,uvar] = hybridvel(imread('fig9im.tif'),1,[],0.47,1,100,25,[1 125]);
        
        %tifPath = 'exampleData/fig9im.tif';
        %delx = 0.47;
        %delt = 1;
    end
    
    acqDate = ''; % filled in when using real data
    acqTime = '';

    %
    % real data
    if doRealData == 1

        % prompt user for .tif file
        if nargin == 0
            disp('Select a .tif file');
            userDataPath = ['/Users/cudmore/box/data/nathan/20190613/Converted/' '*.tif'];
            [userFile,userPath] = uigetfile(userDataPath);
            if isequal(userFile,0)
                disp('Cancelled');
                return
            end

            tifPath = fullfile(userPath, userFile);
        end
        
        % Load header information from corresponding txt file
        % Remember, all value in this header struct will be string and need to
        % be converted.
        headerStruct = bReadHeader2(tifPath);

        if isempty(fieldnames(headerStruct))
            %['ERROR: CORRESPONDING TEXT FILE NOT FOUND "' textFilePath '"']
            return
        end

        % abb added isfield nov 2022
        if isfield(headerStruct, 'date')
            acqDate = headerStruct.date;
        else
            acqDate = '';
        end
        
        if isfield(headerStruct, 'time')
            acqTime = headerStruct.time;
        else
            acqTime = '';
        end
        
        % kim parameters
        numavgs = 100;
        skipamt = 25;
        shiftamt = 5; % capillary (slow)
        %shiftamt = 1; % artery (fast)

        % bReadHeader2 is returning numbers (not char)
        delx = headerStruct.voxelx;
        delt = headerStruct.lineSpeed;
    end

    %
    
    if doRealData == 0
        xMin = 5;
        xMax = 59;
        pntsPerLine = 64;
        numLines = 1024;
    else
        % Ask user for the start/stop column for analysis
        % Nov 29, just using 5 pixels within image
        % turn this back on of needed
        %[xMin, xMax, pntsPerLine, numLines] = bGetLineStartStop(tifPath);

        % just force start/stop along line scan to be 5 pixels
        imageLines = imread(tifPath);
        [numLines, pntsPerLine] = size(imageLines);

        xMin = 5;
        xMax = pntsPerLine - 5;
        disp(['xMin:', num2str(xMin), ' xMax:', num2str(xMax), num2str(pntsPerLine), num2str(numLines)])
    end

    if xMin == -999 || xMax == -999
        return
    end
    
    %
    %  Kim settings
    % Ask user for settings
    if 0
        UIControl_FontSize_bak = get(0, 'DefaultUIControlFontSize');
        set(0, 'DefaultUIControlFontSize', 16);
    
        str = {'capillary (shiftamt=5)', 'artery (shiftamt=1)', 'user'};
        [speedSetting,v] = listdlg('PromptString','Select a configuration',...
                        'SelectionMode','single',...
                        'ListString',str);
        if v == 0
            beep;
            disp('Cancelled');
            return;
        end
    end

    speedSetting = 1;  % abb nov 2022, always use capillary setting for kim

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

    %
    % date/time
    myNow = now;
    myDateTime = datetime(myNow, 'ConvertFrom','datenum');
    myDateTime.Format = 'yyyyMMdd';
    myDate = myDateTime;
    myDateTime.Format = 'hh:mm:ss';
    myTime = myDateTime;

    disp(['   tifPath' tifPath]);
    disp(['   pntsPerLine:', num2str(pntsPerLine)]);
    disp(['   numLines:', num2str(numLines)]);
    disp(['   xMin:' num2str(xMin) ' xMax:' num2str(xMax)]);
    disp([sprintf('   delx:%f', delx)]);
    disp([sprintf('   delt:%f', delt)]);

    %
    % Drew et al
    %
    %OUTPUTS
    %thetas - the time varying agle of the space-time image
    %the_t - time pointsof the angle estimates (in lines)
    %spreadmatrix - matix of variances as a function of angles at each time point
    %spatial_freq=1;
    %npoints=64*spatial_freq; %number of points in a line
    drewData = imimportTif(tifPath)';
    %disp(['1 calling bDrew with pntsPerLine:', num2str(pntsPerLine), ' ', class(pntsPerLine)])
    %disp(['    drewData size() is: ', num2str(size(drewData)), ' class is ', class(drewData)])

    %windowsize - number of lines to use in estimating velocity.
    % must be a multiple of 4
    % cap3 returned false positive 0 velocity for windowSize=20, 24, 32
    drewWindowSize = 16;
    [thetasz32, the_tz32, spread_radon32] = bDrew(drewData, drewWindowSize);

    disp(['    drew returned the_tz32: ', num2str(size(the_tz32)), ' ', class(the_tz32)])
    disp(['    drew returned spread_radon32: ', num2str(size(spread_radon32)), ' ', class(spread_radon32)])

    % plot drew
    figure
    ax1 = subplot(411);
    xImage = [0, numLines] * delt;
    yImage = [0, pntsPerLine];
    imagesc(xImage, yImage, drewData') %plots the artificial 'linescan'
    colormap gray
    title('Drew Raw Data');
    %[thetasz32,the_tz32,spread_radon32]=GetVelocityRadonFig_demo(zz,npoints);

    ax2 = subplot(412);
    %plot(the_tz32*delt,thetasz32, 'b')% plots the angle at any given time point
    %hold on;
    plot(the_tz32*delt, thetasz32, 'bo')% plots the angle at any given time point
    xlabel('time (sec)')
    ylabel('angle, degrees')

    ax3 = subplot(413);
    my_delx = delx;
    my_deltat = delt;  % us/pixel
    %rad_thetasz32 = deg2rad(thetasz32);
    drewTime = the_tz32*delt;
    drewVelocity = (my_delx/my_deltat) * tand(thetasz32);  % delx is um/pixel 
    drewVelocity = drewVelocity / 1000;
    plot(drewTime, drewVelocity, 'ro')  % plots the angle at any given time point
    ylabel('velocity (mm/sec)')
    
    meanDrewVelocity = mean(drewVelocity);
    stdDrewVelocity = std(drewVelocity);
    disp(['    final drew velocity mean:', num2str(meanDrewVelocity), ' sd:', num2str(stdDrewVelocity)])

    % add mean +/- std of velocity
    % TODO: remove velocity (> mean+2*std, < mean-2*std)
    h = line([drewTime(1) drewTime(end)], [meanDrewVelocity meanDrewVelocity]);
    set(h, 'LineStyle','--','Color','k');
    h = line([drewTime(1) drewTime(end)], [meanDrewVelocity+stdDrewVelocity meanDrewVelocity+stdDrewVelocity]);
    set(h, 'LineStyle','--','Color',[.5 .5 .5]);
    h = line([drewTime(1) drewTime(end)], [meanDrewVelocity-stdDrewVelocity meanDrewVelocity-stdDrewVelocity]);
    set(h, 'LineStyle','--','Color',[.5 .5 .5]);

    ax4 = subplot(414);
    %max_spread_radon32 = max(spread_radon32, [], 2);
    max_spread_radon32 = max(spread_radon32, 2);
    plot(the_tz32*delt, max_spread_radon32, 'bo')  % plots the angle at any given time point
    xlabel('time (sec)')
    ylabel('variance')


    linkaxes([ax1,ax2,ax3,ax4],'x');

    saveDrew = 1
    if saveDrew
        [filepath,name,ext] = fileparts(tifPath);
        savePath = fullfile(filepath, 'matlabAnalysis');
        if ~exist(savePath, 'dir')
            mkdir(savePath);
        end
        saveDrewFigPath = fullfile(savePath, [name '_drew.png']);

        display(['saving figure to ', saveDrewFigPath])
        saveas(gca, saveDrewFigPath);
    end

    %return

    %
    % Kim et al
    %

    % if you know the start/stop, xMin/xMax
    % nov 24, turned off
    %[kimTime,kimVelocity] = bKim(tifPath, showOutput, delx, delt, numavgs, skipamt, shiftamt, xMin, xMax);

    % or this and matlab will ask you for xMin and xMax
    %[myTime,velocity] = bKim0(tifPath, showOutput, delx, delt, numavgs, skipamt, shiftamt);


    %
    % Chhatbar and Kara
    %
    % Chattbar parameters
    %delx (microns/pixel)
    %delt (ms/line)
    delt_chhatbar = delt * 1000;
    
    hi = 100;
    lineskip = 16;
%     tmpImsize = size(drewData);
%     hi = tmpImsize(2)-2;
%     lineskip = pntsPerLine;

    showOutput = 1;
    saveimg = 1;
    disp(['calling bChhatbar with delt_chhatbar:'])
    disp(['   delt_chhatbar:', num2str(delt_chhatbar)])
    disp(['   hi:', num2str(hi)])
    disp(['   lineskip:', num2str(lineskip)])
    [chhatbarTime,chhatbarVelocity,angle,utheta,uvar] = bChhatbar(tifPath,showOutput,saveimg,delx,delt_chhatbar,hi,lineskip,xMin,xMax);
    chhatbarTime = chhatbarTime / 1000;

    disp(['    final chhatbar velocity mean:', num2str(mean(chhatbarVelocity)), ' sd:', num2str(std(chhatbarVelocity))])
    disp(['    chhatbarVelocity size:', num2str(size(chhatbarVelocity))])%
    
    if 0
        % plot drew angle with chhatbar angle
        figure
        disp(['    drew is blue'])
        plot(the_tz32*delt, drewVelocity, 'bo-');  % drew
        legend('drew');
        hold on;
        plot(chhatbarTime, chhatbarVelocity, 'ro-');  % chhatbar
        legend('chhatbar');

    %% 
    % put results in one big file '_combined.txt'
    [filePath, fileName, fileExt] = fileparts(tifPath);
    originalFileName = [fileName fileExt];
    outFileName = [fileName '_combined.csv'];
    outFilePath = fullfile(filePath, outFileName);
    disp(['*** saving combined ' outFilePath])

    myFileID = fopen(outFilePath, 'w', 'n', 'UTF-8');
    headerStr = 'filepath,file,acqDate,acqTime,analysisDate,analysisTime,pntsPerLine,numLines,delx,delt,x1,x2,algorithm,k_numavgs,k_skipamt,k_shiftamt,c_hi,c_lineskip,time,velocity';
    fprintf(myFileID, headerStr);
    fprintf(myFileID, '\n');

    % turned off nov 24
%     mKim = length(kimTime);
%     for i = 1:mKim
%         fprintf(myFileID, '%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'kim', numavgs, skipamt, shiftamt, nan, nan, kimTime(i), kimVelocity(i));
%     end

    mChhatbar = length(chhatbarTime);
    for i = 1:mChhatbar
        fprintf(myFileID, '%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'chhatbar', nan, nan, nan, hi, lineskip, chhatbarTime(i), chhatbarVelocity(i));
    end

    mDrew = length(drewTime);
    for i = 1:mDrew
        fprintf(myFileID, '%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'drew', nan, nan, nan, hi, lineskip, drewTime(i), drewVelocity(i));
    end

end % bAnalyze