import L from 'leaflet';
import { LassoHandler, LassoHandlerOptions } from './lasso-handler';
import './lasso-control.css';

export type LassoControlOptions = LassoHandlerOptions & L.ControlOptions;

export class LassoControl extends L.Control {
    options: LassoControlOptions = {
        position: 'topright',
    };

    private lasso?: LassoHandler;

    constructor(options: LassoControlOptions = {}) {
        super();

        L.Util.setOptions(this, options);
    }

    setOptions(options: LassoControlOptions) {
        this.options = { ...this.options, ...options };
        
        if (this.lasso) {
            this.lasso.setOptions(this.options);
        }
    }

    onAdd(map: L.Map) {
        this.lasso = new LassoHandler(map, this.options);

        const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control') as HTMLDivElement;
        const button = L.DomUtil.create('a', 'leaflet-control-lasso', container) as HTMLAnchorElement;
        button.href = '#';
        button.title = 'Toggle Lasso';
        button.setAttribute('role', 'button');
        button.setAttribute('aria-label', button.title);

        L.DomEvent.addListener(button, 'click', this.toggle, this);

        return container;
    }

    enabled() {
        if (!this.lasso) {
            return false;
        }
        return this.lasso.enabled();
    }

    enable() {
        if (!this.lasso) {
            return;
        }
        this.lasso.enable();
    }

    disable() {
        if (!this.lasso) {
            return;
        }
        this.lasso.disable();
    }

    toggle() {
        if (!this.lasso) {
            return;
        }
        this.lasso.toggle();
    }
}
