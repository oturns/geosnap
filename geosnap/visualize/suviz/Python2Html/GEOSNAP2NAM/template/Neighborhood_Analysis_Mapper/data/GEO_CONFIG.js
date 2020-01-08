// Define the number of maps and some configuration parameters that you want to visualize.

var InitialLayers = ["INC", "1980", "1990", "2000", "2010"];
//var InitialLayers = ["1990", "2010"];

var Initial_map_center = [34.0522, -117.9];  
var Initial_map_zoom_level = 8;   


var Index_of_neighborhood_change = true;         //choropleth map: Maps representing index of neighborhood Change
var Maps_of_neighborhood = true;                 //choropleth map: Maps representing clustering result  
var Distribution_INC1 = true;                    //density chart: INC changes as the map extent changes 
var Distribution_INC2_different_period = true;   //density chart: INC changes by different years
var Distribution_INC2_different_cluster = true;  //density chart: INC changes by different clusters
var Temporal_change_in_neighborhoods = true;     //stacked chart: Temporal Change in Neighborhoods over years 
  

var Num_Of_Decimal_Places = 4;                             // default = 2

var Map_width  = "350px";                                  // min 350px
var Map_height = "300px";                                  // min 300px
