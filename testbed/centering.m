fname = 'D:\Chester-master\Chester\testbed\image_base_folder\photo_0001_20260320_124838.png';

imgRGB = imread(fname);

% run hsv mask on image
orange = create_orange_mask(imgRGB);

% apply mask to extract the orange regions from the image
extractedOrange = bsxfun(@times, imgRGB, cast(orange, 'like', imgRGB));

% orange = logical mask 
% retyrbs row and column (in pixels)
[y,x] = find(orange);             % row (y), col (x) (this might be wrong??
if isempty(x)
    error('No orange pixels found.');
end

% left, right
xmin = min(x); xmax = max(x);
%top, bottom indicies
ymin = min(y); ymax = max(y);
%width and height
w = xmax - xmin + 1;
h = ymax - ymin + 1;
%sides
side = max(w,h);

%centre of bounding box
cx = xmin + w/2;
cy = ymin + h/2;

%convert centre and side to integer pixel co-ordinates for the square
%top left pixel
x1 = round(cx - side/2);
y1 = round(cy - side/2);
%bottom right pixel
x2 = x1 + side - 1;
y2 = y1 + side - 1;

%clip to image

%get image size
[mrows,mcols,~] = size(imgRGB);
%prevent the top-left corner from being <1 
% (ifx1/y1 is outside (0), set it to 1
%prevent bottom-rght from exceeding image bounds
x1 = max(1,x1); y1 = max(1,y1);
x2 = min(mcols,x2); y2 = min(mrows,y2);

%recompute actual cropsize aftr clipping
w_clip = x2 - x1 + 1;   % actual width after clipping
h_clip = y2 - y1 + 1;   % actual height after clipping

% Ensure extractedOrange is a uint8/uint16/float in [0,1] as required
% If mask is logical and imgRGB is uint8:
imwrite(imgRGB, 'extractedOrange.png');   % PNG keeps colors/lossless

%visualise boundary box
%imshow(imgRGB); hold on;
%rectangle('Position',[x1,y1,x2-x1+1,y2-y1+1],'EdgeColor','g','LineWidth',2);
%title('Axis-Aligned Square');
%hold off;

%crop around that boundary box
cropped = imgRGB(y1:y2, x1:x2,:); 

title = 'cropped.png';
fname = fullfile('D:\Chester-master\Chester\testbed\image_base_folder', title);
imwrite(cropped, fname);
%see the cropped image
imshow(cropped);

%uncomment if you want to run process_board immediately
%make sure global fname can be read by process_board
%run("process_board.m");
