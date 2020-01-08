import L from 'leaflet';
import { LassoControl } from './lasso-control';

describe('LassoControl', () => {
    let container: HTMLElement;
    let map: L.Map;
    let lasso: LassoControl;
    
    beforeEach(() => {
        container = document.createElement('div');
        container.style.width = '400px';
        container.style.height = '400px';

        map = L.map(container, { renderer: new L.SVG(), center: [0, 0], zoom: 12 });
        lasso = new LassoControl().addTo(map);
    });

    it('setOptions method allows updating options', () => {
        lasso.setOptions({ intersect: true });
        expect(lasso.options.intersect).toEqual(true);
    });

    it('enable method enables handler', () => {
        lasso.enable();
        expect(lasso.enabled()).toEqual(true);
    });

    it('enable method enables handler', () => {
        lasso.enable();
        lasso.disable();
        expect(lasso.enabled()).toEqual(false);
    });

    it('toggle method toggles handler', () => {
        lasso.toggle();
        expect(lasso.enabled()).toEqual(true);

        lasso.toggle();
        expect(lasso.enabled()).toEqual(false);
    });

    it('clicking button toggles handler', () => {
        const button = container.querySelector('.leaflet-control-lasso') as HTMLElement;

        button.click();
        expect(lasso.enabled()).toEqual(true);

        button.click();
        expect(lasso.enabled()).toEqual(false);
    });
});
