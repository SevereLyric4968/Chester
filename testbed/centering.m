% Centering.m
% Author: Kov Ciuchta
% Full camera control (expand later)
global imgRGB;
%and process_pieces
global path;


%calibration or off
%mode = "";
%imgRGB= imread("D:\Chester-master\Chester\testbed\image_base_folder\photo_0008_20260320_125023.png");
%Take Photo
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
pause(1);
imgRGB = snapshot(cam);
tstamp = datestr(now, 'yyyymmdd_HHMMSS');
fname  = sprintf('photo_%04d_%s.png', idx, tstamp);
path   = fullfile(baseFolder, fname);

% Python Integration variable (Double check).
img = path;
imgRGB = imrotate(imgRGB,-90);
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

%new points to compute-stays absolute to the board
pts = [x, y];
sums = x + y;
diffs = x - y;

[~, iTL] = min(sums);   % top-left
[~, iTR] = max(diffs);  % top-right
[~, iBR] = max(sums);   % bottom-right
[~, iBL] = min(diffs);  % bottom-left

corners = pts([iTL, iTR, iBR, iBL], :);  % 4x2 matrix [x, y]

%centre of bounding box
%cx = xmin + w/2;
%cy = ymin + h/2;

%convert centre and side to integer pixel co-ordinates for the square
% top left pixel
%x1 = round(cx - side/2);
%y1 = round(cy - side/2);
%bottom right pixel
%x2 = x1 + side - 1;
%y2 = y1 + side - 1;

%get image size
[mrows,mcols,~] = size(imgRGB);
%prevent the top-left corner from being <1 
% (ifx1/y1 is outside (0), set it to 1
% prevent bottom-rght from exceeding image bounds
%x1 = max(1,x1); y1 = max(1,y1);
%x2 = min(mcols,x2); y2 = min(mrows,y2);

%recompute actual cropsize aftr clipping
%w_clip = x2 - x1 + 1;
%h_clip = y2 - y1 + 1;

%make a new image that is cropped to the board
% selects image rows, image columns, and all colour channels
% indexing is 1-based and inclusive
srcPoints = corners;  % [x,y] for TL, TR, BR, BL

%use all 4 corners to compute bounds
W = round(max(norm(corners(1,:)-corners(2,:)), norm(corners(4,:)-corners(3,:))));
H = round(max(norm(corners(1,:)-corners(4,:)), norm(corners(2,:)-corners(3,:))));

%compute difstance between
padding = 15; % pixels to crop inward on each side, adjust as needed

dstPoints = [1+padding, 1+padding; 
             W-padding, 1+padding; 
             W-padding, H-padding; 
             1+padding, H-padding];

%build perspective transform and apply
tform = fitgeotrans(srcPoints, dstPoints, 'projective');
cropped = imwarp(imgRGB, tform, 'OutputView', imref2d([H, W]));
title = 'cropped.png';
fname = fullfile('D:\Chester-master\Chester\testbed\image_base_folder\img\',title);
imwrite(cropped, fname);
figure; imshow(imgRGB); hold on;

%close shape by appending the first point at the end
cx_pts = corners([1,2,3,4,1], 1);
cy_pts = corners([1,2,3,4,1], 2);

%print for testing
plot(cx_pts, cy_pts, 'g-', 'LineWidth', 2);
plot(corners(:,1), corners(:,2), 'ro', 'MarkerSize', 8, 'LineWidth', 2);

%if running for the first time, remind user to run process_board.m
if isfile('board_calibration.mat')
    %update the image co-ordinates to board_adjusted (new file)
    S = load("board_calibration.mat");
    board_dictionary = S.board_dictionary;
    all_keys = board_dictionary.keys;

    for i = 1:numel(all_keys)
        current_key = all_keys(i);
        val_cell = board_dictionary(current_key); %cell array
        coords = val_cell{1}; % Unpack the cell to get [X, Y] 
        [X, Y] = transformPointsInverse(tform, coords(:,1), coords(:,2));
        plot(X, Y, 'ro', 'MarkerSize', 8, 'LineWidth', 1.5);
        fprintf('square %s: [X: %8.2f, Y: %8.2f]\n', current_key, coords(1), coords(2));
        val_cell{1} = [X(:), Y(:)];
        board_dictionary(current_key) = val_cell;
    end
    save("D:\Chester-master\Chester\testbed\board_adjusted.mat", 'board_dictionary');
else
    print("No calibration file found. Please run process_board.m on an empty board.")
end

if isfile('storage_calibration.mat')
    %update the image co-ordinates to board_adjusted (new file)
    S = load("storage_calibration.mat");
    storage_dictionary = S.storage_dictionary;
    all_keys = storage_dictionary.keys;

    for i = 1:numel(all_keys)
        current_key = all_keys(i);
        val_cell = storage_dictionary(current_key); %cell array
        coords = val_cell{1}; % Unpack the cell to get [X, Y] 
        [X, Y] = transformPointsInverse(tform, coords(:,1), coords(:,2));
        plot(X, Y, 'ro', 'MarkerSize', 8, 'LineWidth', 1.5);
        fprintf('square %s: [X: %8.2f, Y: %8.2f]\n', current_key, coords(1), coords(2));
        val_cell{1} = [X(:), Y(:)];
        storage_dictionary(current_key) = val_cell;
    end
    save("D:\Chester-master\Chester\testbed\storage_adjusted.mat", 'storage_dictionary');
else
    print("No calibration file found. Please run process_board.m on an empty board.")
end