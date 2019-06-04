#Leaflet.loader

Leaflet.loader is a [Leaflet](https://github.com/Leaflet/Leaflet) plugin. It provides a loading screen disabling access to the map.
The loading screen can easily be hidden and access to the map granted by calling a single function.

Check out the [Demo](http://eclipse1979.github.io/leaflet-loader/example/leaflet-loader.html).

## Using Leaflet.loader :

Using Leaflet.loader is very easy.

Add the css and the javascript in the header of your html page :
    
    <link rel="stylesheet" href="leaflet.loader.css" />


    <script src="leaflet.loader.js"></script>

Then create the loader using the function :

    var loader = L.control.loader().addTo(map);
    
To disable the loading screen, simply call the function `hide()` when wanted:

    loader.hide();

## Methods :

* `hide():` hides the loader and gives access to the map 