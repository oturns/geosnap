import L from 'leaflet';
import Terraformer from 'terraformer';
import circleToPolygon from 'circle-to-polygon';

function getCircleMarkerRadius(circleMarker: L.CircleMarker, crs: L.CRS, zoom: number) {
    const latLng = circleMarker.getLatLng();
    const point = crs.latLngToPoint(latLng, zoom);
    const delta = circleMarker.getRadius() / Math.SQRT2;
    const topLeftPoint = L.point([point.x - delta, point.y - delta]);
    const topLeftLatLng = crs.pointToLatLng(topLeftPoint, zoom);
    const radius = crs.distance(latLng, topLeftLatLng);
    return radius;
}

function circleToGeoJSONGeometry(latLng: L.LatLng, radius: number) {
    // Terraformer result is incorrect, see https://github.com/Esri/terraformer/issues/321
    // return new Terraformer.Circle(L.GeoJSON.latLngToCoords(latLng), radius).geometry;

    return circleToPolygon(L.GeoJSON.latLngToCoords(latLng), radius);
}

export function getLayersInPolygon(polygon: GeoJSON.Polygon, layers: L.Layer[], options: { zoom?: number, crs?: L.CRS, intersect?: boolean } = {}) {
    const crs = options.crs || L.CRS.EPSG3857;
    const polygonGeometry = new Terraformer.Primitive(polygon);

    const selectedLayers = layers.filter(layer => {
        let layerGeometry: GeoJSON.GeometryObject;

        if (layer instanceof L.Circle) {
            const latLng = layer.getLatLng();
            const radius = layer.getRadius();
            layerGeometry = circleToGeoJSONGeometry(latLng, radius);
        } else if (layer instanceof L.CircleMarker) {
            if (options.zoom != undefined) {
                const latLng = layer.getLatLng();
                const radius = getCircleMarkerRadius(layer, crs, options.zoom);
                layerGeometry = circleToGeoJSONGeometry(latLng, radius);
            } else {
                console.warn("Zoom is required for calculating CircleMarker polygon, falling back to center point only");
                layerGeometry = layer.toGeoJSON().geometry;
            }
        } else if (layer instanceof L.Marker || layer instanceof L.Polyline) {
            layerGeometry = layer.toGeoJSON().geometry;
        } else {
            return false;
        }

        return options.intersect && layerGeometry.type !== "Point" ?
            polygonGeometry.intersects(layerGeometry) :
            polygonGeometry.contains(layerGeometry);
    });
    
    return selectedLayers;
}