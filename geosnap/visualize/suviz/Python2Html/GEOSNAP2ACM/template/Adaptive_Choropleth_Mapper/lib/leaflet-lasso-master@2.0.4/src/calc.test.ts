import L from 'leaflet';
import { LassoPolygon } from './lasso-polygon';
import { getLayersInPolygon } from './calc';

describe('getLayersInPolygon', () => {
    const zoom = 13;

    // the same layers as in demo page
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

    function createPolygon(center: L.LatLng, options: {scale?: number, ratio?: number} = {}) {
        const scale = options.scale || 1;
        const ratio = options.ratio || 1;
        const inversedRatio = 1 / ratio;

        return new LassoPolygon([
            [center.lat - latSmallDelta * scale * ratio, center.lng - lngSmallDelta * scale * inversedRatio],
            [center.lat - latSmallDelta * scale * ratio, center.lng + lngSmallDelta * scale * inversedRatio],
            [center.lat + latSmallDelta * scale * ratio, center.lng + lngSmallDelta * scale * inversedRatio],
            [center.lat + latSmallDelta * scale * ratio, center.lng - lngSmallDelta * scale * inversedRatio],
        ]).toGeoJSON().geometry;
    }

    it('returns Marker in larger polygon', () => {
        const lassoPolygon = createPolygon(markers[0].getLatLng());
        const expectedResult = [markers[0]];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns Markers in larger polygon', () => {
        const lassoPolygon = createPolygon(markers[4].getLatLng(), { scale: 6 });
        const expectedResult = markers;
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns Markers in irregular larger polygon', () => {
        // plus shape
        const lassoPolygon = new LassoPolygon([
            [markers[7].getLatLng().lat + latSmallDelta, markers[7].getLatLng().lng - lngSmallDelta],
            [markers[7].getLatLng().lat + latSmallDelta, markers[7].getLatLng().lng + lngSmallDelta],
            [markers[4].getLatLng().lat + latSmallDelta, markers[4].getLatLng().lng + lngSmallDelta],
            [markers[5].getLatLng().lat + latSmallDelta, markers[5].getLatLng().lng + lngSmallDelta],
            [markers[5].getLatLng().lat - latSmallDelta, markers[5].getLatLng().lng + lngSmallDelta],
            [markers[4].getLatLng().lat - latSmallDelta, markers[4].getLatLng().lng + lngSmallDelta],
            [markers[1].getLatLng().lat - latSmallDelta, markers[1].getLatLng().lng + lngSmallDelta],
            [markers[1].getLatLng().lat - latSmallDelta, markers[1].getLatLng().lng - lngSmallDelta],
            [markers[4].getLatLng().lat - latSmallDelta, markers[4].getLatLng().lng - lngSmallDelta],
            [markers[3].getLatLng().lat - latSmallDelta, markers[3].getLatLng().lng - lngSmallDelta],
            [markers[3].getLatLng().lat + latSmallDelta, markers[3].getLatLng().lng - lngSmallDelta],
            [markers[4].getLatLng().lat + latSmallDelta, markers[4].getLatLng().lng - lngSmallDelta],
        ]).toGeoJSON().geometry;
        const expectedResult = [markers[1], markers[3], markers[4], markers[5], markers[7]];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns CircleMarker in larger polygon', () => {
        const lassoPolygon = createPolygon(circleMarker.getLatLng(), { scale: 1.2 });
        const expectedResult = [circleMarker];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return CircleMarker in smaller polygon', () => {
        const lassoPolygon = createPolygon(circleMarker.getLatLng(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns CircleMarker with intersection', () => {
        const lassoPolygon = createPolygon(circleMarker.getLatLng(), { ratio: 0.5 });
        const expectedResult = [circleMarker];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns Circle in larger polygon', () => {
        const lassoPolygon = createPolygon(circle.getLatLng(), { scale: 1.2 });
        const expectedResult = [circle];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return Circle in smaller polygon', () => {
        const lassoPolygon = createPolygon(circle.getLatLng(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns Circle with intersection', () => {
        const lassoPolygon = createPolygon(circle.getLatLng(), { ratio: 0.5 });
        const expectedResult = [circle];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns Polyline in larger polygon', () => {
        const lassoPolygon = createPolygon(polyline.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [polyline];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return Polyline in smaller polygon', () => {
        const lassoPolygon = createPolygon(polyline.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns Polyline with intersection', () => {
        const lassoPolygon = createPolygon(polyline.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [polyline];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns multi Polyline in larger polygon', () => {
        const lassoPolygon = createPolygon(multiPolyline.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [multiPolyline];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return multi Polyline in smaller polygon', () => {
        const lassoPolygon = createPolygon(multiPolyline.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns multi Polyline with intersection', () => {
        const lassoPolygon = createPolygon(multiPolyline.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [multiPolyline];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns Rectangle in larger polygon', () => {
        const lassoPolygon = createPolygon(rectangle.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [rectangle];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return Rectangle in smaller polygon', () => {
        const lassoPolygon = createPolygon(rectangle.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns Rectangle with intersection', () => {
        const lassoPolygon = createPolygon(rectangle.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [rectangle];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns Polygon in larger polygon', () => {
        const lassoPolygon = createPolygon(polygon.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [polygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return Polygon in smaller polygon', () => {
        const lassoPolygon = createPolygon(polygon.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns Polygon with intersection', () => {
        const lassoPolygon = createPolygon(polygon.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [polygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns holed Polygon in larger polygon', () => {
        const lassoPolygon = createPolygon(holedPolygon.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [holedPolygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return holed Polygon in smaller polygon', () => {
        const lassoPolygon = createPolygon(holedPolygon.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns holed Polygon with intersection', () => {
        const lassoPolygon = createPolygon(holedPolygon.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [holedPolygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns multi Polygon in larger polygon', () => {
        const lassoPolygon = createPolygon(multiPolygon.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [multiPolygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return multi Polygon in smaller polygon', () => {
        const lassoPolygon = createPolygon(multiPolygon.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns multi Polygon with intersection', () => {
        const lassoPolygon = createPolygon(multiPolygon.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [multiPolygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });

    it('returns holed multi Polygon in larger polygon', () => {
        const lassoPolygon = createPolygon(holedMultiPolygon.getBounds().getCenter(), { scale: 1.2 });
        const expectedResult = [holedMultiPolygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('does not return holed multi Polygon in smaller polygon', () => {
        const lassoPolygon = createPolygon(holedMultiPolygon.getBounds().getCenter(), { scale: 0.8 });
        const expectedResult: L.Layer[] = [];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom });
        expect(result).toEqual(expectedResult);
    });

    it('returns holed multi Polygon with intersection', () => {
        const lassoPolygon = createPolygon(holedMultiPolygon.getBounds().getCenter(), { ratio: 0.5 });
        const expectedResult = [holedMultiPolygon];
        const result = getLayersInPolygon(lassoPolygon, layers, { zoom: zoom, intersect: true });
        expect(result).toEqual(expectedResult);
    });
});