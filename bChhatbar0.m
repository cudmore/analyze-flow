function [angle,utheta,uvar] = bChhatbar0(inputimg,showimg,saveimg,delx,delt,hi,lineskip,xrange)

%
% Robert Cudmore modified version of the original
%
% Blood velocity measurement on linescan images based on the paper titled:
% Improved blood velocity measurements with a hybrid image filtering and 
% iterative Radon transform algorithm
% published in:
% Frontiers in Brain Imaging Methods / Frontiers in Neuroscience
% 
% Syntax:
% [angle,utheta,uvar] = hybridvel(inputimg,showimg,saveimg,delx,delt,hi,lineskip,xrange)
% 
% Where,
% inputimg = linescan/space-time image with space in X-axis and time in Y-axis
% showimg = display image comparing the effect of elementwise demeaning,
%   vertical demeaning and 3x3 vertical Sobel filtering
% saveimg = save image in various formats (.fig,.jpg,.eps,.ai)
% delx = DeltaX, microns/pixel
% delt = DeltaT, ms/line
% hi = height of image segment to be processed in pixels
% lineskip = number of lines before next image segment starts
% xrange = 2-element vector specifying range of pixels in space-dimension
%   to use in the image segment
% 
% Outputs:
% angle: [angle(deg), minstep(deg), location(pixel), dels1(deg), deln(deg), %dv/v, iter, irl, speed (mm/s)]
% utheta: angles used to process the image segments
% uvar: variance on Radon transform at each angle at each image segment
% 
% Example:
% The linescan image used in the Figure 9 of the paper named 'fig9im.tif'
% is located in the same folder as this code. This image can be used as:
% [angle,utheta,uvar] = hybridvel(imread('fig9im.tif'),1,[],0.47,1,100,25,[1 125]);
% 
% by Pratik Chhatbar, Kara Lab @ MUSC Neurosciences
% Charleston, SC. 5/29/2013
% chhatbar@musc.edu
% pratikchhatbar@gmail.com

%% Initialize

imsize = size(inputimg);
inputimg = double(inputimg);
anglineth = 3; 
dvov = 0.1/100; % dv/v to determine minimum step-size
firstthetastep = 45; thetarange = [0 179];
ds = 4; % 4 um streak distance

%if exist('showimg','var') && ~isempty(showimg) && showimg, showimg = 1; else showimg = 0; end
%if exist('saveimg','var') && ~isempty(saveimg) && saveimg, saveimg = 1; showimg = 1; else saveimg = 0; end
if exist('delx','var') && ~isempty(delx) && delx, else delx = 1; end
if exist('delt','var') && ~isempty(delt) && delt, else delt = 1; end
if exist('hi','var') && ~isempty(hi) && hi, else hi = imsize(1)-2; end
if exist('lineskip','var') && ~isempty(lineskip) && lineskip, else lineskip = hi; end
if exist('xrange','var') && ~isempty(xrange) && length(xrange)<3
    if length(xrange)==1
        wi = xrange; xrange = [1 wi];
    else
        if xrange(1)>imsize(2)-1
            xrange(1)=1;
        end
        if xrange(2)>imsize(2)-1
            xrange(2)=imsize(2)-2;
        end
        if xrange(2)<xrange(1)
            xrange = [xrange(1) xrange(2)];
        end
        wi = xrange(2)-xrange(1)+1;
    end
else
    wi = imsize(2)-2; xrange = [1 wi];
end

if showimg
    imgtitle = {inputname(1);['HybridVel-' datestr(now,30)]};
end

%% Process the image with different filters

curimtitle = {'edm','vdm','sob'}; curcolor = {'b','g','k','r','c','m'};
imgseg(:,:,1) = inputimg(2:end-1,2:end-1)-mean(mean(inputimg(2:end-1,2:end-1))); % element-wise demean
imgseg(:,:,2) = bsxfun(@minus,inputimg(2:end-1,2:end-1),...
    mean(inputimg(2:end-1,2:end-1),1)); % vertical demean
imgseg(:,:,3) = filter2([1 2 1; 0 0 0; -1 -2 -1],inputimg,'valid');  % 3x3 vertical Sobel filter, Eq. 5,6

imgsegsz = size(imgseg);
firstiter = (thetarange(1):firstthetastep:thetarange(2));
firstiter = firstiter-(firstiter(end)-firstiter(1))/2+1;

segend = hi:lineskip:imgsegsz(1);
segstart = segend-hi+1;
segn = length(segstart);

angle = nan(segn,9,imgsegsz(3)); % angle = [angle,minstep,loc(pix),dels1,deln,%dv/v,iter,irl,speed(mm/s)]
utheta = cell(segn,imgsegsz(3)); 
uvar = cell(segn,imgsegsz(3));

%% Iterative Radon transform

%for ii = 1:imgsegsz(3)
for ii = 3
    for jj = 1:segn
        irl = 1; % iterative radon level
        curangle = 0; alltheta = []; allvar = []; iter = 0; thetastep = firstthetastep; curvarmax = 0;
        curimgseg = imgseg(segstart(jj):segend(jj),xrange(1):xrange(2),ii);
        if ii==1
            curimgseg = curimgseg-mean(curimgseg(:)); % element-wise demean
        end
        if ii==2
            curimgseg = bsxfun(@minus,curimgseg,mean(curimgseg,1)); % vertical demean
        end
       while irl
            iter = iter+1;
            % smart iterative radon function with graded angle steps
            if iter==1
                theta = firstiter;
            else
                thetastep = thetastep/2;
                theta = (-3*thetastep+curangle):thetastep*2:(3*thetastep+curangle);
            end
            theta = mod(theta+90,180)-90; % ensures angle range of [-90,+90)
            R = radon(curimgseg,theta); % Eq. 7
            R(R==0) = nan; % avoids influence of non-participant pixels
            curvar = nanvar(R);
            alltheta = [alltheta theta];
            allvar = [allvar curvar];
            [Rvarmaxval,Rvarmaxin] = max(curvar);
            if Rvarmaxval>curvarmax
                curangle = theta(Rvarmaxin); % Eq. 8
                curvarmax = Rvarmaxval;
            end
            if irl==1 && thetastep<1 % angle resolution less than 1 deg
                irl=2; % iterative radon level 2, where step-size is decided for given dv/v
                curmpa = abs(atand((dvov+1)*tand(curangle))-curangle); % Eq. 17
                ws = min(wi,ceil(hi*abs(tand(curangle)))); % Eq. 14
                hs = min(hi,ceil(wi*abs(cotd(curangle)))); % Eq. 14
                ns = floor(wi*delx/ds)*(hs==hi)+((hi*delx*ws)/(ds*hs))*(ws==wi); % Eq. 13
                dels1 = abs(atand(ws/hs)-atand((ws-1)/hs)*(ws>hs)-atand(ws/(hs-1))*(ws<=hs)); % Eq. 12
                deln = dels1/ns; % Eq. 11
                
            end
            if irl>1 && thetastep<deln % Eq. 11
                ws = min(wi,ceil(hi*abs(tand(curangle)))); % Eq. 14
                hs = min(hi,ceil(wi*abs(cotd(curangle)))); % Eq. 14
                ns = floor(wi*delx/ds)*(hs==hi)+((hi*delx*ws)/(ds*hs))*(ws==wi); % Eq. 13
                dels1 = abs(atand(ws/hs)-atand((ws-1)/hs)*(ws>hs)-atand(ws/(hs-1))*(ws<=hs)); % Eq. 12
                deln = dels1/ns; % Eq. 11
                if thetastep<deln
                    break
                end
            end
                
            if irl>1 && thetastep<curmpa % Eq. 17
                % actual dv/v calculation
                actdvovper = abs(tand(thetastep+curangle)/tand(curangle)-1)*100; % Eq. 16
                if dvov>actdvovper/100
                    break
                else
                    irl = irl+1;
                    curmpa = atand((dvov+1)*tand(abs(curangle)))-abs(curangle); % Eq. 17
                end
            end
        end
        angle(jj,1,ii) = curangle;

        % actual dv/v 
        actdvovper = abs(tand(thetastep+curangle)/tand(curangle)-1)*100; % Eq. 16
        % deln
        ws = min(wi,ceil(hi*abs(tand(curangle)))); % Eq. 14
        hs = min(hi,ceil(wi*abs(cotd(curangle)))); % Eq. 14
        ns = floor(wi*delx/ds)*(hs==hi)+((hi*delx*ws)/(ds*hs))*(ws==wi); % Eq. 13
        dels1 = abs(atand(ws/hs)-atand((ws-1)/hs)*(ws>hs)-atand(ws/(hs-1))*(ws<=hs)); % Eq. 12
        deln = dels1/ns; % Eq. 11

        angle(jj,2:9,ii) = [thetastep segstart(jj)+hi/2 dels1 deln actdvovper iter irl tand(curangle)*delx/delt];

        % unique angles used for radon and variance measured
        [utheta{jj,ii},um] = sort(alltheta);
        uvar{jj,ii} = allvar(um);
    end
    
    if showimg
        
        figChattbar = figure;
        movegui(figChattbar, [800 300]); % specifies distance from bottom left of screen [x,y] ???
        
        subplot(3,1,1);
        imagesc(imgseg(:,:,ii)');
        
        subplot(3,1,3);
        plot(angle(:,3,ii)*delt,angle(:,9,ii),['-o' curcolor{ii} ]);
        xlabel('time (ms)');
        ylabel('v (mm/s)');
        
        %
        % WAS THIS
       
        %{
        %figure(1496);
        figChattbar = figure;
        movegui(figChattbar, [800 300]); % specifies distance from bottom left of screen [x,y] ???
        
        % linescan plot with angle
        subplot(1,imgsegsz(3)*2,ii+imgsegsz(3));
        imagesc(imgseg(:,:,ii)); axis image; title(curimtitle{ii});
        set(gca,'XTickLabel',[],'YTickLabel',[]);
        hold on;
        for jj=1:segn
        [xp,yp] = pol2cart(mod(angle(jj,1,ii)*pi/180-pi/2,pi),wi/2);
        line(xrange(1)+wi/2+[-xp xp],angle(jj,3,ii)-[-yp yp],'Color','black','LineWidth',anglineth,'EraseMode','xor');
        end
        hold off;
        if ii==1
            ylabel({'processed image';...
                ['\Deltax = ' num2str(delx) ' \mum/pixel' ', \Deltat = ' num2str(delt) ...
                ' ms/line, h = ' num2str(imgsegsz(1)) ' pixels']});
            xlabel(['w = ' num2str(imgsegsz(2))]);
        end
        
        % angle plot
        subplot(2,imgsegsz(3)*2,+(1:imgsegsz(3)))
        plot(angle(:,3,ii)*delt,angle(:,1,ii),['-o' curcolor{ii} ]); hold on;
        if ii==imgsegsz(3)
            legend(curimtitle{ii}); 
            %legend(curimtitle{1:ii}); 
            xlabel('time (ms)'); ylabel('\theta (^o)'); hold off
            title (imgtitle);
        end
            
        ii;
        % velocity plot
        subplot(2,imgsegsz(3)*2,imgsegsz(3)*2+(1:imgsegsz(3)))
        plot(angle(:,3,ii)*delt,angle(:,9,ii),['-o' curcolor{ii} ]); hold on;
        if ii==imgsegsz(3)
            legend(curimtitle{ii}); 
            %legend(curimtitle{1:ii}); 
            xlabel('time (ms)'); ylabel('v (mm/s)'); hold off
        end
        %}
        
        if saveimg && ii==imgsegsz(3)
            savepath = 'D:\lab stuff\savedRadonImages\';
            saveas(gca,fullfile(savepath,['hybridvel' strcat(imgtitle{:}) 'img' num2str(ii) '.eps']), 'psc2');
            saveas(gca,fullfile(savepath,['hybridvel' strcat(imgtitle{:}) 'img' num2str(ii) '.fig']));
            saveas(gca,fullfile(savepath,['hybridvel' strcat(imgtitle{:}) 'img' num2str(ii) '.jpg']));
            saveas(gca,fullfile(savepath,['hybridvel' strcat(imgtitle{:}) 'img' num2str(ii) '.ai']));
        end
        
    end    
end

