% Centering.m
% Author: Kov Ciuchta
% Full camera control (expand later)
global imgRGB;
%and process_pieces
global fname;


%calibration or off
%mode = "";

%Take Photo

% Variables to look for
baseFolder = fullfile("D:\Chester-master\Chester\testbed\image_base_folder\img"); % change as needed
cameraName = 'DroidCam Video';              % set to your camera name or leave empty to use first

% Ensure output folder exists
if ~isfolder(baseFolder)
    mkdir(baseFolder);
end

% Determine next index from existing files
photoFiles = dir(fullfile(baseFolder, 'photo_*.png'));
startIdx = 1;
if ~isempty(photoFiles)
    names = {photoFiles.name}';
    idxNums = zeros(size(names));
    for k = 1:numel(names)
        tok = regexp(names{k}, '^photo_(\d{4})_', 'tokens', 'once');
        if ~isempty(tok)
            idxNums(k) = str2double(tok{1});
        end
    end
    startIdx = max([idxNums; 0]) + 1;
end
idx = startIdx;

% Take one snapshot with defined camera, make sure the camera is clear after
cam = webcam(cameraName);

imgRGB = snapshot(cam);
tstamp = datestr(now, 'yyyymmdd_HHMMSS');
fname  = sprintf('photo_%04d_%s.png', idx, tstamp);
path   = fullfile(baseFolder, fname);

% Python Integration variable (Double check).
img = path;
imgRGB = imrotate(imgRGB,90);
% Save snapshot, which is a
imwrite(imgRGB, path);
fprintf('Saved snapshot #%d -> %s\n', idx, fname);

cleanupObj = onCleanup(@() clear('cam'));

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
%if mode == "calibration"
%    run("process_board.m");
%end

%make if ~ no board_cal
%       end.
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
test = 123;
disp(test);