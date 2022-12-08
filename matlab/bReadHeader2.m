function headerStruct = bReadHeader2(tifPath)
% bReadHeader  Given an image file, read header information from
% corresponding text file.
%
% Assumes the text file is in same folder as .tif
% Assumes the txt file was created on export oir to tif in Olympus software
%
%    "X Dimension"	"30, 0.0 - 11.932 [um], 0.398 [um/pixel]"
%    "Channel Dimension"	"1 [Ch]"
%    "T Dimension"	"1, 0.000 - 34.619 [s], Interval FreeRun"
%
% returns: Struct with header parameters as field names
%    
    if exist(tifPath, 'file') == 0
        ['ERROR: bReadHeader2 SOURCE FILE NOT FOUND "' tifPath '"']
        return
    end
    
    [filePath,name,ext] = fileparts(tifPath);
    
    textFileName = [name '.txt'];
    textFilePath = fullfile(filePath, textFileName);
    
    disp(['   bReadHeader2 opening file:' textFilePath]);
    fid = fopen(textFilePath,'r');
    if (fid == -1)
        ['ERROR: bReadHeader CORRESPONDING TEXT FILE NOT FOUND "' textFilePath '"']
        return
    end
    
%     dateStr = '';
%     timeStr = '';
%     umPerPixel = '';
%     durRecording_sec = '';
%     numLineScans = '';

    aLine = fgetl(fid);
    while ischar(aLine)
        %disp([aLine]);
        aLine2 = strrep(aLine, '"', "");

        % "Date"	"11/02/2022 12:56:48.049 PM"
        if (startsWith(aLine2, 'Date'))
            aLineSplit = strsplit(aLine2,'\t');
            dateTimeLine = aLineSplit{2};
            %disp(['dateTimeLine:', dateTimeLine])
            dateTimeSplit = strsplit(dateTimeLine, ' ');
            %disp(['dateTimeSplit:', dateTimeSplit])
            dateStr = dateTimeSplit{1};
            timeStr = dateTimeSplit{2};
        end

        % um/pixel is in this line
        % "X Dimension"	"30, 0.0 - 11.932 [um], 0.398 [um/pixel]"
        if (startsWith(aLine2, 'X Dimension'))
            aLineSplit = strsplit(aLine2,' ');
            %disp(['    ', aLineSplit])
            umPerPixel = aLineSplit{7}; % rhs is a str
            umPerPixel = str2num(umPerPixel);
            %disp(['umPerPixel:', umPerPixel])
        end

        % duration of recording is in this line
        % "T Dimension"	"1, 0.000 - 34.619 [s], Interval FreeRun"
        if (startsWith(aLine2, 'T Dimension'))
            aLineSplit = strsplit(aLine2,' ');
            %disp(['    ', aLineSplit])
            durRecording_sec_char = aLineSplit{5}; % rhs is a str
            %disp(['1 durRecording_sec_char:', durRecording_sec_char, class(durRecording_sec_char)])
            durRecording_sec = str2num(durRecording_sec_char);
            %disp(['2 durRecording_sec:', durRecording_sec, class(durRecording_sec)])
        end

        % number of line scans is here. Be careful, this is repeated for
        % image with 512 * 512 or similar
        % "Image Size"	"30 * 30000 [pixel]"
        if (startsWith(aLine2, 'Image Size'))
            doIt = 1;
            if (startsWith(aLine2, 'Image Size(Unit Converted)'))
                doIt = 0;
            end
            if exist('numLineScans','var') == 1
                % numLineScans has already been read, assume 512 * 512 comes second in txt file
                doIt = 0;
            end
            if doIt
                aLineSplit = strsplit(aLine2,' ');
                %disp(['    ', aLineSplit])
                numLineScans = aLineSplit{4}; % rhs is a str
                %disp(['1 numLineScans:', numLineScans])
                numLineScans = str2num(numLineScans);
                %disp(['2 numLineScans:', numLineScans])
            end
        end

        % read the next line
        aLine = fgetl(fid);
    end

%     class(durRecording_sec)
%     class(numLineScans)
    
    headerStruct = struct();
    headerStruct.dateStr = dateStr;
    headerStruct.timeStr = timeStr;
    headerStruct.voxelx = umPerPixel;
    headerStruct.numLineScans = numLineScans;
    headerStruct.durRecording_sec = durRecording_sec; % we really want line speed
    headerStruct.lineSpeed = durRecording_sec / numLineScans;

    return  % return control to calling function