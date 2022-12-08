function AnalyzeFlow(tifPath)
    doRealData = 1;  % set to 0 for synthetic, 1 for real%

    acqDate = ''; % filled in when using real data
    acqTime = '';

    if doRealData == 0
        tifPath = 'exampleData/drew_synthetic.tif';
        % image parameters
        delx = 0.15; % 1.0e-3;
        delt = 2.05e-3;

        % The linescan image used in the Figure 9 of the paper named 'fig9im.tif'
        % is located in the same folder as this code. This image can be used as:
        % [angle,utheta,uvar] = hybridvel(imread('fig9im.tif'),1,[],0.47,1,100,25,[1 125]);
    else
        % prompt user for .tif file
        if nargin == 0
            disp('Select a .tif file');
            %userDataPath = ['/Users/cudmore/box/data/nathan/20190613/Converted/' '*.tif'];
            userDataPath = ['/', '*.tif'];
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

        % bReadHeader2 is returning numbers (not char)
        delx = headerStruct.voxelx;
        delt = headerStruct.lineSpeed;

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
    end  % if doRealData 0 else ...

    if doRealData == 0
        xMin = 5;
        xMax = 59;
        pntsPerLine = 64;
        numLines = 1024;
    else
        % just force start/stop along line scan to be 5 pixels
        imageLines = imread(tifPath);
        [numLines, pntsPerLine] = size(imageLines);

        % for chhatbar
        xMin = 5;
        xMax = pntsPerLine - 5;

        % capillary 5 0001
%         xMin = 15;
%         xMax = pntsPerLine - 5;
        
        disp(['xMin:', num2str(xMin), ' xMax:', num2str(xMax), num2str(pntsPerLine), num2str(numLines)])
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

    %% Drew
    drewData = imimportTif(tifPath)';  % transposed
    drewWindowSize = 16;  % must be factor of 4 (# lines for each step)
    [thetasz32, the_tz32, spread_radon32] = bDrew(drewData, drewWindowSize);

    drewTime = the_tz32*delt;
    drewVelocity = (delx/delt) * tand(thetasz32);  % delx is um/pixel 
    drewVelocity = drewVelocity / 1000;

    %% Plot drew
    figure
    ax1 = subplot(311);
    xImage = [0, numLines] * delt;
    yImage = [0, pntsPerLine];
    imagesc(xImage, yImage, drewData') %plots the artificial 'linescan'
    colormap gray
    [filepath,name,ext] = fileparts(tifPath)
    title(['Drew ', [name ext]]);
    %[thetasz32,the_tz32,spread_radon32]=GetVelocityRadonFig_demo(zz,npoints);

    ax2 = subplot(312);
    %plot(the_tz32*delt,thetasz32, 'b')% plots the angle at any given time point
    %hold on;
    plot(the_tz32*delt, thetasz32, 'bo')% plots the angle at any given time point
    xlabel('time (sec)')
    ylabel('angle, degrees')

    ax3 = subplot(313);
    my_delx = delx;
    my_deltat = delt;  % us/pixel
    %rad_thetasz32 = deg2rad(thetasz32);
    drewTime = the_tz32*delt;
    drewVelocity = (my_delx/my_deltat) * tand(thetasz32);  % delx is um/pixel 
    drewVelocity = drewVelocity / 1000;
    plot(drewTime, drewVelocity, 'ro-')  % plots the angle at any given time point
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

%     ax4 = subplot(414);
%     %max_spread_radon32 = max(spread_radon32, [], 2);
%     max_spread_radon32 = max(spread_radon32, 2);
%     plot(the_tz32*delt, max_spread_radon32, 'bo')  % plots the angle at any given time point
%     xlabel('time (sec)')
%     ylabel('variance')

%     linkaxes([ax1,ax2,ax3,ax4],'x');
    linkaxes([ax1,ax2,ax3],'x');

    %% Save Drew
    saveDrew = 1;
    if saveDrew
        [filepath,name,ext] = fileparts(tifPath);
        [tmpFilepath,folderName,ext] = fileparts(filepath);
        savePath = fullfile(filepath, [folderName '-matlab-analysis']);
        if ~exist(savePath, 'dir')
            mkdir(savePath);
        end
        saveDrewFigPath = fullfile(savePath, [name '_drew.png']);

        display(['saving figure to ', saveDrewFigPath])
        saveas(gca, saveDrewFigPath);
    end

    %% Chhatbar and Kara
    %
    %delx (microns/pixel)
    %delt (ms/line)
    delt_chhatbar = delt * 1000;
    
    hi = 100;
    lineskip = 16;

    showOutput = 1;
    saveimg = 1;
    disp(['calling bChhatbar with:'])
    disp(['   delt_chhatbar:', num2str(delt_chhatbar)])
    disp(['   hi:', num2str(hi)])
    disp(['   lineskip:', num2str(lineskip)])
    [chhatbarTime,chhatbarVelocity,angle,utheta,uvar] = bChhatbar(tifPath,showOutput,saveimg,delx,delt_chhatbar,hi,lineskip,xMin,xMax);
    chhatbarTime = chhatbarTime / 1000;

    %% save the results in one big file '_combined.csv'
    [filepath,name,ext] = fileparts(tifPath);
    [tmpFilepath,folderName,ext] = fileparts(filepath);
    savePath = fullfile(filepath, [folderName '-matlab-analysis']);
    if ~exist(savePath, 'dir')
        mkdir(savePath);
    end

    [filePath, fileName, fileExt] = fileparts(tifPath);
    originalFileName = [fileName fileExt];  % save this in the csv
    combinedFileName = [fileName '_combined.csv'];
    combinedFilePath = fullfile(savePath, combinedFileName);
    disp(['*** saving combined ' combinedFilePath])

    [tmpFilePath, parentFolder, tmpExt] = fileparts(filePath);

    combinedFileID = fopen(combinedFilePath, 'w', 'n', 'UTF-8');
    headerStr = 'filepath,parentFolder,file,acqDate,acqTime,analysisDate,analysisTime,pntsPerLine,numLines,delx,delt,x1,x2,algorithm,k_numavgs,k_skipamt,k_shiftamt,c_hi,c_lineskip,time,velocity';
    fprintf(combinedFileID, headerStr);
    fprintf(combinedFileID, '\n');

    lenChhatbar = length(chhatbarTime);
    for i = 1:lenChhatbar
        fprintf(combinedFileID, '%s,%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, parentFolder, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'chhatbar', nan, nan, nan, hi, lineskip, chhatbarTime(i), chhatbarVelocity(i));
    end

    lenDrew = length(drewTime);
    for i = 1:lenDrew
        fprintf(combinedFileID, '%s,%s,%s,%s,%s,%s,%s,%d,%d,%f,%f,%d,%d,%s,%d,%d,%d,%d,%d,%f,%f\n', tifPath, parentFolder, originalFileName, acqDate, acqTime, myDate, myTime, pntsPerLine, numLines, delx, delt, xMin, xMax, 'drew', nan, nan, nan, hi, lineskip, drewTime(i), drewVelocity(i));
    end

    fclose(combinedFileID);

    %% Done
    disp(['AnalyzeFlow2 finished with tif: ', tifPath])

