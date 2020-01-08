import { LassoPolygon } from './lasso-polygon';

describe('LassoPolygon', () => {
    it('constructs with the same latlngs in both polyline and polygon', () => {
        const polygon = new LassoPolygon([[0, 0], [1, 0], [1, 1], [0, 1]]);

        expect(polygon.polyline.getLatLngs()).toEqual(polygon.polygon.getLatLngs()[0]);
    });

    it('adds a latlng to both polyline and polygon', () => {
        const polygon = new LassoPolygon([[0, 0], [1, 0], [1, 1], [0, 1]]);
        polygon.addLatLng([1, 1]);

        expect(polygon.polyline.getLatLngs()).toEqual(polygon.polygon.getLatLngs()[0]);
    });
})
