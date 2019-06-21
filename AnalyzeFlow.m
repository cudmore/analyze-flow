
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
    doRealData = 1; % set to '1' for real data, set to data for synthetic/test data

    %
    % synthetic/tst data
    if doRealData == 0
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
        headerStruct = bReadHeader(tifPath);

        if isempty(fieldnames(headerStruct))
            %['ERROR: CORRESPONDING TEXT FILE NOT FOUND "' textFilePath '"']
            return
        end

        acqDate = headerStruct.date;
        acqTime = headerStruct.time;

        % kim parameters
        numavgs = 100;
        skipamt = 25;
        shiftamt = 5; % capillary (slow)
        %shiftamt = 1; % artery (fast)

        delx = str2num(headerStruct.voxelx);
        delt = str2num(headerStruct.lineSpeed);
    end

    %
    % Ask user for the start/stop column for analysis
    [xMin, xMax, pntsPerLine, numLines] = bGetLineStartStop(tifPath);

    if xMin == -999 || xMax == -999
        return
    end
    
    %
    %  Kim settings
    % Ask user for setting 
    
    % My eyes are getting old, dear matlab ... is it possible to increase your font size???
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
    disp(['   xMin:' num2str(xMin) ' xMax:' num2str(xMax)]);
    disp([sprintf('   delx:%f', delx)]);
    disp([sprintf('   delt:%f', delt)]);

    %
    % Kim et al
    %

    % if you know the start/stop, xMin/xMax
    [kimTime,kimVelocity] = bKim(tifPath, showOutput, delx, delt, numavgs, skipamt, shiftamt, xMin, xMax);

    % or this and matlab will ask you for xMin and xMax
    %[myTime,velocity] = bKim0(tifPath, showOutput, delx, delt, numavgs, skipamt, shiftamt);


    %
    % And then chhatbar and kara
    %
    % Chattbar parameters
    %delx (microns/pixel)
    %delt (ms/line)
    hi = 100;
    lineskip = 25;

    showOutput = 1;
    saveimg = 0;
    [chhatbarTime,chhatbarVelocity,angle,utheta,uvar] = bChhatbar(tifPath,showOutput,saveimg,delx,delt,hi,lineskip,xMin,xMax);

    %
    % put results in one big file '_combined.txt'
    [filePath, fileName, fileExt] = fileparts(tifPath);
    originalFileName = [fileName fileExt];
    outFileName = [fileName '_combined.txt'];
    outFilePath = fullfile(filePath, outFileName);
    disp(['*** saving combined ' outFilePath])

    myFileID = fopen(outFilePath, 'w', 'n', 'UTF-8');
    headerStr = 'filepath,file,acqDate,acqTime,analysisDate,analysisTime,pntsPerLine,numLines,delx,delt,x1,x2,algorithm,k_numavgs,k_skipamt,k_shiftamt,c_hi,c_lineskip,time,velocity';
    fprintf(myFileID, headerStr);
    fprintf(myFileID, '\n');

    mKim = length(kimTime);
    for i = 1:mKim
        fprintf(myFileID, '%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'kim', numavgs, skipamt, shiftamt, nan, nan, kimTime(i), kimVelocity(i));
    end

    mKim = length(chhatbarTime);
    for i = 1:mKim
        fprintf(myFileID, '%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'chhatbar', nan, nan, nan, hi, lineskip, chhatbarTime(i), chhatbarVelocity(i));
    end

end % bAnalyze