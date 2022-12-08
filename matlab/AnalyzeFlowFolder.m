function bAnalyzeFlowFolder(folderPath)

% bAnalyzeFlowFolder . Run bAnalyzeFlow on all .tif files in a user selected folder

    if nargin == 0
        % remove for other users
        % matlab requires trailing '/' to interpret this as a path (wtf, why do they do this!)
        myPath = '/Users/cudmore/box/data/nathan/20190613/Converted/';
        
        folderPath = uigetdir(myPath, 'Select folder with .tif files')
        
        if folderPath == 0
            % cancel
            return
        end
    end
    
    tifWildcard = fullfile(folderPath, '*.tif');
    tifFiles = dir(tifWildcard);
    numFiles = length(tifFiles);
    for i = 1:numFiles
        file = tifFiles(i)
        tifFilePath = fullfile(file.folder, file.name);
        %
        disp(['=== Tiff file ' num2str(i) ' of ' num2str(numFiles)]);
        %
        AnalyzeFlow2(tifFilePath);
        %

        close all;  % close all figures

    end
    