// scipy javascript equivalent
// https://github.com/fernandezajp/PyExtJS

(function() {
window.stats = function stats() {
}
stats.prototype = {
    _slope: 0,
    
    get_slope: function stats$get_slope() {
        return this._slope;
    },
    
    _intercept: 0,
    
    get_intercept: function stats$get_intercept() {
        return this._intercept;
    },
    
    linregress: function stats$linregress(x, y) {
        var data = new Array(x.length);
        for (var i = 0; i < x.length; i++) {
            data[i] = new PolyRegression.Pair(x[i], y[i]);
        }
        var polysolve = new PolyRegression.Matrix();
        var terms = polysolve.computeCoefficients(data, 1);
        this._intercept = terms[0];
        this._slope = terms[1];
    }
}

window.interpolate = function interpolate() {
}
interpolate.prototype = {
    _x: null,
    _y: null,
    
    interp1d: function interpolate$interp1d(x, y) {
        /// </param>
        this._x = x;
        this._y = y;
    },
    
    eval: function interpolate$eval(valueTointerpolate) {
        var type = Type.getInstanceType(valueTointerpolate).get_name();
        if (type === 'Array') {
            var inputarray = valueTointerpolate;
            var returns = new Array(inputarray.length);
            for (var i = 0; i < returns.length; i++) {
                returns[i] = this._f(inputarray[i]);
            }
            return returns;
        }
        else {
            var input = valueTointerpolate;
            return this._f(input);
        }
    },
    
    _f: function interpolate$_f(valueTointerpolate) {
        var yval = 0;
        for (var i = 0; i < this._x.length - 1; i++) {
            if (valueTointerpolate >= this._x[i] && valueTointerpolate < this._x[i + 1]) {
                yval = this._y[i] + (valueTointerpolate - this._x[i]) * (this._y[i + 1] - this._y[i]) / (this._x[i + 1] - this._x[i]);
                return yval;
            }
        }
        return 0;
    }
}


stats.registerClass('stats');
interpolate.registerClass('interpolate');
})();
