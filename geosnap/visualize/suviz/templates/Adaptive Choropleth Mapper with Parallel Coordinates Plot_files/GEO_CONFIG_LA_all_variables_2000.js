// Define the number of maps that you want to visualize. upto 15 maps are supported.
var NumOfMaps = 6;

//Define variables that you want to visualize at initial views. For example, enter five variables when the NumOfMaps is equal to 5.

//var InitialLayers = [ "2000 % in poverty, families with children", "2000 % in poverty, whites", "2000 % in poverty, African Americans", "2000 % in poverty, Hispanics", "2000 % in poverty, Native Americans", "2000 % in poverty, Asian/ Pacific Islanders"];
//var InitialLayers = ["2000 % white, non-Hispanic", "2000 % black, non-Hispanic", "2000 % Hispanic", "2000 % Native American race", "2000 % Asian and Pacific Islander race", "2000 % Hawaiian race", "2000 % Indian birth/race", "2000 % Chinese birth/race", "2000 % Filipino birth/race", "2000 % Japanese birth/race", "2000 % Korean birth/race", "2000 % Vietnamese race", "2000 % 15 and under, non-Hispanic black", "2000 % 60 and older, non-Hispanic black", "2000 % 15 and under, Hispanic", "2000 % 60 and older, Hispanic", "2000 % 15 and under, Native American", "2000 % 60 and older, Native American", "2000 % 15 and under, Asian/  Pacific Islanders", "2000 % 60 and older, Asian/  Pacific Islanders", "2000 % Mexican birth/ethnicity", "2000 % Cuban birth/ethnicity", "2000 % Puerto Rican birth/ethnicity", "2000 % Russian/USSR parentage/ancestry", "2000 % Italian parentage/ancestry", "2000 % German parentage/ancestry", "2000 % Irish parentage/ancestry", "2000 % Scandinavian parentage/ancestry", "2000 % foreign born", "2000 % immigrated in past 10 years", "2000 % Naturalized", "2000 % speaking other language at home, age 5+", "2000 % speaking English not well, age 5+", "2000 % Russian/USSR birth", "2000 % Italian birth", "2000 % German birth", "2000 % Irish birth", "2000 % Scandinavian birth", "2000 % with high school degree or less", "2000 % with 4-year college degree or more", "2000 % unemployed", "2000 % female labor force participation", "2000 % professional employees", "2000 % manufacturing employees", "2000 % self-employed", "2000 % veteran", "2000 % with disability", "2000 Median HH income, total", "2000 Median HH income, whites", "2000 Median HH income, blacks", "2000 Median HH income, Hispanics", "2000 Median HH income, Asian/ Pacific Islanders", "2000 Per capita income", "2000 % in poverty, total", "2000 % in poverty, 65+", "2000 % in poverty, families with children", "2000 % in poverty, whites", "2000 % in poverty, African Americans", "2000 % in poverty, Hispanics", "2000 % in poverty, Native Americans", "2000 % in poverty, Asian/ Pacific Islanders", "2000 % vacant units", "2000 % owner-occupied units", "2000 % multi-family units", "2000 Median home value", "2000 Median rent", "2000 % structures more than 30 years old", "2000 % HH in neighborhood 10 years or less", "2000 % 17 and under, total", "2000 % 60 and older, total", "2000 % 75 and older, total", "2000 % currently married, not separated", "2000 % widowed, divorced and separated", "2000 % female-headed families with children"];

//var InitialLayers = [ "2000 % white, non-Hispanic", "2000 % black, non-Hispanic", "2000 % Hispanic", "2000 % Native American race", "2000 % Asian and Pacific Islander race", "2000 % Korean birth/race"];

/*Define initial map center and zoom level below. Map Extent and Zoom level will be automatically adjusted when you do not define map center and zoom level. Double-slashes  in the front need to be deleted to make them effective*/
var Initial_map_center = [34.1, -118.1];  
var Initial_map_zoom_level = 8;

/* It shows the change in the number of polygons belonging to each class intervals in different 
   It appears only when the map extent and the class intervals of all maps are same.
   To make all maps have the same map extent and class intervals, enable "Grouping All" or click "Sync" on one of maps   */
var Stacked_Chart = false;                                  // true or false

// The number of digit after the decial point.
var Num_Of_Decimal_Places = 1;                             // default = 1 

//Adjust the size of maps
var Map_width  = "350px";                                  // min 350px
var Map_height  = "300px";                                  // min 300px

//Adjust the size of the stacked chart. Double-slashes in the front need to be deleted to make them effective
//var Chart_width  = "350px";                                // min 350px
//var Chart_height = "350px";                                // min 300px


