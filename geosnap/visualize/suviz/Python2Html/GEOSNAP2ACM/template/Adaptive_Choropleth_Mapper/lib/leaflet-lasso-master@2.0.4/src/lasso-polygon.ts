import L from 'leaflet';

export class LassoPolygon extends L.Layer {
    readonly polyline: L.Polyline;
    readonly polygon: L.Polygon;

    constructor(latlngs: L.LatLngExpression[], options?: L.PolylineOptions) {
        super();

        this.polyline = L.polyline(latlngs, options);
        this.polygon = L.polygon(latlngs, { ...options, weight: 0 });
    }

    onAdd(map: L.Map): this {
        this.polyline.addTo(map);
        this.polygon.addTo(map);

        return this;
    }

    onRemove(): this {
        this.polyline.remove();
        this.polygon.remove();

        return this;
    }

    addLatLng(latlng: L.LatLngExpression): this {
        this.polyline.addLatLng(latlng);
        this.polygon.addLatLng(latlng);

        return this;
    }

    getLatLngs(): L.LatLng[] {
        return this.polygon.getLatLngs()[0] as L.LatLng[];
    }

    toGeoJSON(): GeoJSON.Feature<GeoJSON.Polygon> {
        return this.polygon.toGeoJSON() as GeoJSON.Feature<GeoJSON.Polygon>;
    }
}