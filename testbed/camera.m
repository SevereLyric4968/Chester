% Camera.m
% Author: Kov Ciuchta
% Take one snapshot from a webcam

global imgRGB;

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
cleanupObj = onCleanup(@() clear('cam'));

imgRGB = snapshot(cam);
tstamp = datestr(now, 'yyyymmdd_HHMMSS');
fname  = sprintf('photo_%04d_%s.png', idx, tstamp);
path   = fullfile(baseFolder, fname);

% Python Integration variable (Double check).
img = path;

% Save snapshot, which is a
imwrite(imgRGB, path);
fprintf('Saved snapshot #%d -> %s\n', idx, fname);

run("centering.m");