<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Leaflet Lasso</title>
    <script src="https://unpkg.com/leaflet@1.5.1/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>
    <script src="https://unpkg.com/leaflet-lasso@2.0.4/dist/leaflet-lasso.umd.js"></script>
    <!-- <script src="../dist/leaflet-lasso.umd.js"></script> -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.5.1/dist/leaflet.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css">
    <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
    <style>
        #github-corner {
            position: absolute;
            top: 0;
            right: 0;
        }
        #map {
            width: 640px;
            height: 320px;
            float: left;
        }
        #sidebar {
            margin-left: 650px;
        }
        .selected {
            filter: hue-rotate(135deg);
        }
    </style>
</head>
<body>
    <a href="https://github.com/zakjan/leaflet-lasso" id="github-corner">
        <img width="149" height="149" src="https://github.blog/wp-content/uploads/2008/12/forkme_right_darkblue_121621.png?resize=149%2C149">
    </a>
    <div class="container">
        <h1>leaflet-lasso</h1>
        <p>True lasso selection plugin for Leaflet</p>
        <hr>

        <div id="map"></div>
        <div id="sidebar">
            <div>
                <button id="toggleLasso" type="button" class="btn btn-primary btn-sm">Toggle Lasso</button>
                <label class="ml-3"><input type="radio" name="containOrIntersect" id="contain" checked> Contain</label>
                <label class="ml-2"><input type="radio" name="containOrIntersect" id="intersect"> Intersect</label>
            </div>
            <br>
            <div id="lassoEnabled">Disabled</div>
            <br>
            <div id="lassoResult"></div>
        </div>
    </div>

    <script type="module">
        const mapElement = document.querySelector('#map');
        const toggleLasso = document.querySelector('#toggleLasso');
        const contain = document.querySelector('#contain');
        const intersect = document.querySelector('#intersect');
        const lassoEnabled = document.querySelector('#lassoEnabled');
        const lassoResult = document.querySelector('#lassoResult');

        const map = L.map(mapElement, { center: [0, 0], zoom: 0 });
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        const lassoControl = L.control.lasso().addTo(map);

        // the same layers as in unit test
        const startLatLng = [51.5, -0.11];
        const latDelta = 0.01;
        const lngDelta = latDelta * 1.75;
        const latSmallDelta = 0.002;
        const lngSmallDelta = latSmallDelta * 1.75;
        const markers = new Array(9).fill(undefined).map((_, i) => L.marker([startLatLng[0] + Math.floor(i / 3) * latDelta, startLatLng[1] + (i % 3) * lngDelta]));
        const circleMarker = L.circleMarker([startLatLng[0] + latDelta * 2, startLatLng[1] + lngDelta * 3], { radius: 21 });
        const circle = L.circle([startLatLng[0] + latDelta * 2, startLatLng[1] + lngDelta * 4], { radius: 250 });
        const polyline = (latLng => L.polyline([
            [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
            [latLng[0] + latSmallDelta, latLng[1] - lngSmallDelta],
            [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
            [latLng[0] - latSmallDelta, latLng[1] + lngSmallDelta],
        ]))([startLatLng[0] + latDelta * 1, startLatLng[1] + lngDelta * 3]);
        const multiPolyline = (latLng => L.polyline([
            [
                [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
                [latLng[0] + latSmallDelta, latLng[1] - lngSmallDelta],
                [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
                [latLng[0] - latSmallDelta, latLng[1] + lngSmallDelta],
            ],
            [
                [latLng[0] - latSmallDelta / 2, latLng[1] - lngSmallDelta / 2],
                [latLng[0] + latSmallDelta / 2, latLng[1] - lngSmallDelta / 2],
                [latLng[0] + latSmallDelta / 2, latLng[1] + lngSmallDelta / 2],
                [latLng[0] - latSmallDelta / 2, latLng[1] + lngSmallDelta / 2],
            ],
        ]))([startLatLng[0] + latDelta * 1, startLatLng[1] + lngDelta * 4]);
        const rectangle = (latLng => L.rectangle([
            [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
            [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
        ]))([startLatLng[0], startLatLng[1] + lngDelta * 3]);
        const polygon = (latLng => L.polygon([
            [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
            [latLng[0] + latSmallDelta, latLng[1] - lngSmallDelta],
            [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
            [latLng[0] - latSmallDelta, latLng[1] + lngSmallDelta],
        ]))([startLatLng[0], startLatLng[1] + lngDelta * 4]);
        const holedPolygon = (latLng => L.polygon([
            [
                [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
                [latLng[0] - latSmallDelta, latLng[1] + lngSmallDelta],
                [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
                [latLng[0] + latSmallDelta, latLng[1] - lngSmallDelta],
            ],
            [
                [latLng[0] - latSmallDelta / 2, latLng[1] - lngSmallDelta / 2],
                [latLng[0] - latSmallDelta / 2, latLng[1] + lngSmallDelta / 2],
                [latLng[0] + latSmallDelta / 2, latLng[1] + lngSmallDelta / 2],
                [latLng[0] + latSmallDelta / 2, latLng[1] - lngSmallDelta / 2],
            ],
        ]))([startLatLng[0], startLatLng[1] + lngDelta * 5]);
        const multiPolygon = (latLng => L.polygon([
            [
                [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
                [latLng[0] - latSmallDelta, latLng[1]],
                [latLng[0], latLng[1]],
                [latLng[0], latLng[1] - lngSmallDelta],
            ],
            [
                [latLng[0], latLng[1]],
                [latLng[0], latLng[1] + lngSmallDelta],
                [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
                [latLng[0] + latSmallDelta, latLng[1]],
            ],
        ]))([startLatLng[0], startLatLng[1] + lngDelta * 6]);
        const holedMultiPolygon = (latLng => L.polygon([
            [
                [
                    [latLng[0] - latSmallDelta, latLng[1] - lngSmallDelta],
                    [latLng[0] - latSmallDelta, latLng[1]],
                    [latLng[0], latLng[1]],
                    [latLng[0], latLng[1] - lngSmallDelta],
                ],
                [
                    [latLng[0] - latSmallDelta / 4 * 3, latLng[1] - lngSmallDelta / 4 * 3],
                    [latLng[0] - latSmallDelta / 4 * 3, latLng[1] - lngSmallDelta / 4],
                    [latLng[0] - latSmallDelta / 4, latLng[1] - lngSmallDelta / 4],
                    [latLng[0] - latSmallDelta / 4, latLng[1] - lngSmallDelta / 4 * 3],
                ],
            ],
            [
                [
                    [latLng[0], latLng[1]],
                    [latLng[0], latLng[1] + lngSmallDelta],
                    [latLng[0] + latSmallDelta, latLng[1] + lngSmallDelta],
                    [latLng[0] + latSmallDelta, latLng[1]],
                ],
                [
                    [latLng[0] + latSmallDelta / 4 * 3, latLng[1] + lngSmallDelta / 4 * 3],
                    [latLng[0] + latSmallDelta / 4 * 3, latLng[1] + lngSmallDelta / 4],
                    [latLng[0] + latSmallDelta / 4, latLng[1] + lngSmallDelta / 4],
                    [latLng[0] + latSmallDelta / 4, latLng[1] + lngSmallDelta / 4 * 3],
                ],
            ],
        ]))([startLatLng[0], startLatLng[1] + lngDelta * 7]);
        const layers = [
            ...markers,
            circleMarker,
            circle,
            polyline,
            multiPolyline,
            rectangle,
            polygon,
            holedPolygon,
            multiPolygon,
            holedMultiPolygon,
        ];

        const featureGroup = L.featureGroup(layers).addTo(map);
        map.fitBounds(featureGroup.getBounds(), { animate: false });

        function resetSelectedState() {
            map.eachLayer(layer => {
                if (layer instanceof L.Marker) {
                    layer.setIcon(new L.Icon.Default());
                } else if (layer instanceof L.Path) {
                    layer.setStyle({ color: '#3388ff' });
                }
            });

            lassoResult.innerHTML = '';
        }
        function setSelectedLayers(layers) {
            resetSelectedState();

            layers.forEach(layer => {
                if (layer instanceof L.Marker) {
                    layer.setIcon(new L.Icon.Default({ className: 'selected '}));
                } else if (layer instanceof L.Path) {
                    layer.setStyle({ color: '#ff4620' });
                }
            });

            lassoResult.innerHTML = layers.length ? `Selected ${layers.length} layers` : '';
        }

        map.on('mousedown', () => {
            resetSelectedState();
        });
        map.on('lasso.finished', event => {
            setSelectedLayers(event.layers);
        });
        map.on('lasso.enabled', () => {
            lassoEnabled.innerHTML = 'Enabled';
            resetSelectedState();
        });
        map.on('lasso.disabled', () => {
            lassoEnabled.innerHTML = 'Disabled';
        });

        toggleLasso.addEventListener('click', () => {
            if (lassoControl.enabled()) {
                lassoControl.disable();
            } else {
                lassoControl.enable();
            }
        });
        contain.addEventListener('change', () => {
            lassoControl.setOptions({ intersect: intersect.checked });
        });
        intersect.addEventListener('change', () => {
            lassoControl.setOptions({ intersect: intersect.checked });
        });
    </script>
</body>
</html>
