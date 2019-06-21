% requires:
%     Statistics and Machine Learning Toolbox

function [] = bChhatbar(optionsFile)

% chhatbar code in hybrid velocity issues a warning, turn it off
%[a, MSGID] = lastwarn();
MSGID = 'MATLAB:hg:EraseModeIgnored'
warning('off', MSGID)

%check that optionsFile exists

inputTif = '';
tmpstack = '';
channel = 1;
lineidx = 0;
originalfile = '';
inputimg = '';

showimg = 1;
saveimg = 0;

if (0)
    %open optionsFile and grab options (duh)
    fid = fopen(optionsFile,'r');
    if (fid == -1)
        
        ['ERROR: FILE NOT FOUND' optionsFile]
        return
    end
    
    aLine = fgetl(fid);
    while ischar(aLine)
        aLineSplit = strsplit(aLine,'=');
        lhs = aLineSplit{1};
        rhs = aLineSplit{2};
        
        switch lhs
            case 'inputimg'
                inputimg = strrep(rhs, '''', '');
                [tifPath,tifName,tifExt] = fileparts(inputimg);
                inputTif = [tifName tifExt]
            case 'tmpstack'
                tmpstack = strrep(rhs, '''', '');
            % bob's parameter
            case 'lineidx'
                lineidx = str2num(rhs);
            case 'originalfile'
                originalfile = strrep(rhs, '''', '');
            case 'channel'
                channel = str2num(rhs);
            case 'showimg'
                showimg = str2num(rhs);
            case 'saveimg'
                saveimg = str2num(rhs);
            case 'delx'
                delx = str2num(rhs);
            case 'delt'
                delt = str2num(rhs);
            case 'hi'
                hi = str2num(rhs);
            case 'lineskip'
                lineskip = str2num(rhs);
          
            % todo 20171027, add xrange=[xMin xMax]
            %case 'xrange'
            
            case 'xMin'
                xMin = str2num(rhs);
            case 'xMax'
                xMax = str2num(rhs);
            
        end
        
        aLine = fgetl(fid);
        
    end
    fclose(fid);
    
    xrange = [xMin xMax];
    
end

%paste parameters here

if (0)
  Date='2014_01_28 6:48:19 PM';
  inputimg='data/X20140128_a142_013_ch2ur2.tif';
  showimg=1;
  saveimg=0;
  delx=0.081818;
  delt=1.16;
  hi=100;
  lineskip=25;
  xMin=1;
  xMax=1000;

  xrange = [xMin xMax];
end
  

%Chhatbar demo
if (1)
    inputimg = 'exampleData/fig9im.tif';
    showimg = 1;
    saveimg = 0;
    delx = 0.47; %um
    delt = 1; %ms
    
    hi = 100;
    lineskip = 25;
    xMin = 1;
    xMax = 125;
    xrange = [1 125];
end
%[angle,utheta,uvar] = hybridvel(imread('fig9im.tif'),1,[],0.47,1,100,25,[1 125]);

%Drew synthetic
if (0)
    inputimg = 'exampleData/drew_synthetic.tif'
    delx=1.0e-6; %pixel length
    delt=2.05e-6; %pixel clock
    delx = 1.0e-3;
    delt = 2.05e-3;
    
    %delx = 1;
    %delt = 1;
    
    hi = 100;
    lineskip = 25;
    xMin = 1;
    xMax = 60;
    xrange = [1 60]
end

disp('===========   hybridvel()   ==================================')
%disp(['   originalfile:' originalfile])
if (0)
    disp(['   channel:' num2str(channel)])
    disp(['   lineIdx:' num2str(lineidx)])
    disp(['   inputimg:' inputimg])
    disp(['   showimg:' num2str(showimg)])
    disp(['   saveimg:' num2str(saveimg)])
end
disp(['   delx:' num2str(delx)])
disp(['   delt:' num2str(delt)])
disp(['   hi:' num2str(hi)])
disp(['   lineskip:' num2str(lineskip)])
disp(['   xrange:' num2str(xrange)])

disp(['   Reading image...'])
theImage = imread(inputimg);
disp(['      theImage dim: ' num2str(size(theImage,1)) ' x ' num2str(size(theImage,2))])
disp(['   Running hybridvel()...'])

tic;
[angle,utheta,uvar] = hybridvel(theImage,showimg,saveimg,delx,delt,hi,lineskip,xrange);
elapsedTime = toc;

disp(['      took ' num2str(elapsedTime) ' sec'])

%columns of output file:
%time(ms), angle_sob, v_sobel
ii = 3;
bobOut = zeros(size(angle,1),3);
bobOut(:,1) = angle(:,3,ii)*delt; %time
bobOut(:,2) = angle(:,1,ii); %angle
bobOut(:,3) = angle(:,9,ii); %vel

%this gives us yyyymmddhhmmss
datetime = sprintf('%02d', fix(clock));

%outFileName = [inputimg '.' datetime '.out'];
outFileName = inputimg(1:length(inputimg)-4); % strip off .tif
% abb, removed _l, for Olympus we only ever have one line per tif
%outFileName = [outFileName '_l' num2str(lineidx) '_chhatbar' '.txt'];
outFileName = [outFileName '_chhatbar' '.txt'];
disp(['      saving ' outFileName])

fileID = fopen(outFileName, 'w', 'n', 'UTF-8');
    fprintf(fileID, 'originalfile=%s\n', originalfile); % bob's paremeter
    fprintf(fileID, 'channel=%d\n', channel); % bob's paremeter
    fprintf(fileID, 'lineidx=%f\n', lineidx); % bob's paremeter
    fprintf(fileID, 'inputimg=%s\n', inputimg);
    fprintf(fileID, 'inputTif=%s\n', inputTif);
    fprintf(fileID, 'datetime=%s\n', datetime);
    fprintf(fileID, 'delx=%f\n', delx);
    fprintf(fileID, 'delt=%f\n', delt);
    fprintf(fileID, 'hi=%d\n', hi);
    fprintf(fileID, 'lineskip=%d\n', lineskip);
    fprintf(fileID, 'xMin=%f\n', xMin);
    fprintf(fileID, 'xMax=%f\n', xMax);
    fprintf(fileID, 'tmpstack=%s\n', tmpstack);
    fprintf(fileID, 'time,angle,velocity\n');
    for i = 1:size(bobOut,1)
        fprintf(fileID, '%f,%f,%f\n', bobOut(i,1), bobOut(i,2), bobOut(i,3));
    end    
fclose(fileID);
disp('   Done')
disp(' ')