# leaflet-lasso

True lasso selection plugin for Leaflet. [Demo](http://zakjan.github.io/leaflet-lasso/)

<img src="docs/screenshot@2x.jpg" alt="Screenshot" width="640" height="320">

Supports all Leaflet vector layers:

- Marker
- CircleMarker
- Circle
- Polyline
- Polyline with multiple segments
- Rectangle
- Polygon
- Polygon with hole
- Polygon with multiple segments
- Polygon with multiple segments and holes

Selection modes:

- contain - entire shape must be in lasso polygon (default)
- intersect - any part of shape can be in lasso polygon

## Install

```
npm install leaflet-lasso
import "leaflet-lasso"
```

or

```
<script src="https://unpkg.com/leaflet-lasso@2.0.4/dist/leaflet-lasso.umd.min.js"></script>
```

## Usage

For detailed API, please see exported TypeScript typings.

### Handler

Use for custom activation.

```
interface LassoHandlerOptions {
    polygon?: L.PolylineOptions,
    intersect?: boolean;
}
```

```
const lasso = L.lasso(map, options);
yourCustomButton.addEventListener('click', () => {
    lasso.enable();
});
```

### Control

Use for default control.

```
type LassoControlOptions = LassoHandlerOptions & L.ControlOptions;
```

```
L.control.lasso(options).addTo(map);
```

### Finished event

Listen for this event to receive matching Leaflet layers.

```
interface LassoHandlerFinishedEventData {
    latLngs: L.LatLng[];
    layers: L.Layer[];
}
```

```
map.on('lasso.finished', (event: LassoHandlerFinishedEventData) => {
    console.log(event.layers);
});
```

## Thanks

Icon by @Falke-Design
