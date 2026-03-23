% take_one_photo.m
% Take one snapshot from a webcam and save it to disk.

% Configuration
baseFolder = fullfile("D:\Chester-master\Chester\testbed\image_base_folder\img"); % change as needed
cameraName = 'DroidCam Video';                    % set to your camera name or leave empty to use first

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

% Acquire one snapshot and save
cam = webcam(cameraName);
cleanupObj = onCleanup(@() clear('cam')); % ensure camera cleared on exit

imgRGB = snapshot(cam); % single capture

tstamp = datestr(now, 'yyyymmdd_HHMMSS');
fname  = sprintf('photo_%04d_%s.png', idx, tstamp);
path   = fullfile(baseFolder, fname);

img = path;
imwrite(imgRGB, path);
fprintf('Saved snapshot #%d -> %s\n', idx, fname);