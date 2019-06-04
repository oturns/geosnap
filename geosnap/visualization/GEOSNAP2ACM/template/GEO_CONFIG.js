// Define the number of maps that you want to visaulize. Upto 15 maps are supported.

var NumOfMaps = 1;

var InitialLayers = [];

/* Map Extent and Zoom level will be automatically adjusted when you do not define map center and zoom level */
//var Initial_map_center = [34.0522, -117.9];  
//var Initial_map_zoom_level = 8;   

/* It shows the change of number of polygons belonging to each class intervals 
   It appears only when the map extent and the class intervals of all maps are same.
   To make all maps have the same map extent and class intervals, enable "Grouping All" or click "Sync" on each of maps   */
var Stacked_Chart = true;                                  // true or false

var Num_Of_Decimal_Places = 4;                             // default = 1 

var Map_width  = "400px";                                  // min 350px
var Map_height = "400px";                                  // min 300px

//var Chart_width  = "350px";                                // min 350px
//var Chart_height = "350px";                                // min 300px
