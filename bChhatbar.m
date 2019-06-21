
function [time,velocity,angle,utheta,uvar] = bChhatbar(tifPath,showOutput,saveimg,delx,delt,hi,lineskip,x1,x2)

    disp(['*** chhatbar anaysis' tifPath]);
    
    theImage = imread(tifPath); % hybridvel expects a matlab matrix, not a file

    xrange = [x1 x2];
    
    % hybridvel issues warnings, turn them off
    MSGID = 'MATLAB:hg:EraseModeIgnored';
    warning('off', MSGID);

    [theAngle,utheta,uvar] = bChhatbar0(theImage,showOutput,saveimg,delx,delt,hi,lineskip,xrange);

    ii = 3;
    time = theAngle(:,3,ii)*delt;
    angle = theAngle(:,1,ii);
    velocity = theAngle(:,9,ii);

    doSave = 0;
    if doSave
        [filePath, fileName, fileExt] = fileparts(tifPath);
        outFileName = [fileName '_chhatbar.txt'];
        outFilePath = fullfile(filePath, outFileName);
        disp(['   saving chhatbar' outFilePath])

        myFileID = fopen(outFilePath, 'w', 'n', 'UTF-8');
            fprintf(myFileID, 'algorithm=Chhatbar hybridvel;');
            fprintf(myFileID, 'tifPath=%s;', tifPath);
            fprintf(myFileID, 'delx=%f;', delx);
            fprintf(myFileID, 'delt=%f;', delt);
            fprintf(myFileID, 'hi=%d;', hi);
            fprintf(myFileID, 'lineskip=%d;', lineskip);
            fprintf(myFileID, 'xMin=%d;', xrange(1));
            fprintf(myFileID, 'xMax=%d;', xrange(2));
            fprintf(myFileID, '\n');
            fprintf(myFileID, 'time,velocity,angle'); % column headers
            fprintf(myFileID, '\n');
            for i = 1:size(time,1)
                fprintf(myFileID, '%d,%f,%f\n', time(i), velocity(i), angle(i));
            end    
        fclose(myFileID);
    end