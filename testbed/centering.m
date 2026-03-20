%close all; clear all; clc;

%THINGS TO DO:
%1. make the final photo a (2000x2000) pixel grid that the checkerboard
%proportionally maps to as a better co-ordinate system
%2. make a function that deletes the oldest photos to declutter the workspace

global fname %global variable that tracks final image
global img %global variable that tracks camera snapshot


I = imread(img);
[imagePoints, boardSize, imagesUsed] = detectCheckerboardPoints(I);

if isempty(imagePoints)
    disp('No checkerboard detected.');
else
    % Compute convex hull of interior corner points
    xs = imagePoints(:,1);
    ys = imagePoints(:,2);
    valid = isfinite(xs) & isfinite(ys);
    xs = xs(valid); ys = ys(valid);
    k = convhull(xs, ys);        % k includes repeated first/last index
    hullPts = imagePoints(k(1:end-1), :); % remove duplicate last vertex

    % If hull already has 4 points use them; otherwise pick 4 extreme points
    if size(hullPts,1) == 4
        outerPts = hullPts;
    else
        s1 = hullPts(:,1) + hullPts(:,2);   % x+y  -> top-left / bottom-right extremes
        s2 = -hullPts(:,1) + hullPts(:,2);  % -x+y -> top-right / bottom-left extremes

        [~, idx_tl] = min(s1); % top-left (approx)
        [~, idx_br] = max(s1); % bottom-right (approx)
        [~, idx_tr] = min(s2); % top-right (approx)
        [~, idx_bl] = max(s2); % bottom-left (approx)

        outerPts = unique([hullPts(idx_tl,:); hullPts(idx_tr,:); hullPts(idx_br,:); hullPts(idx_bl,:)], 'rows', 'stable');

        % If uniqueness reduced below 4 (degenerate), fallback to hull extremes
        if size(outerPts,1) < 4
            % pick hull points with min/max x and min/max y
            [~, ixmin] = min(hullPts(:,1));
            [~, ixmax] = max(hullPts(:,1));
            [~, iymin] = min(hullPts(:,2));
            [~, iymax] = max(hullPts(:,2));
            outerPts = unique([hullPts(ixmin,:); hullPts(ixmax,:); hullPts(iymin,:); hullPts(iymax,:)], 'rows', 'stable');
        end

        % If still not 4, use entire hull bounding box
        if size(outerPts,1) < 4
            outerPts = [min(hullPts); max(hullPts)]; % yields 2 rows only; will handle below
        end
    end

    % Compute bounding box from outer points
    xMin = min(outerPts(:,1));
    xMax = max(outerPts(:,1));
    yMin = min(outerPts(:,2));
    yMax = max(outerPts(:,2));

    % Fixed padding
    pad = 100;
    x1 = floor(xMin - pad);
    y1 = floor(yMin - pad);
    x2 = ceil(xMax + pad);
    y2 = ceil(yMax + pad);

    % Clamp to image bounds
    [imgH, imgW, ~] = size(I);
    x1 = max(1, x1);
    y1 = max(1, y1);
    x2 = min(imgW, x2);
    y2 = min(imgH, y2);

    % Width and height for display / cropping
    w = x2 - x1 + 1;
    h = y2 - y1 + 1;

    % Show original with rectangle
    %figure; imshow(I); hold on;
    %rectangle('Position', [x1, y1, w, h], 'EdgeColor', 'g', 'LineWidth', 2);
    %title(sprintf('Detected checkerboard outer bounding box (pad=%d)', pad));

    % Crop using indexing
    im = I(y1:y2, x1:x2, :);
    %figure out rotation: quick fix VVV
    %im = imrotate(cropped,-90);
    %figure; imshow(im); title('Cropped checkerboard (outer corners + padding)');

    %exporting as image
    baseFolder = fullfile("D:\Chester-master\Chester\testbed\image_base_folder\fname"); % base directory
    fname = sprintf('cropped_%s.png', datestr(now,'yyyymmdd_HHMMSS'));
    exportgraphics(gcf, fullfile(baseFolder,fname), 'BackgroundColor','none');
    %disp(['Saved: ', fullfile(pwd,fname)]);

    %TODO: return filepath into vision_interface.py

end
