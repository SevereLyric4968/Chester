% Camera.m
% Author: Kov Ciuchta
% Keep the board co-ordinates in same position as irl board
global cropped;
global imgRGB;
global fname;

%imgRGB = imread("D:\Chester-master\Chester\testbed\image_base_folder\img\photo_0011_20260325_164923.png");

%calibration or off
mode = "off";

%Detect the orange corners and apply a bounding box
% run hsv mask on image
orange = create_orange_mask(imgRGB);

%apply mask to extract the orange regions from the image
% orange = logical mask 
% row (y) and column (x) (in pixels)
extractedOrange = bsxfun(@times, imgRGB, cast(orange, 'like', imgRGB));
[y,x] = find(orange);
if isempty(x)
    error('No orange pixels found.');
end

%left, right
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
% top left pixel
x1 = round(cx - side/2);
y1 = round(cy - side/2);
%bottom right pixel
x2 = x1 + side - 1;
y2 = y1 + side - 1;

%get image size
[mrows,mcols,~] = size(imgRGB);
%prevent the top-left corner from being <1 
% (ifx1/y1 is outside (0), set it to 1
% prevent bottom-rght from exceeding image bounds
x1 = max(1,x1); y1 = max(1,y1);
x2 = min(mcols,x2); y2 = min(mrows,y2);

%recompute actual cropsize aftr clipping
w_clip = x2 - x1 + 1;
h_clip = y2 - y1 + 1;

%make a new image that is cropped to the board
% selects image rows, image columns, and all colour channels
% indexing is 1-based and inclusive
cropped = imgRGB(y1:y2, x1:x2,:);
J = cropped;  % pos in data units
sJ = size(J);
title = 'cropped.png';
%------Edit for ChesterIMG bed later
fname = fullfile('D:\Chester-master\Chester\testbed\image_base_folder\img\',title);
imwrite(cropped, fname);
figure; imshow(imgRGB); hold on;
rectangle('Position',[x1,y1,side,side],'EdgeColor','g','LineWidth',2);

%if running for the first time, make sure to get base co-ordinates.
if mode == "calibration"
    run("process_board.m");
end

%update the image co-ordinates to board_adjusted (new file)
S = load("board_calibration.mat");
board_dictionary = S.board_dictionary;
all_keys = board_dictionary.keys;

for i = 1:numel(all_keys)
    current_key = all_keys(i);
    val_cell = board_dictionary(current_key); %cell array
    coords = val_cell{1}; % Unpack the cell to get [X, Y] 
    X = x1 + coords(:,1) - 1;
    Y = y1 + coords(:,2) - 1;
    plot(X, Y, 'ro', 'MarkerSize', 8, 'LineWidth', 1.5);
    fprintf('square %s: [X: %8.2f, Y: %8.2f]\n', current_key, coords(1), coords(2));
    val_cell{1} = [X(:), Y(:)];
    board_dictionary(current_key) = val_cell;
end

save("D:\Chester-master\Chester\testbed\board_adjusted.mat", 'board_dictionary');