import L from 'leaflet';
import './index';

describe('index', () => {
    let container: HTMLElement;
    let map: L.Map;
    
    beforeEach(() => {
        container = document.createElement('div');
        container.style.width = '400px';
        container.style.height = '400px';

        map = L.map(container, { renderer: new L.SVG(), center: [0, 0], zoom: 12 });
    });

    it('exports L.Lasso', () => {
        const lassoHandler: L.Lasso = new L.Lasso(map);
        expect(lassoHandler).toBeInstanceOf(L.Lasso);
    });

    it('exports L.lasso', () => {
        const lassoHandler: L.Lasso = L.lasso(map);
        expect(lassoHandler).toBeInstanceOf(L.Lasso);
    });

    it('exports L.Control.Lasso', () => {
        const lassoControl: L.Control.Lasso = new L.Control.Lasso().addTo(map);
        expect(lassoControl).toBeInstanceOf(L.Control.Lasso);
    });

    it('exports L.control.lasso', () => {
        const lassoControl: L.Control.Lasso = L.control.lasso().addTo(map);
        expect(lassoControl).toBeInstanceOf(L.Control.Lasso);
    });
});
