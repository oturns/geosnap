
//global varible
var getNow = function() { return moment().format('HH:mm:ss.SSS '); };
var CA = null;
var app={
	maxZoom: 14,
	m: 5,                                        // number of the maps in a web page shown
	d: 5,                                        // number of the density charts in a web page shown
	g: 5,                                        // number of the years for cluster charts in a web page shown
	nClusters: 0,                                // number of clusters
	clickedCluster: 0,                           // clecked cluster from map1 ~ 5
	years: ["INC","1980","1990","2000","2010"],  // INC + max five years
	mYears: null,                                // years to draw the maps
	dYears: null,                                // years to draw the density charts
	gYears: null,                                // years to draw the cluster charts
	yearstring: null,                            // global variable for the selected year of string type from the user
	selectedyears: null,                         // global variable for the selected year of array type from the user
	state: null,                                 // global variable for the selected state from the user
	metro: null,                                 // global variable for the selected metro from the user
	county: null,                                // global variable for the selected county from the user
	params: null,                                // global variable for the selected variables from the user
	states: null,                                // global area for the contents of states table from server
	groups: null,                                // global area for the contents of groups table from server
	codebook: null,                              // global area for the contents of codebook table from server
	title: null,                                 // global area for the header of result message from server
	
	titles: [],                                  // global area for the header of result message from server
	geokey: null,                                // global variable for GEO_JSON and GEO_VARIABLES (ex. tractid)
	geoname: null,                               // global variable for GEO_JSON (ex. County, state or '')
	values: [],                                  // global area for the values of title index [L001, L002, ....]
	titdic: {},                                  // key: titles[n], value: values[n]

	InitialMapCenter: null,                      // initial map center coordinates from configuration file [34.0522, -118.2437]
	InitialMapZoomLevel: null,                   // initial map zoom level from configuration file (ex. 10)
	Index_of_neighborhood_change: true,          // draw INC map or not form configuration file (default: true)
	Maps_of_neighborhood: true,                  // draw neighborhood maps or not form configuration file (default: true)
	Distribution_INC1: true,                     // draw INC distribution chart or not form configuration file (default: true)
	Distribution_INC2_different_period: true,    // draw INC by time period chart or not form configuration file (default: true)
	Distribution_INC2_different_cluster: true,   // draw INC by cluster chart or not form configuration file (default: true)
	Temporal_change_in_neighborhoods: true,      // draw stacked area chart or not form configuration file (default: true)
	NumOfDecimalPlaces: 2,                       // the number of decimal places (default: 2)
	MapWidth: "500px",                           // map width of each map (default: 500px)
	MapHeight: "500px",                          // map height of each map (default: 500px)
	ChartWidth: "500px",                         // width of stacked area chart (default: 500px)  ->  same as MapWidth
	ChartHeight: "500px",                        // height of stacked area chart (default: 500px)  ->  same as MapHeight
	
	mapAclassification: {class: 'quantile', count: 8, color: 'Red'},
	map0classification: {class: null, count: null, color: null},

	receivedGeoJSON: null,                       // global area for full GeoJSON data from the server
	selectedGeoJSON: null,                       // global area for selected GeoJSON data from full GeoJSON data
	selectedBounds : null,                       // global area for map bounds when selected GeoJSON data update
	fadeCount: 1000,                             // unique fade id for console.log
	faded_at: moment(new Date()),                // fade start time for console.log

	maps: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	map0: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	map1: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	map2: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	map3: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	map4: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	map5: {map: null, bounds: null, geojson: null, info: null, legend: null, layers: null, layerscontrol:null, lastHighlightedTractid: null, classification: null, item: null, items: null, zIntervals: null, mIntervals: null, nPolygonbyClass: [], densityChart: {minX: null, maxX: null, minY: null, maxY: null}},
	colorGradient: ["#a6cee3","#1f78b4","#b2df8a","#33a02c","#fb9a99","#e31a1c","#fdbf6f","#ff7f00",
					"#cab2d6","#6a3d9a","#ffff99","#b15928","#8dd3c7","#ffffb3","#bebada","#fb8072",
					"#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd","#ccebc5","#ffed6f"],
	colorGradient0: [],                          // colorGradient for map0
	colorGradient1: [],                          // colorGradient for map1 ~ 5
	colorGradient19: [],                         // colorGradient for map1 ~ 5 + "#5E5E5E"
};

var COLOR_CLASS = {
	"Green5"  : ["#ffffcc", "#c2e699", "#78c679", "#31a354", "#006837"],
	"Green6"  : ["#ffffcc", "#d9f0a3", "#addd8e", "#78c679", "#31a354", "#006837"],
	"Green7"  : ["#ffffcc", "#d9f0a3", "#addd8e", "#78c679", "#41ab5d", "#238443", "#005a32"],
	"Green8"  : ["#ffffe5", "#f7fcb9", "#d9f0a3", "#addd8e", "#78c679", "#41ab5d", "#238443", "#005a32"],
	"Green9"  : ["#ffffe5", "#f7fcb9", "#d9f0a3", "#addd8e", "#78c679", "#41ab5d", "#238443", "#006837", "#004529"],
	"Blue5"   : ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"],
	"Blue6"   : ["#ffffcc", "#c7e9b4", "#7fcdbb", "#41b6c4", "#2c7fb8", "#253494"],
	"Blue7"   : ["#ffffcc", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#0c2c84"],
	"Blue8"   : ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#0c2c84"],
    "Blue9"   : ["#ffffd9", "#edf8b1", "#c7e9b4", "#7fcdbb", "#41b6c4", "#1d91c0", "#225ea8", "#253494", "#081d58"],
	"Orange5" : ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
	"Orange6" : ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"],
	"Orange7" : ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"],
	"Orange8" : ["#ffffcc" ,"#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c ", "#b10026"],
   	"Orange9" : ["#ffffcc" ,"#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c ", "#bd0026","#800026"],
	"Red5"    : ["#fee5d9", "#fcae91", "#fb6a4a", "#de2d26", "#a50f15"],
	"Red6"    : ["#fee5d9", "#fcbba1", "#fc9272", "#fb6a4a", "#de2d26", "#a50f15"],
	"Red7"    : ["#fee5d9", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#99000d"],
	"Red8"    : ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#99000d"],
	"Red9"    : ["#fff5f0", "#fee0d2", "#fcbba1", "#fc9272", "#fb6a4a", "#ef3b2c", "#cb181d", "#a50f15", "#67000d"],
	"Pink5"   : ["#feebe2", "#fbb4b9", "#f768a1", "#c51b8a", "#7a0177"],
	"Pink6"   : ["#feebe2", "#fcc5c0", "#fa9fb5", "#f768a1", "#c51b8a", "#7a0177"],
	"Pink7"   : ["#feebe2", "#fcc5c0", "#fa9fb5", "#f768a1", "#dd3497", "#ae017e", "#7a0177"],
	"Pink8"   : ["#fff7f3", "#fde0dd", "#fcc5c0", "#fa9fb5", "#f768a1", "#dd3497", "#ae017e", "#7a0177"],
	"Pink9"   : ["#fff7f3", "#fde0dd", "#fcc5c0", "#fa9fb5", "#f768a1", "#dd3497", "#ae017e", "#7a0177", "#49006a"],
	"Gray8"   : ["#cccccc", "#bfbfbf", "#b3b3b3", "#a6a6a6", "#999999", "#8c8c8c", "#808080", "#737373"],
};

var mbAttr = '' +
		'' +
		'',
	mbUrl = 'https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw';


var FakeBaseLayers = {
};	
	
	
function draw_basemap(mIDX) {
	if (mIDX in app && app[mIDX].map) {
		app[mIDX].map.remove();
	}
	app[mIDX] = $.extend(true, {}, app["maps"]);                     // deep copy  ->  all clear mapN global variable
	
	var selected_mapdiv = document.getElementById(mIDX).getElementsByClassName("map")[0];
	
	var	grayscale   = L.tileLayer(mbUrl, {id: 'mapbox.light'});
	var	streets  = L.tileLayer(mbUrl, {id: 'mapbox.streets'});	
	
	var mapCenter = [37.09024, -95.712891];
	var mapZoomLevel = 4;
	if (app.InitialMapCenter != null) mapCenter = app.InitialMapCenter;
	if (app.InitialMapZoomLevel != null) mapZoomLevel = app.InitialMapZoomLevel;
	app[mIDX].map = L.map(selected_mapdiv, {
		center: mapCenter,
		zoom: mapZoomLevel,
		layers: [grayscale]
	});

	var baseLayers = {
		"Grayscale": grayscale,
		"Streets": streets
	};	
}	

function set_decoration_to_auto(mapN) {
	// change labels to line-through using polygons count
	var nPolygon = $("#"+mapN+"_nPolygon").text();
	if (nPolygon) nPolygon = nPolygon.split(' ')[0];
	if (!$.isNumeric(nPolygon)) nPolygon = 0;
	if (nPolygon > 1000 && $("label[for="+mapN+"_auto]").text() == 'Create a group') {
		$("label[for='"+mapN+"_auto']").css('text-decoration', 'line-through');
	} else {
		$("label[for='"+mapN+"_auto']").css('text-decoration', 'none');
	}
}


function draw_titlemap(mIDX, year) {
	// set drop-down list of 'Year:' 
	var html_year = 'Year: <select name="yearSelect" onChange="year_change(\'' + mIDX + '\')">';
	if (year == "INC") 
			html_year += '<option value="INC" class="line_none">INC</option>';
	else {
		for (var i=0; i<app.m; i++) {
			if (app.mYears[i] == "INC") continue;
			html_year += '<option value="'+app.mYears[i]+'" class="line_none">'+app.mYears[i]+'</option>';
		}
	}
	html_year += '</select>';
	$("#"+mIDX+" .map_year").html(html_year);
	$("#"+mIDX+" select[name=yearSelect]").val(year);
	$("#"+mIDX+" select[name=yearSelect]").attr('disabled', 'disabled');
	
	// set check box of 'map_metroInterval' 
	if (year.startsWith('INC')) {
		var html_metroInterval = 
			'<span style="font-size: 80%;">' +
			'	 <input id="metroInterval" type="checkbox" name="'+mIDX+'-checkbox" value="metroInterval">' +
			'    <label for="metroInterval">Local</label>' + 
			'</span>';
		$("#"+mIDX+" .map_metroInterval").html(html_metroInterval);
	}
	
	// if metro interval checkbox clicked
	$('input[type=checkbox][name="'+mIDX+'-checkbox"]').change(function() {
		var metroInterval = $(this).is(":checked");
		//console.log(getNow(), mIDX, "metroInterval changed:", metroInterval);
		var nowBounds = app[mIDX].map.getBounds();
		if (!boundsEqual(app.selectedBounds, nowBounds)) {
			//console.log(getNow(), mIDX, 'mapN.map.getBounds() != app.selectedBounds', nowBounds, app.selectedBounds);
			app.selectedBounds = nowBounds;
			updateSelectedGeoJSON(mIDX);
			CA = app.selectedGeoJSON;
		}
		ACSdata_render(mIDX);
		//console.log("app[mIDX].item:", app[mIDX].item)
		if (app[mIDX].item.startsWith('INC') && Distribution_INC1) {
			for (var i=0; i<app.d; i++) {
				var dIDX = "mapD" + i;
				var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
				if (!dYear.startsWith('INC')) continue;
				var mapN = "map" + i;
				paintDensity(mapN, {});
			}
		}
	});

	// set sync radio & button
	var leaveGroup = "Leave group";
	if (app.MapWidth.replace('px','') < 400) leaveGroup = "Leave";
	var html_syncbtn = '';
	html_syncbtn += '<span id="'+mIDX+'_nPolygon" style="font-size: 90%;"></span>';
	html_syncbtn += '<span style="font-size: 90%;">&nbsp;&nbsp;</span>';
	html_syncbtn += '<span style="font-size: 90%;">';
	html_syncbtn += '  <input id="'+mIDX+'_auto" type="radio" value="auto" name="'+mIDX+'-radio">';
	html_syncbtn += '  <label for="'+mIDX+'_auto">Create a group</label>';
	html_syncbtn += '</span>';
	html_syncbtn += '<span style="font-size: 90%;">&nbsp;&nbsp;</span>';
	html_syncbtn += '<span style="font-size: 90%;" hidden>';
	html_syncbtn += '  <input id="'+mIDX+'_manual" type="radio" value="manual" name="'+mIDX+'-radio" checked="checked">';
	html_syncbtn += '  <label for="'+mIDX+'_manual">' + leaveGroup + '</label>';
	html_syncbtn += '</span>';
	html_syncbtn += '<span style="font-size: 90%;">&nbsp;&nbsp;&nbsp;&nbsp;</span>';
	html_syncbtn += '<button id="'+mIDX+'_syncbtn" type="button">Sync</button>'
	$("#"+mIDX+" .map_sync").html(html_syncbtn);
	if (app.MapWidth.replace('px','') < 500) $("#"+mIDX+"_nPolygon").hide();

	$('input[type=radio][name="'+mIDX+'-radio"]').on('change', function() {
		var sync = $(this).val();
		//console.log(getNow(), mIDX, 'sync:', sync, 'clicked');
		
		var msec = CA.features.length;
		if (msec < 500) msec = 500;
		// drawMode ->  1: draw normal,  2: draw when auto, manual selected,  3: draw all maps force
		if (sync == 'manual') {
			$("#"+mIDX+"_manual").parent().hide();
			$("label[for="+mIDX+"_auto]").html('Join the group');    // Create a group -> Joined or Join the group
			$("#"+mIDX+" .map").removeClass('borderMaps');
		}
		if (sync == 'auto') {
			$("#"+mIDX+"_manual").parent().show();
			$("label[for="+mIDX+"_auto]").text('Joined');            // Create a group or Join the group -> Joined
			$("#"+mIDX+" .map").addClass('borderMaps');
		}
		// get autoLabels in the five maps, hasJoined, baseBounds
		var autoLabels = [];
		var hasJoined = false;
		var baseBounds = null;                                       // the map bounds of already joined map
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			var label = $("label[for="+mapN+"_auto]").text();
			autoLabels.push(label);
			if (label == 'Joined') {
				hasJoined = true;
				if (mIDX != mapN) {
					baseBounds = app[mapN].map.getBounds();
				}
			}
		}
		
		// maintain the labels:  create a group  ->  Join the map
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			if (hasJoined) {
				if ($("label[for="+mapN+"_auto]").text() != 'Joined') {
					$("label[for="+mapN+"_auto]").text('Join the group');
				}
				$("label[for='"+mapN+"_auto']").css('text-decoration', 'none');
			} else {
				set_decoration_to_auto(mapN);
			}
		}
	
		// set the check box of global join
		if (getGlobalJoinfromMaps()) {
			$('input[type=checkbox][id="globalJoin"]').prop("checked", true);
			$('label[for="globalJoin"]').css('color', 'red');
		} else {
			$('input[type=checkbox][id="globalJoin"]').prop("checked", false);
			$('label[for="globalJoin"]').css('color', 'gray');
		}

		if (sync == 'manual') {
			fadeToWindow(mIDX);
			mapOn_movestart_off();
			mapOn_moveend_off();
			setTimeout(function() { 
				redraw_maps(mIDX, 2);
			}, 300); 	
		}
		if (sync == 'auto') {
			fadeToWindow(mIDX);
			mapOn_movestart_off();
			mapOn_moveend_off();
			setTimeout(function() { 
				redraw_maps(mIDX, 2, baseBounds);
			}, 300);
		}
	});
	
	$("#"+mIDX+"_syncbtn").on('click', function() {
		//console.log(getNow(), mIDX, mIDX+"_syncbtn clicked");
		
		// get input value of global options
		var globalYear = $("#global_year select[name=globalYear]").val();
		var globalLayer = $("#global_layer select[name=globalLayer]").val();
		
		// set input value of global options to the header of five maps
		var prvYears = getYearsfromMaps();
		//var prvLayers = getLayersfromMaps();
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			var year = app.mYears[i];
			if (globalYear != "none") {
				if (globalYear != "each") year = globalYear;
				$("#"+mapN+" select[name=yearSelect]").val(year);
			}
			if (globalLayer != "none") {
				$("#"+mapN+" select[name=ACSdata]").val(globalLayer);
			}
		}
		var nowYears = getYearsfromMaps();
		//var nowLayers = getLayersfromMaps();
		var isChangedMaps = [];
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			isChangedMaps[i] = false;
			if (nowYears[i] != prvYears[i]) isChangedMaps[i] = mapN;
			//if (nowLayers[i] != prvLayers[i]) isChangedMaps[i] = mapN;
		}
		
		// Joined or Join the group -> Create a group
		var globalJoin = $('input[type=checkbox][id="globalJoin"]').is(":checked");
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			if (globalJoin == false) {           // manual
				$("#"+mapN+"_manual").prop("checked", true)
				$("#"+mapN+"_manual").parent().hide();
				$("label[for="+mapN+"_auto]").html('Create a group');
				set_decoration_to_auto(mapN);
				$("#"+mapN+" .map").removeClass('borderMaps');
			}
			if (globalJoin == true) {            // auto
				$("#"+mapN+"_auto").prop("checked", true)
				$("#"+mapN+"_manual").parent().show();
				$("label[for="+mapN+"_auto]").html('Joined');
				set_decoration_to_auto(mapN);
				$("#"+mapN+" .map").addClass('borderMaps');
			}
		}

		fadeToWindow(mIDX);
		mapOn_movestart_off();
		mapOn_moveend_off();
		setTimeout(function() { 
			redraw_maps(mIDX, 3); 
		}, 300);
	});
}

function draw_titleChart(dIDX, year) {
	// set drop-down list of 'Year:' 
	var html_year = 'Year: <select name="yearSelect" onChange="year_change(\'' + dIDX + '\')">';
	if (year == "INC") 
			html_year += '<option value="INC" class="line_none">INC</option>';
	else {
		for (var i=0; i<app.d; i++) {
			if (app.dYears[i] == "INC") continue;
			html_year += '<option value="'+app.dYears[i]+'" class="line_none">'+app.dYears[i]+'</option>';
		}
	}
	html_year += '</select>';
	
	// set density chart
	//var dIDX = mIDX.replace('map', 'mapD');                          // map0 -> mapD0,  map1 -> mapD1  ....
	$("#"+dIDX+" .map_year").html(html_year);
	$("#"+dIDX+" select[name=yearSelect]").val(year);
	$("#"+dIDX+" select[name=yearSelect]").attr('disabled', 'disabled');
	
	if (!year.startsWith('INC')) {
		var html_fixAxes = 
			'<span style="font-size: 100%;">' +
			'	 <input id="'+dIDX+'-fixAxes" type="checkbox" name="dIDX_fixAxes" value="Fix Axes">' +
			'    <label for="fixAxes">Fix Axes</label>' + 
			'</span>';
		$("#"+dIDX+" .map_fixAxes").html(html_fixAxes);
		
		// if Fix Axes checkbox clicked
		$('input[type=checkbox][id="'+dIDX+'-fixAxes"]').change(function() {
			var fixAxes = $(this).is(":checked");
			//console.log(getNow(), dIDX, "fixAxes changed:", fixAxes);
			$('input[type=checkbox][name="dIDX_fixAxes"]').prop("checked", fixAxes);
			
			if (fixAxes == true) {
				var minX =  Number.MAX_VALUE;
				var maxX = -Number.MAX_VALUE;
				var minY =  Number.MAX_VALUE;
				var maxY = -Number.MAX_VALUE;
				for (var i=0; i<app.d; i++) {
					var dIDX = "mapD" + i;
					var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
					//console.log(dIDX, dYear)
					if (dYear.startsWith('INC')) continue;
					var mapN = "map" + i;
					if (minX > app[mapN].densityChart.minX) minX = app[mapN].densityChart.minX;
					if (maxX < app[mapN].densityChart.maxX) maxX = app[mapN].densityChart.maxX;
					if (minY > app[mapN].densityChart.minY) minY = app[mapN].densityChart.minY;
					if (maxY < app[mapN].densityChart.maxY) maxY = app[mapN].densityChart.maxY;
				}
				var update = {
					'xaxis.range': [minX-(maxX-minX)*0.05, maxX+(maxX-minX)*0.05],
					'yaxis.range': [0, maxY*1.05],
				}
				//console.log(update);
				
				for (var i=0; i<app.d; i++) {
					var dIDX = "mapD" + i;
					var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
					//console.log(dIDX, dYear)
					if (dYear.startsWith('INC')) continue;
					Plotly.relayout(dIDX+'_density_chart', update);
				}
			} else {
				for (var i=0; i<app.d; i++) {
					var dIDX = "mapD" + i;
					var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
					//console.log(dIDX, dYear)
					if (dYear.startsWith('INC')) continue;
					var mapN = "map" + i;
					paintDensity(mapN, {});
				}
			}	
		});
	}
}

function draw_titleGraphC(graphC, year) {
	var html_year = 'Year: <select name="yearSelectGraphC" onChange="year_change_graphC(\'' + graphC + '\')">';
	for (var i=0; i<app.g; i++) {
		html_year += '<option value="'+app.gYears[i]+'" class="line_none">'+app.gYears[i]+'</option>';
	}
	html_year += '</select>';
	$("#"+graphC+" .map_year").html(html_year);
	$("#"+graphC+" select[name=yearSelectGraphC]").val(year);
	
	var html_fixAxes = 
		'<span style="font-size: 100%;">' +
		'	 <input id="'+graphC+'-fixAxes" type="checkbox" name="graphC_fixAxes" value="Fix Axes">' +
		'    <label for="fixAxes">Fix Axes</label>' + 
		'</span>';
	$("#"+graphC+" .map_fixAxes").html(html_fixAxes);
	
	// if Fix Axes checkbox clicked
	$('input[type=checkbox][id="'+graphC+'-fixAxes"]').change(function() {
		var fixAxes = $(this).is(":checked");
		//console.log(getNow(), graphC, "fixAxes changed:", fixAxes);
		$('input[type=checkbox][name="graphC_fixAxes"]').prop("checked", fixAxes);
	
		if (fixAxes == true) {
			var minX =  Number.MAX_VALUE;
			var maxX = -Number.MAX_VALUE;
			var minY =  Number.MAX_VALUE;
			var maxY = -Number.MAX_VALUE;
			for (var i=0; i<app.nClusters; i++) {
				var graphC = "graphC" + i;
				if (minX > app[graphC].densityChart.minX) minX = app[graphC].densityChart.minX;
				if (maxX < app[graphC].densityChart.maxX) maxX = app[graphC].densityChart.maxX;
				if (minY > app[graphC].densityChart.minY) minY = app[graphC].densityChart.minY;
				if (maxY < app[graphC].densityChart.maxY) maxY = app[graphC].densityChart.maxY;
			}
			var update = {
				'xaxis.range': [minX-(maxX-minX)*0.05, maxX+(maxX-minX)*0.05],
				'yaxis.range': [0, maxY*1.05],
			}
			//console.log(update);
			
			for (var i=0; i<app.nClusters; i++) {
				var graphC = "graphC" + i;
				Plotly.relayout(graphC+'_density_chart', update);
			}
		} else {
			// parint density chart of the graph of Clusters
			for (var i=0; i<app.nClusters; i++) {
				var graphC = "graphC" + i;
				paintDensityGraphC(graphC, year, i);
			}
		}
	});
}


// get years from #mapN .map_year
function getYearsfromMaps() {
	var years = [];
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
	    var year = $("#"+mapN+" select[name=yearSelect]").val();
		years.push(year);
	}
	return years;
}

// get layers from #mapN .map_layer
function getLayersfromMaps() {
	var layers = [];
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
	    var layer = $("#"+mapN+" select[name=ACSdata]").val();
		layers.push(layer);
	}
	return layers;
}

// get joins from #mapN .map_sync
function getJoinsfromMaps() {
	var joins = [];
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		var join = ($('input[type=radio][name="'+mapN+'-radio"]:checked').val() == "auto") ? true : false;
		joins.push(join);
	}
	return joins;
}

// get global year from #mapN .map_year
function getGlobalYearfromMaps() {
	var years = Array.from(new Set(getYearsfromMaps()));             // get unique years from #mapN .map_year
	var year = "none";
	//if (years.length == 5) year = "each";
	if (years.length == (app.m - 1)) year = "each";
	if (years.length == 1) year = years[0];
	return year;
}

// get global layer from #mapN .map_layer
function getGlobalLayerfromMaps() {
	var layers = Array.from(new Set(getLayersfromMaps()));           // get unique layers from #mapN .map_year
	var layer = "none";
	if (layers.length == 1) layer = layers[0];
	return layer;
}

// get global join from #mapN .map_sync
function getGlobalJoinfromMaps() {
	var joins = Array.from(new Set(getJoinsfromMaps()));             // get unique joins from #mapN .map_sync
	var join = false;
	if (joins.length == 1) join = joins[0];
	return join;
}

// bounds compare with toFixed(2)
function boundsEqual(boundA, boundB) {
	var result = true;
	if ((Math.abs(boundA.getNorth()-boundB.getNorth()) > 0.005) ||             
		(Math.abs(boundA.getEast()-boundB.getEast()) > 0.005) ||               
		(Math.abs(boundA.getSouth()-boundB.getSouth()) > 0.005) ||             
		(Math.abs(boundA.getWest()-boundB.getWest()) > 0.005)) {               
		return false;
	}
	return result;
}

// is bounds of five maps are all same without INC
function isAllBoundsEqual_withoutINC() {
	var bounds = [];
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (app[mapN].item.startsWith('INC')) continue;
		bounds.push(app[mapN].map.getBounds());
	}
	var j = 0;
	var isAllSameBounds = true;
	for (var i=1; i<bounds.length; i++) {
		if (!boundsEqual(bounds[i], bounds[0])) {
			isAllSameBounds = false;
			j = i;
			break;
		}
	}
	if (!isAllSameBounds) {
		//console.log('mapX bounds of all maps are not same.  from: [map' + j + ']');
	}
	return isAllSameBounds;
}

// is bounds of five maps are all same
function isAllBoundsEqual() {
	var bounds = [];
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		bounds.push(app[mapN].map.getBounds());
	}
	var j = 0;
	var isAllSameBounds = true;
	for (var i=1; i<bounds.length; i++) {
		if (!boundsEqual(bounds[i], bounds[0])) {
			isAllSameBounds = false;
			j = i;
			break;
		}
	}
	if (!isAllSameBounds) {
		//console.log('mapX bounds of all maps are not same.  from: [map' + j + ']');
	}
	return isAllSameBounds;
}

// intervals compare
function intervalsEqual(intervalsA, intervalsB) {
	if (intervalsA.length != intervalsB.length) return false;
	for (var i=0; i<intervalsA.length; i++) {
		if (intervalsA[i] != intervalsB[i]) return false;
	}
	//console.log("same intervlas");
	return true;
}

// is zIntervals of five maps are all same
function isAllzIntervalsEqual() {
	var j = 0;
	var isAllSameIntervals = true;
	for (var i=1; i<app.m; i++) {
		var mapN = "map" + i;
		if (!intervalsEqual(app[mapN].zIntervals, app.map0.zIntervals)) {
			isAllSameIntervals = false;
			j = i;
			break;
		}
	}
	if (!isAllSameIntervals) {
		//console.log('mapX zIntervals of all maps are not same.  from: [map' + j + ']');
	}
	return isAllSameIntervals;
}


// hide or show the 'Set Globally' button
function updateGloballyButton() {
	if (isAllBoundsEqual()) $("#global_submit").show();
	else $("#global_submit").hide();
}


// draw global selection menu
function draw_globalSelection() {
	var html_year = 'Year: <select name="globalYear" style="color:red;">' +
					'<option value="none" class="line_none">No Select</option>' +
					'<option value="each" class="line_none" selected>each</option>';
	for (var i=1; i<app.m; i++) {
		html_year += '<option value="'+app.mYears[i]+'" class="line_none">'+app.mYears[i]+'</option>';
	}
	html_year += '</select>';
	$("#global_year").html(html_year);
	$("#global_year").hide();
	if ($("#global_year select[name=globalYear]").val() == "none") {
		$("#global_year select[name=globalYear]").css('color', 'gray');
	} else {
		$("#global_year select[name=globalYear]").css('color', 'red');
	}
	
	// set check box of 'global_join' 
	var html_join = '<span style="font-size: 80%;">' +
					'	 <input id="globalJoin" type="checkbox" name="join_checkbox" value="groupingAuto">' +
					'    <label for="globalJoin" style="color:gray;">Grouping All</label>' + 
					'</span>';
	$("#global_join").html(html_join);

	$("#global-selection").show();
	
	$("#global_year select[name=globalYear]").unbind('click').change(function(){
		var globalYear = $(this).val();                              // save year to global variable, if changed
		if ($("#global_year select[name=globalYear]").val() == "none") {
			$("#global_year select[name=globalYear]").css('color', 'gray');
		} else {
			$("#global_year select[name=globalYear]").css('color', 'red');
		}
	});
	
	/*
	$("#global_layer select[name=globalLayer]").change(function(){
		var globalLayer = $(this).val();                // save layer to global variable, if changed
		if ($("#global_layer select[name=globalLayer]").val() == "none") {
			$("#global_layer select[name=globalLayer]").css('color', 'gray');
		} else {
			$("#global_layer select[name=globalLayer]").css('color', 'red');
		}
	}); */

	$('input[type=checkbox][id="globalJoin"]').change(function(){
		var globalJoin = $(this).is(":checked");
		if (globalJoin == false) {
			$('label[for="globalJoin"]').css('color', 'gray');
		} else {
			$('label[for="globalJoin"]').css('color', 'red');
		}
	});
	
	$("#global_submit").unbind('click').on('click', function(){
		//console.log(getNow(), "    ", "Set Globally button clicked.");
		// check input value of global options
		var globalYear = $("#global_year select[name=globalYear]").val();
		var globalLayer = $("#global_layer select[name=globalLayer]").val();
		//if (globalYear == "none" && globalLayer == "none") {
		if (globalYear == "none") {
			//swal({
			//	title: "Attention!",
			//	text: "You have not selected any of global options.",
			//	icon: "warning",
			//	button: "GO BACK",
			//});
			//return;
		}

		// check the bounds of five maps are all same
		if (!isAllBoundsEqual()) {
			//swal({
			//	title: "Attention!",
			//	text: 'Please make all maps show the same region by clicking one of "Sync" buttons on the top of each map.',
			//	icon: "warning",
			//	button: "GO BACK",
			//});
			//return;
		}
		
		// set input value of global options to the header of five maps
		var prvYears = getYearsfromMaps();
		//var prvLayers = getLayersfromMaps();
		for (var i=1; i<app.m; i++) {
			var mapN = "map" + i;
			var year = app.mYears[i];
			if (globalYear != "none") {
				if (globalYear != "each") year = globalYear;
				$("#"+mapN+" select[name=yearSelect]").val(year);
			}
			if (globalLayer != "none") {
				$("#"+mapN+" select[name=ACSdata]").val(globalLayer);
			}
		}
		var nowYears = getYearsfromMaps();
		//var nowLayers = getLayersfromMaps();
		var isChangedMaps = [];
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			isChangedMaps[i] = false;
			if (nowYears[i] != prvYears[i]) isChangedMaps[i] = mapN;
			//if (nowLayers[i] != prvLayers[i]) isChangedMaps[i] = mapN;
		}
		
		// Joined or Join the group -> Create a group
		var globalJoin = $('input[type=checkbox][id="globalJoin"]').is(":checked");
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;	
			if (globalJoin == false) {                               // manual
				$("#"+mapN+"_manual").prop("checked", true)
				$("#"+mapN+"_manual").parent().hide();
				$("label[for="+mapN+"_auto]").html('Create a group');
				set_decoration_to_auto(mapN);
				$("#"+mapN+" .map").removeClass('borderMaps');
			}
			if (globalJoin == true) {                                // auto
				$("#"+mapN+"_auto").prop("checked", true)
				$("#"+mapN+"_manual").parent().show();
				$("label[for="+mapN+"_auto]").html('Joined');
				set_decoration_to_auto(mapN);
				$("#"+mapN+" .map").addClass('borderMaps');
			}
		}
		
		var msec = CA.features.length;
		if (msec < 500) msec = 500;
		//if (msec > 3000)
		swal({
			title: "Please wait...",
			text: "Maps will be ready in "+(msec/1000).toFixed(1)+" seconds.",
			timer: msec,
			icon: "info",
			buttons: false,
		}).then((value) => {
			//console.log("Redraw all maps by global_submit ended in "+(msec/1000).toFixed(1)+" seconds.");
			triggerStackedAreaChart();
		});
		
		setTimeout(function() {
			mapOn_movestart_off();
			mapOn_moveend_off(); 
			setTimeout(function() { 
				for (var i=0; i<app.m; i++) {
					var mapN = "map" + i;
					drawAmap(mapN, 3);
				}
				for (var i=0; i<app.d; i++) {
					var mapN = "map" + i;
					drawAchart(mapN);
				}
				setTimeout(function() {
					mapOn_movestart_set();
					mapOn_moveend_set(); 
				}, 500); 
			}, 100); 
		}, 100); 
	});
}


function year_change(mIDX) { 
	var year  = $("#"+mIDX+" select[name=yearSelect]").val();
	
	// change year of density chart header
	var dIDX = mIDX.replace('map', 'mapD');                          // map0 -> mapD0,  map1 -> mapD1  ....
	$("#"+dIDX+" select[name=yearSelect]").val(year);
	
	// set global_year
	$("#global_year select[name=globalYear]").val(getGlobalYearfromMaps());
	if ($("#global_year select[name=globalYear]").val() == "none") {
		$("#global_year select[name=globalYear]").css('color', 'gray');
	} else {
		$("#global_year select[name=globalYear]").css('color', 'red');
	}

	/* set drop-down list of 'Layer:' 
	var html_layer = 'Layer: <select name="ACSdata" onChange="layer_change(\'' + mIDX + '\')">';
	$.each(app.groups, function(gIdx, gRow) {
		group_id = gRow[0];
		group_name = gRow[1];
		$("input[name=input_area" + group_id + "_checkboxes]").each(function() {
			if (!this.checked) return true;
			var label = $($(this).prop('labels')).text();
			var codeYY = this.value.substring(0,this.value.length-2) + year.substring(2,4)
			if (app.title.indexOf(codeYY) >= 5) {
				html_layer += '<option value="' + this.value + '" class="line_none">' + label + '</option>';
			} else {
				html_layer += '<option value="' + this.value + '" class="line_through">' + label + '</option>';
			}
		});
	});
	if (html_layer.length < 100) 
	html_layer += '<option value="None">No Data</option>';
	html_layer += '</select>'
	$("#"+mIDX+" .map_layer").html(html_layer);
	
	// set previous layer as selected
	$("#"+mIDX+" select[name=ACSdata]").val(prvLayer).prop('selected', true); */

	headerChange(mIDX);
}


function year_change_graphC(graphC) {

	var year  = $("#"+graphC+" select[name=yearSelectGraphC]").val();
	$("select[name=yearSelectGraphC]").val(year);                    // all of year in the clusters charts are set to same year
	
	// parint density chart of the graph of Clusters
	for (var i=0; i<app.nClusters; i++) {
		var graphC = "graphC" + i;
		paintDensityGraphC(graphC, year, i);
	}
}


function layer_change(mIDX) {
	// set global_layer
	$("#global_layer select[name=globalLayer]").val(getGlobalLayerfromMaps());
	if ($("#global_layer select[name=globalLayer]").val() == "none") {
		$("#global_layer select[name=globalLayer]").css('color', 'gray');
	} else {
		$("#global_layer select[name=globalLayer]").css('color', 'red');
	}
	headerChange(mIDX);
}

function headerChange(mIDX) {
	//console.log(getNow(), mIDX, "Year or Layer changed.");
	fadeToWindow(mIDX);
	mapOn_movestart_off();
	mapOn_moveend_off();
	setTimeout(function() { 
		redraw_maps(mIDX, 2); 
	}, 300);
};


// clear info, legend, layers in the map
function clear_map(mIDX) {
	if (app[mIDX].info) {
		app[mIDX].info.remove();
		app[mIDX].info = null;
	}
	if (app[mIDX].legend) {
		app[mIDX].legend.remove();
		app[mIDX].legend = null;
	}
	if (app[mIDX].layerscontrol) {
		app[mIDX].layerscontrol.remove();
		app[mIDX].layerscontrol = null;
	}
	if (app[mIDX].map.hasLayer(app[mIDX].geojson)) {
		app[mIDX].map.removeLayer(app[mIDX].geojson);
		app[mIDX].geojson = null;
	}
}


// items = [nhwht10] or [nhwht10, nhwht70, .....]
function geostats_classification(classification, nClass, geojson, items) {   

	var values = [];
	var j=0;
	for (var l=0; l<items.length; l++) {
		item = items[l];
		for (var i=0; i<geojson.features.length; i++) {
			if (!(item in geojson.features[i].properties)) continue;
			if (geojson.features[i].properties[item] == -9999) continue;
			// geometric progression can't be applied with a serie containing negative or zeor values.
			if (classification == 'geometric' && geojson.features[i].properties[item] == 0) continue;
			values[j++] = geojson.features[i].properties[item];
		}
	}
	if (values.length == 0) {
		return null;
	}
	var maxInterval = nClass * 1;
	if (maxInterval > values.length) {
		maxInterval = values.length;
	}
	
	values.sort(function(a,b){return a-b});
	var intervals = [];
	
	if (classification != 'ckmeans') {                               // using geostats.js
		var serie = new geostats();
		serie.setSerie(values);
		var ranges = [];                                             // ranges.length = maxInterval + 1
		if (classification == 'equal')      ranges = serie.getClassEqInterval(maxInterval);
		if (classification == 'quantile')   ranges = serie.getClassQuantile(maxInterval);
		if (classification == 'std')        ranges = serie.getClassStdDeviation(maxInterval);
		if (classification == 'arithmetic') ranges = serie.getClassArithmeticProgression(maxInterval);
		if (classification == 'geometric')  ranges = serie.getClassGeometricProgression(maxInterval);
		if (classification != 'quantile') {
			intervals = ranges.slice(0, -1);
		} else {
			if (maxInterval > values.length) {
				intervals = ranges;
			} else {
				intervals = [ranges[0]];
				var r = 1;
				for (var v=0; v<values.length; v++) {
					if (values[v] == ranges[r]) {
						var n = v + 1;
						if (n >= values.length) n = v;
						intervals.push(values[n]);
						if (intervals.length >= maxInterval) break;
						if (++r >= ranges.length) break;
					}
				}
			}
			
		}
	}
	
	if (classification == 'ckmeans') {                               // using simple-statistics
		var clusteredValues = ss.ckmeans(values, maxInterval);
		for (var key in clusteredValues) {
			clusteredValue = clusteredValues[key];
			intervals.push(clusteredValue[0]);
		}
	}

	if (intervals.length > nClass) intervals = intervals.slice(0, nClass);

	return intervals;
}


function drawAmap(mIDX, drawMode) { 
	// drawMode ->  1: draw normal,  2: draw when auto, manual selected,  3: draw all maps force
	if (!drawMode) drawMode = 1;

	var map = app[mIDX].map;

	var selectedYear  = $("#"+mIDX+" select[name=yearSelect]").val();
	var selectedLayer  = $("#"+mIDX+" select[name=ACSdata]").val();
	var selectedLayerIndex  = $("#"+mIDX+" select[name=ACSdata]").prop('selectedIndex');

	var item = selectedYear;
	//console.log(getNow(), mIDX, selectedYear, selectedLayer,
	//	' ['+selectedLayerIndex+':', '"'+item+'"] ', classification, ' draw a map started');
	
	// set off metro interval check box when redraw a map every time
	$('input[type=checkbox][name="'+mIDX+'checkbox"]').prop("checked", false);
	
	// change labels to line-through using polygons count
	var count = CA.features.length;	
	$("#"+mIDX+"_nPolygon").text(count + ' Polygons');               // Polygons
	set_decoration_to_auto(mIDX);
	
	app[mIDX].item = item;
	app[mIDX].zIntervals = []
	app[mIDX].mIntervals = []
	
	//console.log("app[mIDX].item:", app[mIDX].item)
	if (selectedYear.startsWith("INC")) {
		var classification;
		if (app[mIDX].item.startsWith('INC')) classification = app.map0classification.class;
		
		var nClass;
		if (app[mIDX].item.startsWith('INC')) nClass = app.map0classification.count;
		
		// re-calculate zoomed intervals and save it to app.mapN.zIntervals
		app[mIDX].zIntervals = geostats_classification(classification, nClass, CA, [item]);
		//console.log(getNow(), mIDX, 'quantile zIntervals:', app[mIDX].zIntervals);
		if (!app[mIDX].zIntervals) {
			$("#"+mIDX+"_nPolygon").text("No Data");
			clear_map(mIDX);
			return;
		}
		
		app[mIDX].mIntervals = geostats_classification(classification, nClass, app.receivedGeoJSON, [item]);
	} else {
		for (var i=0; i<app.nClusters; i++) {
			app[mIDX].zIntervals[i] = i;
			app[mIDX].mIntervals[i] = i;
		}
	}
	//console.log(getNow(), mIDX, 'zIntervals:', app[mIDX].zIntervals);
	//console.log(getNow(), mIDX, 'mIntervals:', app[mIDX].mIntervals);
	ACSdata_render(mIDX);
	
}

function drawAchart(mIDX, drawMode) {
	paintDensity(mIDX, {});
}

function ACSdata_render(mIDX) {
		var map = app[mIDX].map;
		var item = app[mIDX].item;
		
		var localInterval = $('input[type=checkbox][name="'+mIDX+'-checkbox"]').is(":checked");
		//console.log('localInterval:', localInterval)
		var zIntervals = app[mIDX].zIntervals;
		var mIntervals = app[mIDX].mIntervals;
		
		// control that shows state info on hover
		if (app[mIDX].info != null) app[mIDX].info.remove();
		app[mIDX].info = L.control();
		app[mIDX].info.onAdd = function (map) {
			this._div = L.DomUtil.create('div', 'info infolegend');
			this.update();
			return this._div;
		};
		app[mIDX].info.update = function (props) {
			var v = (props && item in props && props[item] != -9999) ? props[item] : "No Data";
			var v2 = (v == "No Data") ? v : v.toFixed(app.NumOfDecimalPlaces);
			var vstring = (v == "No Data") ? v : (app[mIDX].item.startsWith('INC') ? 'INC &nbsp; ' + v2 : 'Cluster ' + v);
			var c = '';
			var nm = getClass1(v * 1.0, "m");
			var nz = getClass1(v * 1.0, "z");
			var fm = (nm > 4) ? 'white' : 'black';
			var fz = (nz > 4) ? 'white' : 'black';
			var cm = '<i style="color:'+fm+'; background:' + getColor1(v * 1.0, "m") + '">' + nm + '</i>';
			var cz = '<i style="color:'+fz+'; background:' + getColor1(v * 1.0, "z") + '">' + nz + '</i>';
			if (!localInterval) c = cm;
			else {
				if (cm != cz) c = '<span> )</span>' + cz + '<span> &nbsp; ( </span>' + cm;
				else c = '<span> &nbsp; ( &nbsp; &nbsp; )</span>' + cm;
			}
			var geoname = (typeof props == "object" && props.hasOwnProperty(app.geoname)) ? props[app.geoname] : "";
			this._div.innerHTML = '<h4></h4>' +  (props ?
				'<b>' + ' ' + vstring + '</b> &nbsp; ' + c + '<br/>'
				+ (geoname ? geoname + '<br/>' : '')
				+ 'tract id : ' + props.tractid.substring(5)
				: 'Hover over an area');
		};
		app[mIDX].info.addTo(map);

		// get getOpacity
		function getOpacity1(feature) {
			return 0.7;
		}

		// get color depending on selected layer's value
		function getColor1(d, interval) {
			var colorGradient = app.colorGradient1;
			if (app[mIDX].item.startsWith('INC')) colorGradient = app.colorGradient0;
			
			if (!$.isNumeric(d) || d == "-9999") return "#5E5E5E";
			var intervals = (localInterval) ? zIntervals : mIntervals;
			if (interval == 'm') intervals = mIntervals;
			if (interval == 'z') intervals = zIntervals;
			
			for (var i=colorGradient.length-1; i>=0; i--) {
				if (d >= intervals[i]) {
					return colorGradient[i];
				}
			}			
		}
		
		function getClass1(d, interval) {
			var colorGradient = app.colorGradient1;
			if (app[mIDX].item.startsWith('INC')) colorGradient = app.colorGradient0;
			
			if (!$.isNumeric(d) || d == "-9999") 
				return colorGradient.length;                         // may be 9 (the last member)
			var intervals = (localInterval) ? zIntervals : mIntervals;
			if (interval == 'm') intervals = mIntervals;
			if (interval == 'z') intervals = zIntervals;
	
			for (var i=colorGradient.length-1; i>=0; i--) {
				if (d >= intervals[i]) {
					return i;
				}
			}
			return colorGradient.length;                             // may be 9 (the last member)
		}
		
		function style1(feature) {
			var v = (item in feature.properties && feature.properties[item] != -9999) ? feature.properties[item] : "No Data";
			var nz = getClass1(v * 1.0, "z");
			
			var colorGradient = app.colorGradient1;
			if (app[mIDX].item.startsWith('INC')) colorGradient = app.colorGradient0;
			
			app[mIDX].nPolygonbyClass[nz] += 1;
			return {
				weight: 0.5,
				opacity: 1,
				color: 'white',
				dashArray: '1',
				fillOpacity: getOpacity1(feature),
				fillColor: getColor1(feature.properties[item])
			};
		}

		function highlightFeature(e) {
			var layer = e.target;
			var layerid = layer._leaflet_id;
			var tractid = layer.feature.properties.tractid;
			app[mIDX].lastHighlightedTractid = tractid;
			layer.setStyle({
				weight: 3,
				color: '#00ffff',
				dashArray: '',
				fillOpacity: 0.9
			});
			for (var i=0; i<app.m; i++) {
				var mapN = "map" + i;
				if (mIDX == mapN) continue;
				if (!app[mapN].geojson) continue;
				var layerN = app[mapN].geojson._layers[app[mapN].layers[tractid]];
				if (!layerN) continue;
				layerN.setStyle({
					weight: 3,
					color: '#666',
					dashArray: '',
					fillOpacity: 0.9
				});
			}
			if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
				//layer.bringToFront();
				for (var i=0; i<app.m; i++) {
					var mapN = "map" + i;
					//if (mIDX == mapN) continue;
					if (!app[mapN].geojson) continue;
					//console.log(getNow(), mapN, 'geojson', app[mapN].geojson);
					var layerN = app[mapN].geojson._layers[app[mapN].layers[tractid]];
					if (!layerN) continue;
					layerN.bringToFront();
				}
			}
			for (var i=0; i<app.m; i++) {
				var mapN = "map" + i;
				if (app[mapN].info) app[mapN].info.update(layer.feature.properties);
			}
		}

		function resetHighlight(e) {
			var layer = e.target;
			var tractid = layer.feature.properties.tractid;
			for (var i=0; i<app.m; i++) {
				var mapN = "map" + i;
				//if (mIDX == mapN) continue;
				if (!app[mapN].geojson) continue;
				var layerN = app[mapN].geojson._layers[app[mapN].layers[tractid]];
				if (!layerN) {
					continue;
				}
				app[mapN].geojson.resetStyle(layerN);
			}
			for (var i=0; i<app.m; i++) {
				var mapN = "map" + i;
				if (app[mapN].info) app[mapN].info.update();
			}
		}
		
		function clicked_aTract(e) {
			var layer = e.target;
			//console.log('layer.feature.properties:', layer.feature.properties)
			var cluster = layer.feature.properties[item];
			if (cluster == -9999) return;
			app.clickedCluster = cluster;
			for (var i=0; i<app.d; i++) {
				var dIDX = "mapD" + i;
				var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
				if (dYear.startsWith('INC')) continue;
				var mapN = "map" + i;
				paintDensity(mapN, {});
			}
		}

		function zoomToFeature(e) {
			map.fitBounds(e.target.getBounds());
		}

		function onEachFeature(feature, layer) {
			if (app[mIDX].item.startsWith('INC'))
				layer.on({
					mouseover: highlightFeature,
					mouseout: resetHighlight,
					//click: zoomToFeature
					//click: highlightFeature
				});
			else
				layer.on({
					mouseover: highlightFeature,
					mouseout: resetHighlight,
					//click: zoomToFeature
					//click: highlightFeature
					click: clicked_aTract
				});
		}
		
		// layer that shows data
		if (map.hasLayer(app[mIDX].geojson)){
			map.removeLayer(app[mIDX].geojson);	
			
		}
		app[mIDX].nPolygonbyClass = $.extend(true, {}, app["maps"].nPolygonbyClass);         // clear nPolygonbyClass
		app[mIDX].geojson = L.geoJson(CA, {
			style: style1,
			onEachFeature: onEachFeature
		}).addTo(map);
		
		var overlays = {
			"layer": app[mIDX].geojson,
		};
		
		// Create layercontrol. Before create, remove layercontrol if it exists
		if (app[mIDX].layerscontrol ) {
			app[mIDX].layerscontrol.remove();			
		}	
	    app[mIDX].layerscontrol = L.control.layers(FakeBaseLayers, overlays, {
			position: 'bottomleft', // 'topleft', 'bottomleft', 'bottomright'
			collapsed: false, // true
			//autoZIndex: false
		}).addTo(app[mIDX].map);
		
		app[mIDX].layers = {};
		app[mIDX].geojson.eachLayer(function(layer) {
			layerid = layer._leaflet_id;
			tractid = layer.feature.properties.tractid;
			//console.log(getNow(), mIDX, " tractid:", tractid, "layerid:", layerid, layer)
			app[mIDX].layers[tractid] = layerid;
		})
		
		// control that shows legend
		var colorGradient = app.colorGradient1;
		if (app[mIDX].item.startsWith('INC')) colorGradient = app.colorGradient0;
		if (app[mIDX].item.startsWith('INC')) {
			if (app[mIDX].legend != null) app[mIDX].legend.remove();
			app[mIDX].legend = L.control({position: 'bottomright'});
	
			app[mIDX].legend.onAdd = function (map) {
				var div = L.DomUtil.create('div', 'info legend'),
					//grades = zIntervals,
					labels = [],
					zClass, mClass;
				var spaces = "&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;";
				for (var i = 0; i < colorGradient.length; i++) {
					zClass = (i < zIntervals.length) ? zIntervals[i].toFixed(app.NumOfDecimalPlaces) : spaces;
					mClass = (i < mIntervals.length) ? mIntervals[i].toFixed(app.NumOfDecimalPlaces) : spaces;
					labels.push(
						'<i style="background:' + colorGradient[i] + '"></i> ' + mClass +
						((localInterval) ? '&nbsp; (' + zClass + ')' : ''));
				}
				labels.push(                                         // last legend is always 'No Data'
						'<i style="background:' + getColor1(-9999) + '"></i> ' +
						'No Data');				
				div.innerHTML = labels.join('<br>');
				return div;
			};
	
			app[mIDX].legend.addTo(map);
		}
}	// end of ACSdata_render(mIDX)



$( document ).ready(function() {
	// Set up the AJAX indicator
    $('body').append('<div id="ajaxBusy"><p id="ajaxBusyMsg">Please wait...</p></div>');
	
	//console.log(GEO_JSON.features.length, GEO_JSON);
	//console.log(GEO_VARIABLES);
	
	// build app.receivedGeoJSON from GEO_JSON and GEO_VARIABLES
	app.titles = GEO_VARIABLES[0];
	app.geokey = app.titles[0];
	app.values = [];
	app.titdic = {};
	for (var i=0; i<app.titles.length; i++) {
		var value = 'L'+zeroPad(i, 3);
		app.values.push(value);
		if (i != 0) app.titdic[app.titles[i]] = value;
	}
	//console.log(app.titles, app.values, app.titdic)
	
	var geokey = app.geokey;
	
	if (!('features' in GEO_JSON) || GEO_JSON.features.length < 1) {
		swal({
			title: "Alert!",
			text: "The 'GEO_JSON' you provided has no 'features'.",
			icon: "error",
			button: "ABORT",
		});
		return;
	}
	
	var firstProperty = $.extend(true, {}, GEO_JSON.features[0].properties);             // deep copy of the object
	if (!(geokey in firstProperty)) {
		swal({
			title: "Alert!",
			text: "The key in your geojosn should match the key in your attributes.",
			icon: "error",
			button: "ABORT",
		});
		return;
	}
	
	delete firstProperty[geokey];
	app.geoname = (Object.keys(firstProperty).length > 0) ? Object.keys(firstProperty)[0] : "";
	var geoname = app.geoname;
	
	var geoFeatures = {}                                             // key: geokey,  value: geometry
	var nError = 0;
	$.each(GEO_JSON.features, function(rIdx, row) {
		var tractid = ('properties' in row && geokey in row.properties) ? row.properties[geokey] : "";
		var geometry = ('geometry' in row) ? row.geometry : {};
		if (tractid == "") {
			nError += 1;
			return true;
		}
		if ($.isEmptyObject(geometry)) {
			nError += 1;
			return true;
		}
		geoFeatures[tractid] = {'geometry': geometry, 'properties': row.properties};
	});
	//console.log(nError, Object.keys(geoFeatures).length, geoFeatures);
	
	if (Object.keys(geoFeatures).length == 0) {
		swal({
			title: "Alert!",
			text: "The 'GEO_JSON' you provided is not valid.\nPlease check it.",
			icon: "error",
			button: "ABORT",
		});
		return;
	}
	if (nError != 0) {
		swal({
			title: "Attention!",
			text: "The 'GEO_JSON' you provided has "+nError+" errors.\nProceed anyway?",
			icon: "warning",
			button: "CONTINUE",
		});
	}
	
	nError = 0;
	app.receivedGeoJSON = {"type":"FeatureCollection", "features":[]}
	$.each(GEO_VARIABLES, function(rIdx, row) {
		if (rIdx == 0) return true;                                  // skip title's row
		var geokey = row[0];
		if (!(geokey in geoFeatures)) {
			//console.log("The key '"+geokey+"' is not found in the GEO_JSON.");
			nError += 1;
			return true;
		}
		var geoFeature = geoFeatures[geokey];
		var feature = {"type": "Feature", "geometry": geoFeature["geometry"], "properties": geoFeature["properties"]};
		$.each(row, function(cIdx, col) {
			if (cIdx < 1) return true;                               // skip key's row (first column is the geokey)
			//feature.properties[app.values[cIdx]] = row[cIdx] * 1.0;
			feature.properties[GEO_VARIABLES[0][cIdx]] = row[cIdx] * 1.0;
		});
		app.receivedGeoJSON["features"].push(feature);
	});
	
	CA = app.receivedGeoJSON;	
	//console.log(CA);
	
	// get nClusters from GEO_VARIABLES
	app.nClusters = 0;
	for (var i=1; i<GEO_VARIABLES.length; i++) {
		for (var j=1; j<GEO_VARIABLES[i].length; j++) {
			if (GEO_VARIABLES[0][j].startsWith("INC")) continue;
			if (app.nClusters < GEO_VARIABLES[i][j]) app.nClusters = GEO_VARIABLES[i][j];
		}
	}
	if (app.nClusters == 0) {
		swal({
			title: "Alert!",
			text: "The 'GEO_VARIABLES' you provided has no cluster value in it.\nPlease check it.",
			icon: "error",
			button: "ABORT",
		});
		return;
	} else app.nClusters += 1;
	//console.log("app.nClusters:", app.nClusters);
	app.colorGradient1 = app.colorGradient.slice(0, app.nClusters);
	app.colorGradient19 = app.colorGradient.slice(0, app.nClusters);
	app.colorGradient19.push("#5E5E5E");
	
	// set app.maps.nPolygonbyClass for clear stackedAreaChart
	app.maps.nPolygonbyClass = [];
	for (var i=0; i<=app.nClusters; i++) app.maps.nPolygonbyClass.push(0);     // the last one is for 'No Data'

	// set default layers for each map
	app.yearstring = "";
	app.selectedlayers = [];
	var nError = 0;
	if (typeof InitialLayers !== 'undefined' && InitialLayers instanceof Array) {
		for (var i=0; i<InitialLayers.length; i++) {
			if (typeof InitialLayers[i] === 'string' && InitialLayers[i] in CA.features[0].properties) {
				app.selectedlayers.push(InitialLayers[i]);
				if (!InitialLayers[i].startsWith("INC")) app.yearstring += InitialLayers[i] + ",";
			} else nError += 1;
		}
	}
	if (app.yearstring.length > 0) app.yearstring = app.yearstring.substr(0, app.yearstring.length-1);
	
	if (app.selectedlayers.length == 0) {
		//swal({
		//	title: "Attention!",
		//	text: "The InitialLayers in 'GEO_CONFIG.js' you provided is not match with 'GEO_VARIABLES'.\nProceed anyway?",
		//	icon: "warning",
		//	button: "CONTINUE",
		//});
		console.log("The InitialLayers in 'GEO_CONFIG.js' are not match with 'GEO_VARIABLES.js'.");
		console.log("All titles of 'GEO_VARIABLES.js' are used instead of the InitialLayers in 'GEO_CONFIG.js'.");
		for (var i=1; i<app.titles.length; i++) {
			app.selectedlayers.push(app.titles[i]);
			if (!app.titles[i].startsWith("INC")) app.yearstring += app.titles[i] + ",";
		}
		if (app.yearstring.length > 0) app.yearstring = app.yearstring.substr(0, app.yearstring.length-1);
	}
	
	if (app.selectedlayers.length == 0) {
		swal({
			title: "Alert!",
			text: "The 'GEO_JSON' you provided is not valid.\nPlease check it.",
			text: "The InitialLayers in 'GEO_CONFIG.js' you provided is not match with 'GEO_VARIABLES'.\nProceed anyway?",
			icon: "error",
			button: "ABORT",
		});
		return;
	}
	if (nError != 0) {
		swal({
			title: "Attention!",
			text: "The InitialLayers in 'GEO_CONFIG.js' you provided has "+nError+" errors.\nProceed anyway?",
			icon: "warning",
			button: "CONTINUE",
		});
	}
	
	//app.layers = [];
	//for (var i=0; i<app.m; i++) {
	//	var theLayer = (selectedlayers.length > i) ? selectedlayers[i] : "";
	//	if (theLayer == "") theLayer = app.titles[i+1];
	//	app.layers.push(theLayer);
	//}
	//app.layers = app.selectedlayers.slice();                       // deep copy of array
	//app.firstDefinedLayers = app.layers.slice();                   // deep copy of array
	app.selectedyears = app.selectedlayers.slice();                  // deep copy of array
	
	// redefine parameters of 'GEO_CONFIG' using app.selectedyears
	if (!app.selectedyears.includes("INC")) {
		Index_of_neighborhood_change = false;
		Distribution_INC1 = false;
	}
	if (app.selectedyears.length == 1 && app.selectedyears.includes("INC")) {
		Maps_of_neighborhood = false;
		Distribution_INC2_different_period = false;
		Distribution_INC2_different_cluster = false;
		Temporal_change_in_neighborhoods = false;
	}
	//console.log("Index_of_neighborhood_change:", Index_of_neighborhood_change);
	//console.log("Maps_of_neighborhood:", Maps_of_neighborhood);
	//console.log("Distribution_INC1:", Distribution_INC1);
	//console.log("Distribution_INC2_different_period:", Distribution_INC2_different_period);
	//console.log("Distribution_INC2_different_cluster:", Distribution_INC2_different_cluster);
	//console.log("Temporal_change_in_neighborhoods:", Temporal_change_in_neighborhoods);
	
	
	// set initial map center to global variable
	if (typeof Initial_map_center !== 'undefined' && Initial_map_center instanceof Array) {
		if (Initial_map_center.length == 2) app.InitialMapCenter = Initial_map_center;
	}
	//console.log("app.InitialMapCenter:", app.InitialMapCenter);
	
	// set initial map zoom level to global variable
	if (typeof Initial_map_zoom_level !== 'undefined' && typeof Initial_map_zoom_level === 'number') {
		if (Initial_map_zoom_level >= 1 && Initial_map_zoom_level <= 20) app.InitialMapZoomLevel = Initial_map_zoom_level;
	}
	//console.log("app.InitialMapZoomLevel:", app.InitialMapZoomLevel);
	
	// set draw INC map or not to global variable
	if (typeof Index_of_neighborhood_change !== 'undefined' && typeof Index_of_neighborhood_change === 'boolean') {
		app.Index_of_neighborhood_change = Index_of_neighborhood_change;
	}
	//console.log("app.Index_of_neighborhood_change:", app.Index_of_neighborhood_change);

	// set draw neighborhood maps or not to global variable
	if (typeof Maps_of_neighborhood !== 'undefined' && typeof Maps_of_neighborhood === 'boolean') {
		app.Maps_of_neighborhood = Maps_of_neighborhood;
	}
	//console.log("app.Maps_of_neighborhood:", app.Maps_of_neighborhood);
	
	// set draw INC distribution chart or not to global variable
	if (typeof Distribution_INC1 !=='undefined' && typeof Distribution_INC1 ==='boolean') {
		app.Distribution_INC1 = Distribution_INC1;
	}
	//console.log("app.Distribution_INC1:", app.Distribution_INC1);
	
	// set draw INC by time period chart or not to global variable
	if (typeof Distribution_INC2_different_period !=='undefined' && typeof Distribution_INC2_different_period ==='boolean') {
		app.Distribution_INC2_different_period = Distribution_INC2_different_period;
	}
	//console.log("app.Distribution_INC2_different_period:", app.Distribution_INC2_different_period);

	// set draw INC by cluster chart or not to global variable
	if (typeof Distribution_INC2_different_cluster !== 'undefined' && typeof Distribution_INC2_different_cluster === 'boolean') {
		app.Distribution_INC2_different_cluster = Distribution_INC2_different_cluster;
	}
	//console.log("app.Distribution_INC2_different_cluster:", app.Distribution_INC2_different_cluster);
	
	// set draw stacked area chart or not to global variable
	if (typeof Temporal_change_in_neighborhoods !== 'undefined' && typeof Temporal_change_in_neighborhoods === 'boolean') {
		app.Temporal_change_in_neighborhoods = Temporal_change_in_neighborhoods;
	}
	//console.log("app.Temporal_change_in_neighborhoods:", app.Temporal_change_in_neighborhoods);
	
	// set number of decimal places to global variable
	if (typeof Num_Of_Decimal_Places !== 'undefined' && typeof Num_Of_Decimal_Places === 'number') {
		app.NumOfDecimalPlaces = Num_Of_Decimal_Places;
	}
	//console.log("app.NumOfDecimalPlaces:", app.NumOfDecimalPlaces);
	
	// set map width and height to global variable
	if (typeof Map_width !== 'undefined' && typeof Map_width === 'string' && 
	    Map_width.substring(Map_width.length-2) == 'px' && $.isNumeric(Map_width.replace('px',''))) {
		if (Map_width.substring(0, Map_width.length-2) >= 350) {
			app.MapWidth = Map_width;
			app.ChartWidth = Map_width;
		}
	}
	if (typeof Map_height !== 'undefined' && typeof Map_height === 'string' && 
	    Map_height.substring(Map_height.length-2) == 'px' && $.isNumeric(Map_height.replace('px',''))) {
		if (Map_height.substring(0, Map_height.length-2) >= 300) {
			app.MapHeight = Map_height;
			app.ChartHeight = Map_height;
		}
	}
	//console.log(app.MapWidth, app.MapHeight);
	
	app.years = app.selectedyears;
	app.m = app.selectedyears.length;
	app.d = app.selectedyears.length;
	
	app.mYears = [];
	for (var i=0; i<app.years.length; i++) {
		var year = app.years[i];
		if (app.Index_of_neighborhood_change == true &&  year.startsWith('INC')) app.mYears.push(year);
		if (app.Maps_of_neighborhood         == true && !year.startsWith('INC')) app.mYears.push(year);
	}
	app.m = app.mYears.length;
	
	if (app.m < 2 || app.m < 3 && app.mYears.includes('INC')) {
		Temporal_change_in_neighborhoods = false;
		//console.log("app.Temporal_change_in_neighborhoods:", app.Temporal_change_in_neighborhoods);
	}
	
	app.dYears = [];
	for (var i=0; i<app.years.length; i++) {
		var year = app.years[i];
		if (app.Distribution_INC1 == true &&  year.startsWith('INC')) app.dYears.push(year);
		if (app.Distribution_INC2_different_period == true && !year.startsWith('INC')) app.dYears.push(year);
	}
	app.d = app.dYears.length;
	
	app.gYears = [];
	for (var i=0; i<app.years.length; i++) {
		var year = app.years[i];
		if (!year.startsWith('INC')) app.gYears.push(year);
	}
	app.g = app.gYears.length;
	
	//console.log("app.yearstring:", app.yearstring);
	//console.log("app.selectedyears:", app.selectedyears);
	//console.log("app.years:", app.years);
	//console.log("app.mYears:", app.mYears);
	//console.log("app.dYears:", app.dYears);
	//console.log("app.gYears:", app.gYears);
	//console.log("app.m:", app.m);
	//console.log("app.d:", app.d);
	//console.log("app.nClusters:", app.nClusters);
	
	drawMapContainer();                                              // draw mapContainer by options in 'GEO_CONFIG'
	
	analysisAndDrawMaps(0);
	
	// redraw all five maps using received GeoJSON
	$("#initFiveMaps").click(function() {
		//console.log(getNow(), "    ", "Initialize all maps button clicked.");
		CA = app.receivedGeoJSON;
		var msec = CA.features.length;
		if (msec < 500) msec = 500;
		swal({
			title: "Please wait...",
			text: "Maps will be ready in "+(msec/1000).toFixed(1)+" seconds.",
			timer: msec,
			icon: "info",
			buttons: false,
		}).then((value) => {
			//console.log("Initiaize all maps ended in "+(msec/1000).toFixed(1)+" seconds.");
			triggerStackedAreaChart();
		});

		setTimeout(function() { 
			//mapOn_moveend_off(); 
			setTimeout(function() { 
				draw_all_maps(); 
				//setTimeout(function() { mapOn_moveend_set(); }, 500); 
			}, 100); 
		}, 100);
	});
});


function analysisAndDrawMaps(scrollTop) {
	document.documentElement.scrollTop = 0;
	fadeToWindow("Submit");
	$("#ajaxBusy").show();
		
	CA = app.receivedGeoJSON;
	var msec = CA.features.length;
	if (msec < 500) msec = 500;
	swal({
		title: "Please wait...",
		text: "Maps will be ready in "+(msec/1000).toFixed(1)+" seconds.",
		timer: msec,
		icon: "info",
		buttons: false,
	}).then((value) => {
		//console.log("Initiaize all maps ended in "+(msec/1000).toFixed(1)+" seconds.");
		triggerStackedAreaChart();
	});
	
	setTimeout(function() { 
		//mapOn_moveend_off(); 
		setTimeout(function() { 
			draw_all_maps(); 
			//setTimeout(function() { mapOn_moveend_set(); }, 500); 
		}, 100); 
	}, 100); 
	
	$("#initFiveMaps").show();
	$("#submitForm").hide();
	
	fadeOutWindow("Submit");
	$("#ajaxBusy").hide();
	document.documentElement.scrollTop = scrollTop;
}


// check and draw stacked area chart
function triggerStackedAreaChart() {
	$("#stackedAreaChart").html("");
	$("#map"+app.m).hide();
	
	if ($("#global_year select[name=globalYear]").val() != 'each') return;
	if (!isAllBoundsEqual_withoutINC()) return;
	
	$("#map"+app.m).show();
	var data = [];
	for (var i=0; i<app.m; i++) {
		if (app.mYears[i].startsWith("INC")) continue;
		var mapN = "map" + i;
		var row = {date: new Date(app.mYears[i], 1, 1)};
		for (var j=0; j<app.maps.nPolygonbyClass.length; j++) {
			var c = "Cluster" + j;
			row[c] = app[mapN].nPolygonbyClass[j];
		}
		data.push(row);
	}
	data["columns"] = ["date"];
	for (var j=0; j<app.maps.nPolygonbyClass.length; j++) {
		var c = "Cluster" + j;
		data["columns"].push(c);
	}
	//console.log(data);		
	if (Temporal_change_in_neighborhoods) drawStackedAreaChart("stackedAreaChart", data);
}


// draw all five maps when
//   1. when receive GeoJSON from server
//   2. when 'Initialize all maps' button clicked
function draw_all_maps() {

	// deep copy all classification of mapA to all classification of map0
	app.map0classification = $.extend(true, {}, app.mapAclassification);
	//console.log('app.map0classification:', app.map0classification)
	
	var cc = app.map0classification.color + app.map0classification.count
	app.colorGradient0 = COLOR_CLASS[cc].slice(0, COLOR_CLASS[cc].length);   // deep copy

	// draw titles area
	var map_html = '';
	map_html += '<div>';
	map_html += '	<div class="map_layer" style="height:25px;float:right" hidden></div>';
	map_html += '	<div class="map_year" style="margin:0px 30px 0px 0px; height:25px;float:both"></div>';
	map_html += '</div>';
	map_html += '<div>';
	map_html += '	<div class="map_metroInterval" style="height:25px;float:left;clear:both"></div>';
	map_html += '	<div class="map_sync" style="height:25px;float:right"></div>';
	map_html += '</div>';
	map_html += '<div class="map"></div>';
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		document.getElementById(mapN).innerHTML = map_html;
	}
	
	var map_html = '';
	map_html += '<div>';
	map_html += '	<div class="map_year" style="margin:0px 100px 0px 0px; height:25px;float:left;"></div>';
	map_html += '	<div class="map_nPolygon" style="margin:0px 100px 0px 0px; height:25px;float:left;"></div>';
	map_html += '	<div class="map_fixAxes" style="height:25px;float:left;"></div>';
	map_html += '</div>';
	map_html += '<br><br>';
	map_html += '<div id="_density_chart" class="chart densityPeriod"></div>';
	for (var i=0; i<app.d; i++) {
		var mapD = "mapD" + i;
		var html = map_html.replace('_density_chart', mapD+'_density_chart');
		if (app.dYears[i].startsWith('INC')) 
			html = html.replace('class="chart densityPeriod"', 'class="chart densityINC"');
		document.getElementById(mapD).innerHTML = html;
		if (app.MapWidth.replace('px','') < 500) $("#"+mapD+" .map_nPolygon").hide();
	}
	
	if (app.Distribution_INC2_different_cluster) {
		var map_html = '';
		map_html += '<div>';
		map_html += '	<div class="map_year" style="margin:0px 100px 0px 0px; height:25px;float:left;"></div>';
		map_html += '	<div class="map_nPolygon" style="margin:0px 100px 0px 0px; height:25px;float:left;"></div>';
		map_html += '	<div class="map_fixAxes" style="height:25px;float:left;"></div>';
		map_html += '</div>';
		map_html += '<br><br>';
		map_html += '<div id="_density_chart" class="chart densityCluster"></div>';
		for (var i=0; i<app.nClusters; i++) {
			var graphC = "graphC" + i;
			document.getElementById(graphC).innerHTML = map_html.replace('_density_chart', graphC+'_density_chart');
			if (app.MapWidth.replace('px','') < 500) $("#"+graphC+" .map_nPolygon").hide();
		}
	}
	
	// change height and width for maps and stacked area chart
	$("#mapContainer").css("height", app.MapHeight.replace('px','')*1+100+'px');
	$(".mapArea").css("width", app.MapWidth);
	$(".mapAreaLast").css("width", app.ChartWidth);
	$(".map").css("width", app.MapWidth);
	$(".map").css("height", app.MapHeight);
	$(".chart").css("width", app.MapWidth.replace('px','')*1-10+'px');
	$(".chart").css("height", app.MapHeight.replace('px','')*1-10+'px');
	
	// draw each base map
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		draw_basemap(mapN);
	}

	// draw titles of each map
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		draw_titlemap(mapN, app.mYears[i]);
	}
	
	// draw titles of each density chart
	for (var i=0; i<app.d; i++) {
		var mapN = "mapD" + i;
		draw_titleChart(mapN, app.dYears[i]);
	}
	
	// draw titles of each graph of clusters
	for (var i=0; i<app.nClusters; i++) {
		var graphC = "graphC" + i;
		draw_titleGraphC(graphC, app.gYears[0]);
	}
	
	draw_globalSelection();

	// initialize all bounds in app.mapN
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		app[mapN].bounds = app[mapN].map.getBounds();
		//console.log(getNow(), mapN, 'app.'+mapN+'.bounds: ', app[mapN].bounds);
	}
	
	// set map bounds using geo bounds in d3 function
	var geoBounds = d3.geoBounds(CA);
	
	var fitBounds = L.latLngBounds(L.latLng(geoBounds[0][1], geoBounds[0][0]), 
								   L.latLng(geoBounds[1][1], geoBounds[1][0]));
	//console.log('fitBounds:', fitBounds);
	if (app.m > 0 && app.InitialMapCenter != null && app.InitialMapZoomLevel != null) {
	
		// set bitBounds from InitialMapCenter and InitialMapZoomLevel
		fitBounds = app[mapN].bounds;
		var mapBounds = app[mapN].map.getBounds();
		var west = mapBounds.getWest();
		var south = mapBounds.getSouth();
		var east = mapBounds.getEast();
		var north = mapBounds.getNorth();
		var featureMapBounds = {type: "Feature", properties: {}, geometry: {type: "Polygon", coordinates: [
			[ [west, south], [east, south], [east, north], [west, north], [west, south] ] 
		]}}

		// build selectedGeoJSON from receivedGeoJSON
		var count = 0, edgeCount = 0;
		var started = moment(new Date());
		var selectedFeatures = [];
		var count = 0;
		var baseLines = lineify(featureMapBounds);
		
		$.each(app.receivedGeoJSON.features, function(rIdx, feature) {
			if (isPolygonInMapBounds(feature, baseLines, west, south, east, north)) {
				count += 1;
				selectedFeatures.push([feature.properties[app.geokey], rIdx]);
			}
		});
		var duration = moment.duration(moment(new Date()).diff(started));
		
		// build selectedGeoJSON and set it to CA
		app.selectedGeoJSON = {"type":"FeatureCollection", "features":[]};
		$.each(selectedFeatures, function(rIdx, feature) {
			// feature[0] -> tractid, feature[1] -> rIdx
			app.selectedGeoJSON.features.push(app.receivedGeoJSON.features[feature[1]]);
		});
		CA = app.selectedGeoJSON;
		selectedFeatures = null;
		app.selectedBounds = mapBounds;
	}
	
	// fitBounds and redraw maps
	setTimeout(function () {
		// fitBounds
		var started = moment(new Date());
		var watchfitbounds = [];
		for (var i=0; i<app.m; i++) watchfitbounds.push(false);
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			var alreadyFitted = false;
			if (boundsEqual(app[mapN].map.getBounds(), fitBounds)) alreadyFitted = true;
			else app[mapN].map.fitBounds(fitBounds);

			watchfitbounds[i] = setInterval(function(i, mapN) {
				var duration = moment.duration(moment(new Date()).diff(started));
				var nowBounds = app[mapN].map.getBounds();
				//console.log(getNow(), mapN, mapN+'.bounds:', app[mapN].bounds);
				//console.log(getNow(), mapN, 'nowBounds:', nowBounds, duration / 1000);
				if (alreadyFitted || !boundsEqual(app[mapN].bounds, nowBounds)) {
					//console.log(getNow(), mapN, 'after  fitBounds: ', nowBounds, 'duration:', duration/1000);
					clearInterval(watchfitbounds[i]);
					watchfitbounds[i] = false;
					app[mapN].bounds = nowBounds;
				}
				if (duration > 10000) {                              // 10000 = 10 sec
					//console.log(getNow(), mapN, 'ffit fitBounds incompleted: ', nowBounds, 'duration:', duration/1000);
					clearInterval(watchfitbounds[i]);
					watchfitbounds[i] = false;
				}
				if (!watchfitbounds.reduce(function(x, y) {return x || y;})) {
					//console.log(getNow(), mapN, 'ALL fit fitBounds completed: ', nowBounds, 'duration:', duration/1000);
					updateGloballyButton();
					app.selectedBounds = nowBounds;
					setTimeout(function() { mapOn_contextmenu_set(); }, 100);
					setTimeout(function() { mapOn_movestart_set(); }, 200);
					setTimeout(function() { mapOn_moveend_set(); }, 500);
				}
			}, 100, i, mapN);
		}
		
		// redraw maps
		for (var i=0; i<app.m; i++) {
			var mapN = "map" + i;
			drawAmap(mapN, 3);
		}
		
		// redraw charts
		for (var i=0; i<app.d; i++) {
			var mapN = "map" + i;
			drawAchart(mapN);
		}
		
		// parint density chart of the graph of Clusters
		for (var i=0; i<app.nClusters; i++) {
			var graphC = "graphC" + i;
			var year   = $("#"+graphC+" select[name=yearSelectGraphC]").val();
			paintDensityGraphC(graphC, year, i);
		}
		
	}, 100);
}


function fadeToWindow(mIDX) {
	if (!app.isFaded) {
		app.isFaded = true;
		app.fadeCount += 1;
		app.faded_at = moment(new Date());
		//console.log(getNow(), mIDX, 'fadeToWindow start.', app.fadeCount);
		$(".backLayer").css({top:(window.pageYOffset || document.documentElement.scrollTop), position:'absolute'});
		$(".backLayer").width($(window).width()).height($(window).height());
		$(".backLayer").fadeTo(300, 0.3);
	} else {
		console.log(getNow(), mIDX, 'fadeToWindow start ignored.', app.fadeCount);
	}
}

function fadeOutWindow(mIDX) {
	if (app.isFaded) {
		app.isFaded = false;
		var duration = moment.duration(moment(new Date()).diff(app.faded_at));
		//console.log(getNow(), mIDX, 'fadeOutWindow ended.', app.fadeCount, 'duration:', duration/1000);
		$("#backLayer").html('')
		$(".backLayer").fadeOut(300);
	} else {
		console.log(getNow(), mIDX, 'fadeOutWindow ended ignored.', app.fadeCount);
	}
}

function mapOn_contextmenu_set(mIDX) {
	var pIDX = (mIDX) ? mIDX : "    "
	//console.log(getNow(), pIDX, 'START mapOn_contextmenu_set');
	if (app.m >= 1  && (pIDX == "    " || pIDX == "map0")) app["map0"].map.on('contextmenu', mapON_contextmenu_map0, "map10");
	if (app.m >= 2  && (pIDX == "    " || pIDX == "map1")) app["map1"].map.on('contextmenu', mapON_contextmenu_map1, "map11");
	if (app.m >= 3  && (pIDX == "    " || pIDX == "map2")) app["map2"].map.on('contextmenu', mapON_contextmenu_map2, "map12");
	if (app.m >= 4  && (pIDX == "    " || pIDX == "map3")) app["map3"].map.on('contextmenu', mapON_contextmenu_map3, "map13");
	if (app.m >= 5  && (pIDX == "    " || pIDX == "map4")) app["map4"].map.on('contextmenu', mapON_contextmenu_map4, "map14");
	if (app.m >= 6  && (pIDX == "    " || pIDX == "map5")) app["map5"].map.on('contextmenu', mapON_contextmenu_map5, "map15");
	//console.log(getNow(), pIDX, 'ENDED mapOn_contextmenu_set');
}

//function mapON_contextmenu_mapA(e) { mapON_contextmenu(e, "mapA"); }
function mapON_contextmenu_map0(e) { mapON_contextmenu(e, "map0"); }
function mapON_contextmenu_map1(e) { mapON_contextmenu(e, "map1"); }
function mapON_contextmenu_map2(e) { mapON_contextmenu(e, "map2"); }
function mapON_contextmenu_map3(e) { mapON_contextmenu(e, "map3"); }
function mapON_contextmenu_map4(e) { mapON_contextmenu(e, "map4"); }
function mapON_contextmenu_map5(e) { mapON_contextmenu(e, "map5"); }

function mapON_contextmenu(e, mIDX) {
	var metroInterval = $('input[type=checkbox][name="'+mIDX+'-checkbox"]').is(":checked");
	if (metroInterval) {
		$('input[type=checkbox][name="'+mIDX+'-checkbox"]').prop("checked", false);
	} else {
		$('input[type=checkbox][name="'+mIDX+'-checkbox"]').prop("checked", true);
	}
	var nowBounds = app[mIDX].map.getBounds();
	if (!boundsEqual(app.selectedBounds, nowBounds)) {
		//console.log(getNow(), mIDX, 'mIDX.map.getBounds() != app.selectedBounds', nowBounds, app.selectedBounds);
		app.selectedBounds = nowBounds;
		updateSelectedGeoJSON(mIDX);
		CA = app.selectedGeoJSON;
	}
	ACSdata_render(mIDX);
	if (app[mIDX].item.startsWith('INC') && Distribution_INC1) {
		for (var i=0; i<app.d; i++) {
			var dIDX = "mapD" + i;
			var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
			if (!dYear.startsWith('INC')) continue;
			var mapN = "map" + i;
			paintDensity(mapN, {});
		}
	}
}

var mapON_movestarts = [
	function mapON_movestart_map0(e) { mapON_movestart(e, "map0"); },
	function mapON_movestart_map1(e) { mapON_movestart(e, "map1"); },
	function mapON_movestart_map2(e) { mapON_movestart(e, "map2"); },
	function mapON_movestart_map3(e) { mapON_movestart(e, "map3"); },
	function mapON_movestart_map4(e) { mapON_movestart(e, "map4"); },
	function mapON_movestart_map5(e) { mapON_movestart(e, "map5"); },
];

function mapOn_movestart_set(mIDX) {
	var pIDX = (mIDX) ? mIDX : "    "
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (count_movestart_event(mapN) == 0 && (pIDX == "    " || pIDX == mapN))
			app[mapN].map.on('movestart', mapON_movestarts[i], mapN);
	}
}

function mapOn_movestart_off(mIDX) {
	var pIDX = (mIDX) ? mIDX : "    "
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (count_movestart_event(mapN) != 0 && (pIDX == "    " || pIDX == mapN))
			app[mapN].map.off('movestart', mapON_movestarts[i], mapN);
	}
}

function mapON_movestart(e, mIDX) {
	//console.log(getNow(), mIDX, 'event movestart detected');
	//console.log(getNow(), mIDX, 'fadeToWindow start.');
	fadeToWindow(mIDX);
	mapOn_movestart_off();
}

var mapON_moveends = [
	function mapON_moveend_map0(e) { mapON_moveend(e, "map0"); },
	function mapON_moveend_map1(e) { mapON_moveend(e, "map1"); },
	function mapON_moveend_map2(e) { mapON_moveend(e, "map2"); },
	function mapON_moveend_map3(e) { mapON_moveend(e, "map3"); },
	function mapON_moveend_map4(e) { mapON_moveend(e, "map4"); },
	function mapON_moveend_map5(e) { mapON_moveend(e, "map5"); },
];


function mapOn_moveend_set(mIDX) {
	var pIDX = (mIDX) ? mIDX : "    "
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (count_moveend_event(mapN) == 0 && (pIDX == "    " || pIDX == mapN))
			app[mapN].map.on('moveend', mapON_moveends[i], mapN);
	}
}

function mapOn_moveend_off(mIDX) {
	var pIDX = (mIDX) ? mIDX : "    "
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (count_moveend_event(mapN) != 0 && (pIDX == "    " || pIDX == mapN))
			app[mapN].map.off('moveend', mapON_moveends[i], mapN);
	}
}

function mapON_moveend(e, mIDX) { 
	//console.log(getNow(), mIDX, 'event moveend detected'); 
	mapOn_moveend_off();
	setTimeout(function() { 
		redraw_maps(mIDX, 1);
	}, 100);
};

// count 'movestart' event registered in the map 
function count_movestart_event(mIDX, e) {
	var movestartEvents = app[mIDX].map._events["movestart"];
	if (e) movestartEvents = e.target._events["movestart"];
	if (!movestartEvents) return 0;
	var count = 0;
	$.each(movestartEvents, function(idx, row) {
		var ctx = row['ctx'];
		if (typeof ctx === 'string' && ctx.startsWith(mIDX)) count += 1;
	});
	return count;
}

// count 'moveend' event registered in the map 
function count_moveend_event(mIDX, e) {
	var moveendEvents = app[mIDX].map._events["moveend"];
	if (e) moveendEvents = e.target._events["moveend"];
	if (!moveendEvents) return 0;
	var count = 0;
	$.each(moveendEvents, function(idx, row) {
		var ctx = row['ctx'];
		if (typeof ctx === 'string' && ctx.startsWith(mIDX)) count += 1;
	});
	return count;
}


// 1. call 'redraw_all_maps' or 'redraw_only_mapA'
// 2. check it completed.
function redraw_maps(mIDX, drawMode, baseBounds) {
	
	redraw_all_maps(mIDX, drawMode, baseBounds);
	
	var started = moment(new Date());
	//console.log(getNow(), mIDX, 'after  redraw_all_maps');
	var i = 0;
	function repeat_setTimeout() {
		setTimeout(function() {
			i += 1;
			if (i > 70) {
				var duration = moment.duration(moment(new Date()).diff(started));
				//console.log(getNow(), mIDX, 'after  redraw_all_maps:', (i-1), ' duration:', duration/1000);
				updateGloballyButton();
				mapOn_movestart_set();
				mapOn_moveend_set();
				triggerStackedAreaChart();
				//console.log(getNow(), mIDX, 'fadeOutWindow ended.');
				fadeOutWindow(mIDX);
			} else {
				repeat_setTimeout();
			}
		}, 0);
	}
	repeat_setTimeout();
}

	
// redraw a map and related maps
function redraw_all_maps(mIDX, drawMode, baseBounds) {
	// drawMode ->  1: draw normal,  2: draw when auto, manual selected,  3: draw all maps force
	//console.log(getNow(), mIDX, 'redraw_maps start', 'drawMode: ', drawMode, 'baseBounds: ', baseBounds);
	
	var prvBounds = app[mIDX].bounds;
	var mapBounds = app[mIDX].map.getBounds();
	app[mIDX].bounds = mapBounds;                                    // save this map bounds to app.mapN.bounds
	if (baseBounds) mapBounds = baseBounds;                          // auto clicked, join the group aleady existed
	
	//console.log(getNow(), mIDX, 'prvBounds: ', prvBounds);
	//console.log(getNow(), mIDX, 'mapBounds: ', mapBounds);
	
	var west = mapBounds.getWest();
	var south = mapBounds.getSouth();
	var east = mapBounds.getEast();
	var north = mapBounds.getNorth();
	var featureMapBounds = {type: "Feature", properties: {}, geometry: {type: "Polygon", coordinates: [
		[ [west, south], [east, south], [east, north], [west, north], [west, south] ] 
	]}}

	// build selectedGeoJSON from receivedGeoJSON
	var count = 0;
	var selectedFeatures = [];
	var baseLines = lineify(featureMapBounds);
	
	var started = moment(new Date());
	$.each(app.receivedGeoJSON.features, function(rIdx, feature) {
		if (isPolygonInMapBounds(feature, baseLines, west, south, east, north)) {
			count += 1;
			selectedFeatures.push([feature.properties[app.geokey], rIdx]);
		}
	});
	var duration = moment.duration(moment(new Date()).diff(started));
	//console.log(getNow(), mIDX, 'selected features count in mapBounds:', count, 'duration:', duration/1000);

	var this_sync = $('input[type=radio][name="'+mIDX+'-radio"]:checked').val();
	
	// determine witch maps need to fitBounds
	var refitBoundableMaps = (!boundsEqual(mapBounds, app[mIDX].map.getBounds())) ? [mIDX] : [];
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (mapN == mIDX) continue;
		var that_sync = $('input[type=radio][name="'+mapN+'-radio"]:checked').val();
		if (drawMode != 3) {
			if (this_sync == 'auto' && that_sync == 'manual') continue;
			if (this_sync == 'manual') continue;
		}
		if (!boundsEqual(mapBounds, app[mapN].map.getBounds())) {
			refitBoundableMaps.push(mapN);
		}
	}

	// check need redrawing or not
	var needDrawing = true;
	if (drawMode == 1 && count < 1) {
		console.log(getNow(), mIDX, 'redrawing map ignored when count < 1');
		needDrawing = false;
	}
	
	if (selectedFeatures.length == CA.features.length) {
		var isEqual = true;
		for (var f=0; f<selectedFeatures.length; f++) {
			var prvFeature = CA.features[f];
			var newFeature = selectedFeatures[f];
			if (newFeature[0] != prvFeature.properties.tractid) {
				isEqual = false;
				break;
			}
		}
		if (drawMode == 1 && isEqual) {
			console.log(getNow(), mIDX, 'redrawing map ignored when prvGeoJSON = selectedFeatures');
			needDrawing = false;
		}
	}
	
	// determine witch maps need to redraw
	var redrawableMaps = [mIDX];
	var autoCount = (this_sync == 'auto') ? 1 : 0;
	for (var i=0; i<app.m; i++) {
		var mapN = "map" + i;
		if (mapN == mIDX) continue;
		var that_sync = $('input[type=radio][name="'+mapN+'-radio"]:checked').val();
		if (that_sync == 'auto') autoCount += 1;
		var needRedraw = false;
		if (drawMode == 1 && this_sync == 'auto' && that_sync == 'auto') needRedraw = true;
		if (drawMode == 2 && that_sync == 'auto') needRedraw = true;
		if (drawMode == 3) needRedraw = true;
		if (needRedraw) redrawableMaps.push(mapN);
	}
	if (drawMode == 2 && this_sync == 'auto' && redrawableMaps.length == 1) redrawableMaps = [];
	//console.log(getNow(), mIDX, 'redrawableMaps', redrawableMaps);

	// build redraw decison table
	var fitBoundDT = [];  for (var i=0; i<app.m; i++) fitBoundDT.push("    ");
	var drawMapsDT = [];  for (var i=0; i<app.m; i++) drawMapsDT.push("    ");
	for (var i=0; i<refitBoundableMaps.length; i++) 
		fitBoundDT[refitBoundableMaps[i].substr(refitBoundableMaps[i].length-1)] = refitBoundableMaps[i];
	if (needDrawing)
	for (var i=0; i<redrawableMaps.length; i++) 
		drawMapsDT[redrawableMaps[i].substr(redrawableMaps[i].length-1)] = redrawableMaps[i];
	//console.log(getNow(), mIDX, 'fitBoundDT: ', fitBoundDT);
	//console.log(getNow(), mIDX, 'drawMapsDT: ', drawMapsDT);
	
	// re arrange decison table
	var c = mIDX.substr(mIDX.length-1);
	var fitBoundST = [fitBoundDT[c]];
	var drawMapsST = [drawMapsDT[c]];
	for (var i=0; i<app.m; i++) {
		if (i != c) {
			fitBoundST.push(fitBoundDT[i]);
			drawMapsST.push(drawMapsDT[i]);
		}
	}
	//console.log(getNow(), mIDX, 'fitBoundST: ', fitBoundST);
	//console.log(getNow(), mIDX, 'drawMapsST: ', drawMapsST);
	
	if (needDrawing) {
		// build selectedGeoJSON
		app.selectedGeoJSON = {"type":"FeatureCollection", "features":[]};
		$.each(selectedFeatures, function(rIdx, feature) {
			app.selectedGeoJSON.features.push(app.receivedGeoJSON.features[feature[1]]);
		});
		CA = app.selectedGeoJSON;
		selectedFeatures = null;
		app.selectedBounds = mapBounds;
	}
	
	var mapN;
	for (var i=0; i<app.m; i++) {
		//console.log('app.m:', app.m, '    i:', i)
		// fitBounds 
		mapN = fitBoundST[i];
		if (mapN != "    ") {
			//console.log(getNow(), mapN, 'fit mapBounds: ', mapBounds);
			app[mapN].map.fitBounds(mapBounds);
		}
		// redraw maps
		mapN = drawMapsST[i];
		if (mapN != "    ") {
			//console.log(getNow(), mapN, 'drawing map started.');
			drawAmap(mapN, drawMode);
		}
	}
	// redraw charts
	for (var i=0; i<app.d; i++) {
		var mapN = "map" + i;
		//console.log(getNow(), mapN, 'drawing chart started.');
		drawAchart(mapN);
	}
}


// update global variable of selectedJSON from app.mapN.geojson.eachLayer
function updateSelectedGeoJSON(mIDX) {
	app.selectedGeoJSON = {"type":"FeatureCollection", "features":[]};
	app[mIDX].geojson.eachLayer(function(layer) {
		app.selectedGeoJSON.features.push(layer.feature);
	})
}


// draw map container
function drawMapContainer() {
	var html_maps = '';
	
	for (var i=0; i<app.m; i++) {
			html_maps += '<div id="map'+i+'" class="mapArea"></div><div class="MapBetween"></div>';
	}
	
	for (var i=0; i<app.d; i++) {
		html_maps += '<div id="mapD'+i+'" class="mapArea"></div><div class="MapBetween"></div>';
	}
	
	if (app.Distribution_INC2_different_cluster) {
		for (var i=0; i<app.nClusters; i++) {                                            // graph of clusters
			html_maps += '<div id="graphC'+i+'" class="mapArea"></div><div class="MapBetween"></div>';
		}
	}
	
	if (app.Temporal_change_in_neighborhoods) {
		html_maps += '<div id="map'+app.m+'" class="mapAreaLast"></div>';                // for the stacked area chart
	}
	
	$("#mapContainer").html(html_maps);
}


// Pading a value with leading zeors
function zeroPad(num, places) {
  var zero = places - num.toString().length + 1;
  return Array(+(zero > 0 && zero)).join("0") + num;
}


// Draw Stacked Area Chart
function drawStackedAreaChart(svgid, data) {

	var svg_html = ' &nbsp; &nbsp; &nbsp; &nbsp; Temporal change in neighborhoods<br><br><svg id="stackedAreaChart" ' +
				   'width="'+app.ChartWidth.replace('px','')+'" height="'+app.ChartHeight.replace('px','')+'"></svg>'
	$("#map"+app.m).html(svg_html);
	var svgid = "stackedAreaChart";

	var clone = JSON.parse(JSON.stringify(data));          // deep copy from data
	var svg = d3.select("#"+svgid),
		margin = {top: 20, right: 30, bottom: 20, left: 40},
		width = svg.attr("width") - margin.left - margin.right,
		height = svg.attr("height") - margin.top - margin.bottom;
	
	var xAxis = {domain: [], range: []};
	for (var i=0; i<data.length; i++) {
		xAxis.domain.push(data[i].date.getFullYear());
		xAxis.range.push(width*i*1.0/(data.length-1));
	}
	
	var ordinalScale = d3.scaleOrdinal().domain(xAxis.domain).range(xAxis.range),
		x = d3.scaleTime().range([0, width]),
		y = d3.scaleLinear().range([height, 0]),
		z = d3.scaleOrdinal()
			.range(app.colorGradient19);
	
	var stack = d3.stack();
	
	var area = d3.area()
		.x(function(d, i) { return x(d.data.date); })
		.y0(function(d) { return y(d[0]); })
		.y1(function(d) { return y(d[1]); });
	
	var g = svg.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");
	
	var keys = data.columns.slice(1);
	//console.log('data.length: '+data.length, 'keys: '+keys);

	// convert value to percent
	for (var i=0; i<data.length; i++) {
		var t = 0;
		for (var j=0; j<keys.length; j++) {
			var k = keys[j];
			t += data[i][k];
		}
		for (var j=0; j<keys.length; j++) {
			var k = keys[j];
			data[i][k] = data[i][k] / t;
		}
	}
	//console.log(data);
	
	x.domain(d3.extent(data, function(d) { return d.date; }));
	z.domain(keys);
	stack.keys(keys);
	
	var layer = g.selectAll(".layer")
		.data(stack(data))
		.enter().append("g")
		.attr("class", "layer");
	
	layer.append("path")
		//.attr("class", "area")
		.attr("class", "stackedArea")
		.style("fill", function(d) { return z(d.key); })
		.attr("d", area);
	
	layer.filter(function(d) { return d[d.length - 1][1] - d[d.length - 1][0] > 0.01; })
		.append("text")
		.attr("x", width - 6)
		.attr("y", function(d) { return y((d[d.length - 1][0] + d[d.length - 1][1]) / 2); })
		.attr("dy", ".35em")
		.style("font", "10px sans-serif")
		.style("text-anchor", "end")
		.text(function(d) {
			if (d.key.includes(app.nClusters.toString())) return "No Data";
			return d.key;
		});
	
	g.append("g")
		.attr("class", "axis axis--x")
		.attr("transform", "translate(0," + height + ")")
		.call(d3.axisBottom(ordinalScale).ticks(data.length));
	
	g.append("g")
		.attr("class", "axis axis--y")
		.call(d3.axisLeft(y).ticks(5, "%"));
	
	// Prep the tooltip bits, initial display is hidden
    var tooltip = svg.append("g")
		.attr("class", "tooltip")
		.style("opacity", 1.0)
		.style("display", "none");

	tooltip.append("rect")
		.attr("width", 120)
		.attr("height", 20)
		.attr("fill", "white")
		.style("opacity", 0.5);
	
	tooltip.append("text")
		.attr("x", 60)
		.attr("dy", "1.2em")
		.style("text-anchor", "middle")
		.attr("font-size", "12px")
		.attr("font-weight", "bold");

}


function paintDensity(mIDX, {rankIdx="", eventData="", chosenState=0, baseYear=""}) {

	var dIDX = mIDX.replace('map', 'mapD');                          // map0 -> mapD0,  map1 -> mapD1  ....
	var cluster = app.clickedCluster;
	var dYear = $("#"+dIDX+" select[name=yearSelect]").val();
	var item = dYear;
	var metroInterval = $('input[type=checkbox][name="'+mIDX+'-checkbox"]').is(":checked");
	Plotly.purge(dIDX+'_density_chart');
	
	// paint density chart means no fix axes
	$('input[type=checkbox][id="'+dIDX+'-fixAxes"]').prop("checked", false);
	
	var geojson;;
	if (item.startsWith('INC') && metroInterval) geojson = CA;
	else geojson = app.receivedGeoJSON;
	//console.log(dIDX, item, geojson);
	
	var geoData = [];
	for (var i=0; i<geojson.features.length; i++) {
		var properties = geojson.features[i].properties;
		if (properties['INC'] == -9999) continue;
		if (!item.startsWith('INC') && properties[item] != cluster) continue;
		geoData.push({tractid: properties.tractid, value: properties['INC']});
	}
	//console.log(dIDX, item, geoData);
	$("#"+dIDX+" .map_nPolygon").text(geoData.length + ' Polygons');
	
	geoData.sort((a, b) => a.value-b.value);
	
	var prvinc = -1;
	var n = 0;
	var counts = [];
	for (var i=0; i<geoData.length; i++) {
		var g = geoData[i];
		//var tractid  = g.tractid;
		var kdeinc   = g.value;
		if (kdeinc != prvinc) {
			if (prvinc != -1) {
				counts.push([n, prvinc]);
			}
			prvinc   = kdeinc;
			n    = 0;
		}
		n += 1;
	}
	if (prvinc != -1) {
		counts.push([n, prvinc]);
	}
	//console.log(dIDX, item, geoData.length, counts);
	
	// update app[mIDX].densityChart
	app[mIDX].densityChart.minX =  Number.MAX_VALUE;
	app[mIDX].densityChart.maxX = -Number.MAX_VALUE;
	app[mIDX].densityChart.minY =  Number.MAX_VALUE;
	app[mIDX].densityChart.maxY = -Number.MAX_VALUE;
	for (var i=0; i<counts.length; i++) {
		var count = counts[i];
		if (app[mIDX].densityChart.minX > count[1]) app[mIDX].densityChart.minX = count[1];
		if (app[mIDX].densityChart.maxX < count[1]) app[mIDX].densityChart.maxX = count[1];
		if (app[mIDX].densityChart.minY > count[0]) app[mIDX].densityChart.minY = count[0];
		if (app[mIDX].densityChart.maxY < count[0]) app[mIDX].densityChart.maxY = count[0];
	}
	//console.log(dIDX, item, app[mIDX].densityChart);
	
	var color = (item == 'INC') ? '#e377c2' : app.colorGradient1[cluster];
	var xaxisTitle = 'Index of Neighborhood Change (INC)'
	
	var data = [
		{
			'x': counts.map(function(o) { return o[1] }),
			'y': counts.map(function(o) { return o[0] }),
			'mode': 'lines',
			'fill': 'tozeroy',
			'name': 'dens',
			'hoverinfo': 'none',
			'showlegend': false,
			'line': {'shape': 'spline', 'smoothing': 1.3, 'color': color, 'width': 3}
		},
		{
			'x': counts.map(function(o) { return o[1] }),
			'y': counts.map(function(o) { return o[0] }),
			'mode': 'markers',
			'showlegend': false,
			'marker': {'symbol': 'circle', 'size': 8, 'color': color, 'opacity': 1.0},
			'name': '',
			'showlegend': false,
			'text': counts.map(function(o) { return o[0] + ' Polygons' }),
		},
    ];
	
	var layout = {
        'xaxis': {
			rangeslider: {                       // There is no event to fire for this 'rangeslider' in the API yet.
				visible: false,
			},
			'title': xaxisTitle
		},
        'yaxis': {
			fixedrange: true,
			'title': 'Frequency'
		},
		'title': (item != 'INC') ? 'Cluster ' + cluster + '  in <b>' + item + '</b>' : '<b>INC  Distribution</b>',
    };
	//console.log(layout);
	
	Plotly.plot(dIDX+'_density_chart', data, layout);
	
	var densityDiv = document.getElementById(dIDX+'_density_chart');
	densityDiv.on('plotly_relayout', function(eventData) {
		if (typeof eventData !== "object") return;
		if ('xaxis.autorange' in eventData && eventData['xaxis.autorange'] == true) {
			paintChoropleth(year, {});
			removeLayersOnMap(0);
			geoJsonBuild();
			return;
		}
		
		if (!('xaxis.range[0]' in eventData) || !('xaxis.range[1]' in eventData)) return;
		//console.log(eventData['xaxis.range[0]'], eventData['xaxis.range[1]']);
		var points = [];
		for (var i=0; i<kdeStates.length; i++) {
			if (kdeStates[i][1] < eventData['xaxis.range[0]']) continue;
			if (kdeStates[i][1] > eventData['xaxis.range[1]']) continue;
			points.push({pointIndex: kdeStates[i][0]});
		}
		//console.log(points);
		paintChoropleth(year, {});
		removeLayersOnMap(0);
		geoJsonBuild(points);
	});
}


// parint density chart of the graph of Clusters
function paintDensityGraphC(graphC, year, cluster) {
	var item = year;
	Plotly.purge(graphC+'_density_chart');
	
	// paint density chart means no fix axes
	$('input[type=checkbox][id="'+graphC+'-fixAxes"]').prop("checked", false);
	
	var geojson = app.receivedGeoJSON;
	
	var geoData = [];
	for (var i=0; i<geojson.features.length; i++) {
		var properties = geojson.features[i].properties;
		//console.log(properties)
		if (properties['INC'] == -9999) continue;
		if (properties[item] != cluster) continue;
		geoData.push({tractid: properties.tractid, value: properties['INC']});
	}
	//console.log(item, geoData);
	$("#"+graphC+" .map_nPolygon").text(geoData.length + ' Polygons');
	
	geoData.sort((a, b) => a.value-b.value);
	
	var prvinc = -1;
	var n = 0;
	var counts = [];
	for (var i=0; i<geoData.length; i++) {
		var g = geoData[i];
		//var tractid  = g.tractid;
		var kdeinc   = g.value;
		if (kdeinc != prvinc) {
			if (prvinc != -1) {
				counts.push([n, prvinc]);
			}
			prvinc   = kdeinc;
			n    = 0;
		}
		n += 1;
	}
	if (prvinc != -1) {
		counts.push([n, prvinc]);
	}
	//console.log(item, geoData.length, counts);
	
	// update app[graphC].densityChart
	app[graphC] = {densityChart: {minX: null, maxX: null, minY: null, maxY: null}}
	app[graphC].densityChart.minX =  Number.MAX_VALUE;
	app[graphC].densityChart.maxX = -Number.MAX_VALUE;
	app[graphC].densityChart.minY =  Number.MAX_VALUE;
	app[graphC].densityChart.maxY = -Number.MAX_VALUE;
	for (var i=0; i<counts.length; i++) {
		var count = counts[i];
		if (app[graphC].densityChart.minX > count[1]) app[graphC].densityChart.minX = count[1];
		if (app[graphC].densityChart.maxX < count[1]) app[graphC].densityChart.maxX = count[1];
		if (app[graphC].densityChart.minY > count[0]) app[graphC].densityChart.minY = count[0];
		if (app[graphC].densityChart.maxY < count[0]) app[graphC].densityChart.maxY = count[0];
	}
	//console.log(item, app[graphC].densityChart);
	
	var color = app.colorGradient1[cluster];
	var xaxisTitle = 'Index of Neighborhood Change (INC)'
	
	var data = [
		{
			'x': counts.map(function(o) { return o[1] }),
			'y': counts.map(function(o) { return o[0] }),
			'mode': 'lines',
			'fill': 'tozeroy',
			'name': 'dens',
			'hoverinfo': 'none',
			'showlegend': false,
			'line': {'shape': 'spline', 'smoothing': 1.3, 'color': color, 'width': 3}
		},
		{
			'x': counts.map(function(o) { return o[1] }),
			'y': counts.map(function(o) { return o[0] }),
			'mode': 'markers',
			'showlegend': false,
			'marker': {'symbol': 'circle', 'size': 8, 'color': color, 'opacity': 1.0},
			'name': '',
			'showlegend': false,
			'text': counts.map(function(o) { return o[0] + ' Polygons' }),
		},
	];
	
	var layout = {
        'xaxis': {
			rangeslider: {                       // There is no event to fire for this 'rangeslider' in the API yet.
				visible: false,
			},
			'title': xaxisTitle
		},
        'yaxis': {
			fixedrange: true,
			//range: [0, 3],
			'title': 'Frequency'
		},
		'title': '<b>Cluster ' + cluster + '</b>  in ' + item,
    };
	//console.log(layout);
	
	Plotly.plot(graphC+'_density_chart', data, layout);

}


function isPolygonInMapBounds(feature, baseLines, west, south, east, north) {

	// false, if the bounds of Polygon are completely out of Rectangle
	var geoBounds = d3.geoBounds(feature);
	if (geoBounds[0][0] > east  ||
		geoBounds[1][0] < west  ||
		geoBounds[0][1] > north ||
		geoBounds[1][1] < south) return false;
	
	// 1st: check the first point of Polygon against the Rectangle
	var coordinates = [];
	if (feature.geometry.type == 'Polygon') {
		coordinates.push(feature.geometry.coordinates[0][0]);
	}		
	if (feature.geometry.type == 'MultiPolygon') {
		for (var i=0; i<feature.geometry.coordinates.length; i++) {
			coordinates.push(feature.geometry.coordinates[i][0][0]);
		}
	}
	for (var i=0; i<coordinates.length; i++) {
		var point = coordinates[i];
		if (west  <= point[0] && point[0] <= east &&
			south <= point[1] && point[1] <= north) return true;
	}
	
	// 2nd: check the bottom left corner point in Rectangle against the Polygon          
	if (d3.geoContains(feature, [west, south])) return true;
	
	// 3rd: check the lines of Rectangle against the Polygon          
	var drawLines = lineify(feature);
	var crossPoints = [];
	for (var i=0; i<drawLines.geometries.length; i++) {
		for (var j=0; j<baseLines.geometries.length; j++) {
			var crossTest = lineStringsIntersect(drawLines.geometries[i], baseLines.geometries[j]);
			if (crossTest) {
				for (var k=0; k<crossTest.length; k++) {
					crossPoints.push(crossTest[k]);
				}
			}
		}
	}
	if (crossPoints.length != 0) return true;
	
	return false;
}


////////////////////////////////////////////////////////////////////////////////////////////
//intersection and geometry conversion functions form nathansnider's public fiddles       //
////////////////////////////////////////////////////////////////////////////////////////////

// corrected intersection code from https://github.com/maxogden/geojson-js-utils
// (using projected coordinates, because straight lat/lons will produce incorrect results)
// originally adapted from http://www.kevlindev.com/gui/math/intersection/Intersection.js
function lineStringsIntersect(l1, l2) {
    var intersects = [];
    for (var i = 0; i <= l1.coordinates.length - 2; ++i) {
        for (var j = 0; j <= l2.coordinates.length - 2; ++j) {
            var a1Latlon = L.latLng(l1.coordinates[i][1], l1.coordinates[i][0]),
                a2Latlon = L.latLng(l1.coordinates[i + 1][1], l1.coordinates[i + 1][0]),
                b1Latlon = L.latLng(l2.coordinates[j][1], l2.coordinates[j][0]),
                b2Latlon = L.latLng(l2.coordinates[j + 1][1], l2.coordinates[j + 1][0]),
                a1 = L.Projection.SphericalMercator.project(a1Latlon),
                a2 = L.Projection.SphericalMercator.project(a2Latlon),
                b1 = L.Projection.SphericalMercator.project(b1Latlon),
                b2 = L.Projection.SphericalMercator.project(b2Latlon),
                ua_t = (b2.x - b1.x) * (a1.y - b1.y) - (b2.y - b1.y) * (a1.x - b1.x),
                ub_t = (a2.x - a1.x) * (a1.y - b1.y) - (a2.y - a1.y) * (a1.x - b1.x),
                u_b = (b2.y - b1.y) * (a2.x - a1.x) - (b2.x - b1.x) * (a2.y - a1.y);
            if (u_b != 0) {
                var ua = ua_t / u_b,
                    ub = ub_t / u_b;
                if (0 <= ua && ua <= 1 && 0 <= ub && ub <= 1) {
                    var pt_x = a1.x + ua * (a2.x - a1.x),
                        pt_y = a1.y + ua * (a2.y - a1.y),
                        pt_xy = {
                            "x": pt_x,
                                "y": pt_y
                        },
                        pt_latlon = L.Projection.SphericalMercator.unproject(pt_xy);
                    intersects.push({
                        'type': 'Point',
                            'coordinates': [pt_latlon.lng, pt_latlon.lat]
                    });
                }
            }
        }
    }
    if (intersects.length == 0) intersects = false;
    return intersects;
}

//takes GeoJSON as input, creates a GeoJSON GeometryCollection of linestrings as output
// from https://gis.stackexchange.com/questions/170919/how-to-tell-if-a-geojson-path-intersects-with-another-feature-in-leaflet
function lineify(inputGeom) {
    var outputLines = {
        "type": "GeometryCollection",
            "geometries": []
    }
    switch (inputGeom.type) {
        case "GeometryCollection":
            //for (var i in inputGeom.geometries) {
			for (var i=0; i<inputGeom.geometries.length; i++) {
                var geomLines = lineify(inputGeom.geometries[i]);
                if (geomLines) {
					for (var j=0; j<geomLines.geometries.length; j++) {
                        outputLines.geometries.push(geomLines.geometries[j]);
                    }
                } else {
                    outputLines = false;
                }
            }
            break;
        case "Feature":
            var geomLines = lineify(inputGeom.geometry);
            if (geomLines) {
				for (var j=0; j<geomLines.geometries.length; j++) {
                    outputLines.geometries.push(geomLines.geometries[j]);
                }
            } else {
                outputLines = false;
            }
            break;
        case "FeatureCollection":
			for (var i=0; i<inputGeom.features.length; i++) {
                var geomLines = lineify(inputGeom.features[i].geometry);
                if (geomLines) {
                    //for (var j in geomLines.geometries) {
					for (var j=0; j<geomLines.geometries.length; j++) {
                        outputLines.geometries.push(geomLines.geometries[j]);
                    }
                } else {
                    outputLines = false;
                }
            }
            break;
        case "LineString":
            outputLines.geometries.push(inputGeom);
            break;
        case "MultiLineString":
        case "Polygon":
            for (var i=0; i<inputGeom.coordinates.length; i++) {
                outputLines.geometries.push({
                    "type": "LineString",
                        "coordinates": inputGeom.coordinates[i]
                });
            }
            break;
        case "MultiPolygon":
			for (var i=0; i<inputGeom.coordinates.length; i++) {
				for (var j=0; j<inputGeom.coordinates[i].length; j++) {
                    outputLines.geometries.push({
                        "type": "LineString",
                            "coordinates": inputGeom.coordinates[i][j]
                    });
                }
            }
            break;
        default:
            outputLines = false;
    }
    return outputLines;
}