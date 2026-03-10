close all; clear all; clc;

data = load('board_calibration.mat');
board_dictionary = data.board_dictionary;

% read in image
raw_img = imread('C:\Users\kirst\chess-vision\images\green pieces\starting.jpg');
%rotate
img=imrotate(raw_img,-90);
%use pink mask
pink_masked_img = pink_mask_function(img);

%radius of sticker
radius = 170;

white_piece_centre_coords = [];

%show boundaries labeled in green
[B,L] = bwboundaries(pink_masked_img,'noholes');
stats = regionprops(L, 'Centroid', 'Area');
figure,imshow(img);imshow(pink_masked_img);
minArea = 500;
hold on;
for k = 1:length(B)
      if stats(k).Area>minArea
            boundary = B{k};
            plot(boundary(:,2), boundary(:,1), 'g', 'LineWidth', 2)
            centroid = stats(k).Centroid;
            plot(centroid(1), centroid(2), 'r*', 'MarkerSize', 10, 'LineWidth', 2);
            %fill in square coords
            white_piece_centre_coords = [white_piece_centre_coords; centroid];
      end
end

%list of square names
pos_list = board_dictionary.keys;

%occupancy grid - 8x8 1s and 0s
raw_white_occupancy_grid = zeros(8,8);


for i=1:64
    number_row = mod(i-1, 8) + 1;
    letter_col = floor((i-1)/8) + 1;


    current_pos = pos_list(i);
    square_coord = board_dictionary(current_pos);
    square_xy = square_coord{1}; % unpacks xy coords

    if ~isempty(white_piece_centre_coords)
      euc_distances = sqrt((white_piece_centre_coords(:,1) - square_xy(1)).^2 + (white_piece_centre_coords(:,2) - square_xy(2)).^2);

      if any (euc_distances <=radius)
            raw_white_occupancy_grid(number_row,letter_col) = 1;
      end

    end 

end      



%use green mask
green_masked_img = green_mask_function(img);


black_piece_centre_coords = [];

%show boundaries labeled in green
[B,L] = bwboundaries(green_masked_img,'noholes');
stats = regionprops(L, 'Centroid', 'Area');
figure,imshow(img);imshow(green_masked_img);
minArea = 500;
hold on;
for k = 1:length(B)
      if stats(k).Area>minArea
            boundary = B{k};
            plot(boundary(:,2), boundary(:,1), 'g', 'LineWidth', 2)
            centroid = stats(k).Centroid;
            plot(centroid(1), centroid(2), 'r*', 'MarkerSize', 10, 'LineWidth', 2);
            %fill in square coords
            black_piece_centre_coords = [black_piece_centre_coords; centroid];
      end
end

%list of square names
pos_list = board_dictionary.keys;

%occupancy grid - 8x8 1s and 0s
raw_black_occupancy_grid = zeros(8,8);



for i=1:64
    number_row = mod(i-1, 8) + 1;
    letter_col = floor((i-1)/8) + 1;


    current_pos = pos_list(i);
    square_coord = board_dictionary(current_pos);
    square_xy = square_coord{1}; % unpacks xy coords

    if ~isempty(black_piece_centre_coords)
      euc_distances = sqrt((black_piece_centre_coords(:,1) - square_xy(1)).^2 + (black_piece_centre_coords(:,2) - square_xy(2)).^2);

      if any (euc_distances <=radius)
            raw_black_occupancy_grid(number_row,letter_col) = 1;
      end

    end 

end      







figure, imshow(img); hold on;
for i = 1:64
    center = board_dictionary(pos_list(i));
    xy = center{1};
    % Draw a circle for the radius
    viscircles(xy, radius, 'Color', 'b', 'LineWidth', 1);
end
%plot(piece_centre_coords(:,1), piece_centre_coords(:,2), 'r*', 'MarkerSize', 10);

%rotate grids
black_occupancy_grid = raw_black_occupancy_grid.';
white_occupancy_grid = raw_white_occupancy_grid.';


disp(white_occupancy_grid);
disp(black_occupancy_grid);