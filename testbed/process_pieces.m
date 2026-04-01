close all; clear all; clc;

%load gamesquare coords
data = load('board_calibration.mat');
board_dictionary = data.board_dictionary;
%load storage coords
data = load('storage_calibration.mat');
storage_dictionary = data.storage_dictionary;


fname = ('C:\\Users\\kirst\\chester\\testbed\\image_base_folder\\storage_test\\storage_test_full.jpg');
% read in image
raw_img = imread(fname);
%rotated back to correct orientation 
img = imrotate(raw_img,270);
%use green mask
green_masked_img = green_mask_function(img);

%radius of sticker
radius = 70;

white_piece_centre_coords = [];

%show boundaries labeled in green
[B,L] = bwboundaries(green_masked_img,'noholes');
stats = regionprops(L, 'Centroid', 'Area');
figure,imshow(img);imshow(green_masked_img);
minArea = 400;
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
game_pos_list = board_dictionary.keys;
storage_pos_list = storage_dictionary.keys;

%game occupancy grid - 8x8 1s and 0s
white_game_occupancy = zeros(8,8);

%storage occupancy grid - 1x7 1s and 0s
raw_white_storage_occupancy = zeros(1,7);

for i=1:64
    number_row = floor((i-1)/8) + 1; 
    letter_col = mod(i-1, 8) + 1;


    current_pos = game_pos_list(i);
    square_coord = board_dictionary(current_pos);
    square_xy = square_coord{1}; % unpacks xy coords

    if ~isempty(white_piece_centre_coords)
      euc_distances = sqrt((white_piece_centre_coords(:,1) - square_xy(1)).^2 + (white_piece_centre_coords(:,2) - square_xy(2)).^2);

      if any (euc_distances <=radius)
            white_game_occupancy(number_row,letter_col) = 1;
      end

    end 

end      



%use pink mask
pink_masked_img = pink_mask_function(img);


black_piece_centre_coords = [];

%show boundaries labeled in green
[B,L] = bwboundaries(pink_masked_img,'noholes');
stats = regionprops(L, 'Centroid', 'Area');
figure,imshow(img);imshow(pink_masked_img);
minArea = 300;
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


%occupancy grid - 8x8 1s and 0s
black_game_occupancy = zeros(8,8);

%storage occupancy grid - 1x7 1s and 0s
black_storage_occupancy = zeros(1,7);



for i=1:64
    number_row = floor((i-1)/8) + 1; 
    letter_col = mod(i-1, 8) + 1;


    current_pos = game_pos_list(i);
    square_coord = board_dictionary(current_pos);
    square_xy = square_coord{1}; % unpacks xy coords

    if ~isempty(black_piece_centre_coords)
      euc_distances = sqrt((black_piece_centre_coords(:,1) - square_xy(1)).^2 + (black_piece_centre_coords(:,2) - square_xy(2)).^2);

      if any (euc_distances <=radius)
            black_game_occupancy(number_row,letter_col) = 1;
      end

    end 

end      

storage_radius = 90;

for i=1:7
      number_row = floor((i-1)/7) + 1;
      current_pos = storage_pos_list(i);
      square_coord = storage_dictionary(current_pos);
      square_xy = square_coord{1}; %unpacks xy coords

      if ~isempty(white_piece_centre_coords)
      euc_distances = sqrt((white_piece_centre_coords(:,1) - square_xy(1)).^2 + (white_piece_centre_coords(:,2) - square_xy(2)).^2);

            if any (euc_distances <=storage_radius)
                  raw_white_storage_occupancy(1,i) = 1;
            end

      end 

end

%flip white storage for jay
white_storage_occupancy = flip(raw_white_storage_occupancy);

for i=8:14
      number_row = floor((i-1)/7) + 1;
      current_pos = storage_pos_list(i);
      square_coord = storage_dictionary(current_pos);
      square_xy = square_coord{1}; %unpacks xy coords

      if ~isempty(black_piece_centre_coords)
      euc_distances = sqrt((black_piece_centre_coords(:,1) - square_xy(1)).^2 + (black_piece_centre_coords(:,2) - square_xy(2)).^2);

            if any (euc_distances <=storage_radius)
                  black_storage_occupancy(1,i-7) = 1;
            end

      end 

end







figure, imshow(img); hold on;
for i = 1:64
    center = board_dictionary(game_pos_list(i));
    xy = center{1};
    % Draw a circle for the radius
    viscircles(xy, radius, 'Color', 'b', 'LineWidth', 1);
end

for i = 1:numel(storage_pos_list)
    center = storage_dictionary(storage_pos_list(i));
    xy = center{1};
    viscircles(xy, storage_radius, 'Color', 'm', 'LineWidth', 1); % Magenta for storage
end



disp(white_game_occupancy);
disp(black_game_occupancy);

disp(white_storage_occupancy);
disp(black_storage_occupancy);