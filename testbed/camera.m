
close all; clear all; clc;
global fname %global variable that tracks final image
global img %global variable that tracks camera snapshot

% debugging purposes: list available cameras
disp('Available webcams:');
camNames = webcamlist;
disp(camNames);

% Create webcam object
cam = webcam('DroidCam Video');

% Output folders (change paths if needed)
baseFolder = fullfile("D:\Chester-master\Chester\testbed\image_base_folder\img"); % base directory

% Initialize counters (scan existing files to continue numbering)
photoFiles = dir(fullfile(baseFolder, '*.png'));
startIdx = max([numel(photoFiles)]) + 1;
idx = startIdx;

fprintf('Ready. Press Enter to take a snapshot, type q and press Enter to quit.\n');

while true
    userIn = input('> ', 's'); % waits for Enter (returns ''), or typed text
    if strcmpi(userIn, 'q')
        disp('Quitting.');
        break;
    end

    % Capture snapshot
    stereo = snapshot(cam); % RGB image



    % Create filenames with index and timestamp
    tstamp = datestr(now, 'yyyymmdd_HHMMSS');
    name  = sprintf('photo_%04d_%s.png',  idx, tstamp);

    path  = fullfile(baseFolder,  name);
    img = path;
    disp(img);

    % Save files
    imwrite(stereo, path);

    fprintf('Saved #%d -> %s and %s\n', idx, name);

    idx = idx + 1;
end

% NESSECARY FOR MATLAB INTEGRATION
function print_image_path()
    fprintf('%s\n', img);
end

print_image_path();

% Clean up
clear cam;
disp('Camera cleared.');

%cropping time%
%run("centering.m");
exit