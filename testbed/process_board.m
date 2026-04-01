close all;

global cropped

raw_img = cropped;
%rotated back to correct orientation 
img = imrotate(raw_img,0);
% convert to greyscale
grey_img = rgb2gray(img);
% gaussian blurring filter
%kirsty images =  20
gauss_img = imgaussfilt(grey_img,1);
% canny edge detection
canny_img = edge(gauss_img,'Canny');
%dialate edges
%kirsty images = 15
se = strel('square', 5);
dialated_edges = imdilate(canny_img, se);
imshow(dialated_edges);
% fill holes
holes_filled = imfill(dialated_edges,"holes");
%disregard big board
squares_only = holes_filled & ~dialated_edges;
double = im2double(canny_img);

%initialise square coords array
square_coords = [];


%show boundaries labeled in green
[B,L] = bwboundaries(squares_only,'noholes');
stats = regionprops(L, 'Centroid', 'Area');
%org value = 10000;
%org value 1000000000;
minArea = 300;
maxArea = 50000;
figure;
imshow(gauss_img)
imshow(label2rgb(L, @jet, [.5 .5 .5]));
imshow(img);
hold on;
for k = 1:length(B)
   if stats(k).Area>minArea && stats(k).Area<maxArea
      boundary = B{k};
      plot(boundary(:,2), boundary(:,1), 'g', 'LineWidth', 2)
      centroid = stats(k).Centroid;
      plot(centroid(1), centroid(2), 'r*', 'MarkerSize', 10, 'LineWidth', 2);
      %fill in square coords
      square_coords = [square_coords; centroid];
   end
end

%[ginput_x, ginput_y] = ginput(1);

%apply yellow mask to detect sticker
yellow_mask = yellow_mask_function(img);

biggest_yellow = bwpropfilt(logical(yellow_mask), 'Area', 1);

%find centroid of yellow sticket
yellow_centroid = regionprops(biggest_yellow, 'Centroid');
%extract x and y vals of the centroid
topleft_x = yellow_centroid(1).Centroid(1);
topleft_y = yellow_centroid(1).Centroid(2);



% make dictionary to associate 
letters = {'a','b','c','d','e','f','g', 'h'};
numbers = {'8','7','6','5','4','3','2', '1'};
spacing = 28;
keys = strings(64,1);
pairs = cell(64,1);
i=1;
%sort coords
for num = 1:8
    for let = 1:8
        %calculate projection from that square
        x = topleft_x + ((let-1) * spacing);
        y = topleft_y + ((num-1) * spacing);
        plot(x, y, 'yo', 'MarkerSize', 5);

        %create the key for that square
        keys(i) = string([letters{let}, numbers{num}]);

        if num == 1 && let == 1
            pairs{i} = [topleft_x, topleft_y];

        else

            %find which centroid coord is closest
            dists = sqrt((square_coords(:,1) - x).^2 + (square_coords(:,2) - y).^2);
            [min_dist,idx]=min(dists);

            %if the closest centroid is less than half a square away (with tolerance built into spacing val)
            if min_dist<spacing/2
                %detect this as the next square
                pairs{i} = square_coords(idx, :);
            else
                error('Calibration failed');
            end
        end

        %increment i
        i = i + 1;
    end
end


%create coordinate dictionary
board_dictionary = dictionary(keys, pairs);
save('board_calibration.mat', 'board_dictionary');

all_keys = board_dictionary.keys;

%%%% STORAGE TIME :))))))
%mask to detect storage left
%colour_mask = colour_mask_function(img);
%identify two biggest hits of that colour
%biggest_colour = bwpropfilt(logical(colour_mask), 'Area', 2);
%get their centrepoints
%colour_centroids = regionprops(biggest_colour, 'Centroid');
%turn them into a 2d, horizontal array
%centroids = cat(1, colour_centroids.Centroid);
%sort by increasing x coords
%[~, sortIdx] = sort(centroids(:,1));
%left_storage_marker = centroids(sortIdx(1), :);
%right_storage_marker = centroids(sortIdx(2), :);

% make dictionary to associate 
%side = {'L','R'};
%row = {'8','7','6','5','4','3','2', '1'};
%s_keys = strings(14,1);
%s_pairs = cell(14,1);
%s_idx = 1;

%markers = [left_storage_marker; right_storage_marker];

%for s = 1:2
%    marker_x = markers(s, 1);
%    marker_y = markers(s, 2);
    
%    for r = 1:7
        % Calculate vertical projection downwards
%       x = marker_x;
%        y = marker_y + ((r-1) * spacing);
%       plot(x, y, 'g', 'MarkerSize', 5);

%        s_keys(s_idx) = string([side{s},row{r}] );

         %find which centroid coord is closest
%            dists = sqrt((square_coords(:,1) - x).^2 + (square_coords(:,2) - y).^2);
%            [min_dist,idx]=min(dists);

            %if the closest centroid is less than half a square away (with tolerance built into spacing val)
 %           if min_dist<spacing/2
                %detect this as the next square
 %               pairs{i} = square_coords(idx, :);
 %           else
  %              error('Calibration failed');
   %         end

        %increment s_idx
    %z    s_idx = s_idx + 1;

    %end

%end

%create and save storage dict
%storage_dictionary = dictionary(s_keys, s_pairs);
%save('storage_calibration.mat', 'storage_dictionary');




fprintf('\nall chessboard coords:\n');
for i = 1:numel(all_keys)
    current_key = all_keys(i);
    val_cell = board_dictionary(current_key);
    coords = val_cell{1}; % Unpack the cell to get [X, Y]
    
    %print in a readable format
    fprintf('square %s: [X: %8.2f, Y: %8.2f]\n', current_key, coords(1), coords(2));
end
