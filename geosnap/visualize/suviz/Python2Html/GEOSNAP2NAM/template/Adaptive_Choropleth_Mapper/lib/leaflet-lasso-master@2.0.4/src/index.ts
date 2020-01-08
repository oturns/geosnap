import L from 'leaflet';
import { LassoHandler } from './lasso-handler';
import { LassoControl } from './lasso-control';

declare module 'leaflet' {
    type Lasso = LassoHandler;
    let Lasso: typeof LassoHandler;

    let lasso: (...args: ConstructorParameters<typeof LassoHandler>) => LassoHandler;
    
    namespace Control {
        type Lasso = LassoControl;
        let Lasso: typeof LassoControl;
    }

    namespace control {
        let lasso: (...args: ConstructorParameters<typeof LassoControl>) => LassoControl;
    }
}

L.Lasso = LassoHandler;
L.lasso = (...args: ConstructorParameters<typeof LassoHandler>) => new LassoHandler(...args);

L.Control.Lasso = LassoControl;
L.control.lasso = (...args: ConstructorParameters<typeof LassoControl>) => new LassoControl(...args);

export * from './lasso-handler';
export * from './lasso-control';