fname = "D:\Chester-master\Chester\testbed\image_base_folder\photo_0008_20260320_125023.png"

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


%make a new image that is cropped to the board

%selects image rows, image columns, and all colour channels
%indexing is 1-based and inclusive
cropped = imgRGB(y1:y2, x1:x2,:);
J = cropped;  % pos in data units
sJ = size(J);
fname = 'cropped.png'
img = fullfile('D:\Uni\Masters Project\photos',fname);
exportgraphics(gcf, img, 'BackgroundColor','none');
disp(img);

%now: save snapshot co-ordinates to a variable placeholder.
currentPoints = [x1 y1; x2 y2];

fn = "previousPoints.mat";
thresh = 0; % pixels

if isfile(fn)
    S = load(fn, "previousPoints");
    if isfield(S, "previousPoints")
        previousPoints = S.previousPoints;
    else
        previousPoints = [];
    end
    
    if isempty(previousPoints)         % fallback if file existed but var missing
        previousPoints = currentPoints;
        save(fn, "previousPoints");
        fprintf("Saved initial coordinates.\n");
    else
        %per-point Euclidean distance
        currentPoints = ensurePointsForm(currentPoints);
        previousPoints = ensurePointsForm(previousPoints);
        dists = sqrt(sum((currentPoints - previousPoints).^2, 2)); % 2x1
        %compare the co-ordinates to the ones previous
        %if mis-aligned by more than 5 pixels, compute the difference and save the
        %new co-ordinates.
        if any(dists > thresh)
            delta = currentPoints - previousPoints;
            previousPoints = currentPoints;
            save(fn, "previousPoints");
            fprintf("Alignment changed. Delta = [%g %g; %g %g]\n", delta.');
        else
            fprintf("Alignment within %d pixels; no change.\n", thresh);
        end
    end
else
    %save on first run
    previousPoints = currentPoints;
    save(fn, "previousPoints");
    fprintf("Saved initial coordinates: [%g %g; %g %g]\n", previousPoints.');
end

%ensures that previousPoints is stored as a 2x2 matrix
function pts = ensurePointsForm(pts)
    pts = squeeze(pts);
    if isvector(pts) && numel(pts) == 4
        pts = reshape(pts, 2, 2)';
    elseif isequal(size(pts), [2,2])
        % already correct
        disp("already 2x2");
    else
        error('Points must be 1x4 or 2x2 (rows = [x y]).');
    end
end

run("process_board.m");

% Co-ordinate mapping
S = load('board_calibration.mat');
vars = fieldnames(S);
if isempty(vars)
    error('No variables found in the MAT file.');
end

raw = S.(vars{1});

coords = [];

v_all = values(raw);

for k = 1:numel(v_all)
    v = v_all{k};
    if iscell(v)
        vv = v{1};
        if isnumeric(vv) && size(vv, 2) == 2
            coords = [coords; vv];
        end
    elseif isnumeric(v) && size(v, 2) == 2
        coords = [coords; v];
    end
end

if isempty(coords)
    error('Could not extract coordinates from file.');
end

%map to image space
isNormalized = all(coords(:) >= 0 & coords(:) <= 1);
if isNormalized
    disp("normalised");
    gx = x1 + coords(:,1)*(side-1);
    gy = y1 + coords(:,2)*(side-1);
else
    disp("coords");
    gx = x1 + coords(:,1) - 1;
    gy = y1 + coords(:,2) - 1;
end

%keep points inside the rectangle bounds
inside = gx >= x1 & gx <= x1+side-1 & gy >= y1 & gy <= y1+side-1;
gx = gx(inside);
gy = gy(inside);

%co-ordinate updating HERE VV
%For some reason i am having a lot of trouble
%writing the co-ordinates back to board_calibration.mat...
%giving up for now, will try again tomorrow.