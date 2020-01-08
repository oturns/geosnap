declare module 'circle-to-polygon' {
    const circleToPolygon: (center: GeoJSON.Position, radius: number, numberOfSegments?: number) => GeoJSON.Polygon;
    export default circleToPolygon;
}