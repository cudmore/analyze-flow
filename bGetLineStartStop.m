function [startColumn,endColumn, pntsPerLine, numLines] = bGetLineStartStop(tifPath)

    startColumn = -999;
    endColumn = -999;
    pntsPerLine = NaN;
    numLines = NaN;

    % used by Kim et al
    %imageLines = imimportTif(tifPath)'; % abb, imimportTif() is a .m file !!!
    % abb
    imageLines = imread(tifPath);
    imageLines = im2double(imageLines); % this is needed otherwise background subtraction (DCoffset) fails???
    %imageLines = imimportTif(tifPath)'; % abb, imimportTif() is a .m file !!!

    [numLines, pntsPerLine] = size(imageLines);
    
    %
    % subtract background signal
    DCoffset = sum(imageLines,1) / size(imageLines,1);
    imageLinesDC = imageLines - repmat(DCoffset,size(imageLines,1),1);

    [filePath, fileName, fileExt] = fileparts(tifPath);
    
    %
    % choose where in the image to process
    myFigHandle = figure;
    
    fileName
    
    subplot(1,3,1);
    % Kim
    %imagesc(imageLines(1:size(imageLines,2),:)) % imagesc is image 'scaled colors'
    % abb
    %imagesc(imageLines(:,:)) % imagesc is image 'scaled colors'
    imagesc(imageLinesDC(:,:)); % imagesc is image 'scaled colors'
    colormap('gray');
    
    % label axis
    xlabel('Pixels along line');
    ylabel('Line Scans');
    
    % size the figure
    set(gcf, 'Position',  [100, 100, 800, 1400]);
    
    showThisNumberOfLines = 1000;
    if showThisNumberOfLines <= numLines
        showThisNumberOfLines = numLines/2;
    end
    
    try
        subplot(1,3,2);
        imagesc(imageLinesDC(1:showThisNumberOfLines,:)); % imagesc is image 'scaled colors'
        colormap('gray');
        title(sprintf('%s',fileName)); % wtf, sprintf is required???

        subplot(1,3,3);
        imagesc(imageLinesDC(numLines-showThisNumberOfLines:numLines,:)); % imagesc is image 'scaled colors'
        colormap('gray');
    catch
        disp('error displaying subplot ???');
        %return
    end
    
    %
    % abb
    subplot(1,3,2) % switch back to plot on left
    userPrompt = 'Click the left (min) point along x-axis to start analysis';
    title(userPrompt);
    disp(userPrompt)
    try
        notGood = 1;
        while notGood
            [X1,Y1] = ginput(1);
            notGood = X1<1 || X1>pntsPerLine;
            if notGood
                disp(['Please select a starting X coordinate within the image ... try again']);
            end
        end
        %disp(['good ' num2str(X1)]);
    catch
        disp([' .  bGetLineStartStop() aborted by user, tifPath:' tifPath]);
        return
    end
    line([X1 X1],[1 size(imageLines,2)]);

    % abb
    %title('Select the boundaries of the region of interest 2/2');
    userPrompt = 'Click the right (max) point along x-axis to start analysis';
    title(userPrompt);
    disp(userPrompt)
    try
        notGood = 1;
        while notGood
            [X2,Y2] = ginput(1);
            notGood = X2<1 || X2>pntsPerLine;
            if notGood
                disp(['Please select an ending X coordinate within the image ... try again']);
            end
        end
        %disp(['good ' num2str(X1)]);
    catch
        disp([' .  bGetLineStartStop() aborted by user, tifPath:' tifPath]);
        return
    end
    line([X2 X2],[1 size(imageLines,2)]);
    refresh
    pause(.01);
    
    startColumn   = round(min(X1, X2));      % Defines what part of the image we perform LSPIV on.
    endColumn     = round(max(X1, X2));
    
    close(myFigHandle);
