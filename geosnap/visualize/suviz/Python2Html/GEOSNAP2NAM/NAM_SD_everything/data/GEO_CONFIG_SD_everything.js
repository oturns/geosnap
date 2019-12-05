// Define the number of maps and some configuration parameters that you want to visualize.

var InitialLayers = ["INC", "1980", "1990", "2000", "2010"];

/* Map Extent and Zoom level will be automatically adjusted when you do not define map center and zoom level */
//var Initial_map_center = [34.0522, -117.9];  
//var Initial_map_zoom_level = 8;   


var allMetros = false;                                      //choropleth map: Maps representing INC of all metros
var Index_of_neighborhood_change = true;					//choropleth map: Maps representing index of neighborhood Change
var Maps_of_neighborhood = true;							//choropleth map: Maps representing clustering result  
var Distribution_INC1 = true;								//density chart: INC changes as the map extent changes 
var Distribution_INC2_different_period = true;				//density chart: INC changes by different years
var Distribution_INC2_different_cluster = true;				//density chart: INC changes by different clusters
var Temporal_change_in_neighborhoods = true;				//stacked chart: Temporal Change in Neighborhoods over years
var Parallel_Categories_Diagram_in_neighborhoods = true;	//parallel categories diagram
var Chord_Diagram_in_neighborhoods = true;					//chord diagram
  

var Num_Of_Decimal_Places = 2;                             // default = 2

var Map_width  = "400px";                                  // min 350px
var Map_height = "400px";                                  // min 300px


/////////////////////////////////////////////////////////////////
// Options for only INC map                                    //
/////////////////////////////////////////////////////////////////

//option for class(the classification method): equal, quantile, std, arithmetic, geometric, quantile
//option for count(the number of classes): 1 to 9
//options for color: Green, Blue, Orange, Red, Pink

var mapAclassification = {class: 'equal', count: 9, color: 'Red'};