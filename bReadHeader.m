function headerStruct = bReadHeader(tifPath)
% bReadHeader  Given an image file, read header information from
% corresponding text file.
%
% Assumes the text file is in a folder 'oir_headers'
%
% returns: Struct with header parameters as field names
%

    headerStruct = struct();
    
    if exist(tifPath, 'file') == 0
        ['ERROR: bReadHeader SOURCE FILE NOT FOUND "' tifPath '"']
        return
    end
    
    [filePath,name,ext] = fileparts(tifPath);
    
    textFileName = [name '.txt'];
    textFilePath = fullfile(filePath, 'oir_headers', textFileName);
    
    disp(['   bReadHeader opening file:' textFilePath]);
    fid = fopen(textFilePath,'r');
    if (fid == -1)
        ['ERROR: bReadHeader CORRESPONDING TEXT FILE NOT FOUND "' textFilePath '"']
        return
    end
    
    aLine = fgetl(fid);
    while ischar(aLine)
        aLineSplit = strsplit(aLine,'=');
        lhs = aLineSplit{1};
        rhs = aLineSplit{2}; % rhs will default to a string
        
        headerStruct.(lhs) = rhs;
        
        aLine = fgetl(fid);
    end