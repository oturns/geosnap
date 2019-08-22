// javascript utility
// https://github.com/fernandezajp/PyExtJS

(function() {

Type.registerNamespace('PolyRegression');

PolyRegression.Matrix = function PolyRegression_Matrix() {
}
PolyRegression.Matrix.prototype = {
    _pairs: null,
    
    computeCoefficients: function PolyRegression_Matrix$computeCoefficients(data, degree) {
        degree += 1;
        var n = data.length;
        var r, c;
        var rs = 2 * degree - 1;
        var m = new Array(degree);
        for (var i = 0; i < degree; i++) {
            var mm = new Array(degree + 1);
            for (var j = 0; j <= degree; j++) {
                mm[j] = 0;
            }
            m[i] = mm;
        }
        var mpc = new Array(rs);
        for (var i = 0; i < rs; i++) {
            mpc[i] = 0;
        }
        mpc[0] = n;
        for (var i = 0; i < data.length; i++) {
            var pr = data[i];
            for (r = 1; r < rs; r++) {
                mpc[r] += Math.pow(pr.get_x(), r);
            }
            m[0][degree] += pr.get_y();
            for (r = 1; r < degree; r++) {
                m[r][degree] += Math.pow(pr.get_x(), r) * pr.get_y();
            }
        }
        for (r = 0; r < degree; r++) {
            for (c = 0; c < degree; c++) {
                m[r][c] = mpc[r + c];
            }
        }
        this._echelonize(m);
        var terms = new Array(degree);
        for (var i = 0; i < m.length; i++) {
            var mc = m[i];
            terms[i] = mc[degree];
        }
        this._pairs = terms;
        return terms;
    },
    
    eval: function PolyRegression_Matrix$eval(x) {
        var y = 0;
        var power = 0;
        for (var i = 0; i < this._pairs.length; i++) {
            y += this._pairs[i] * Math.pow(x, power++);
        }
        return y;
    },
    
    _echelonize: function PolyRegression_Matrix$_echelonize(A) {
        var n = A.length;
        var m = A[0].length;
        var i = 0;
        var j = 0;
        var k;
        var swap;
        while (i < n && j < m) {
            k = i;
            while (k < n && !A[k][j]) {
                k++;
            }
            if (k < n) {
                if (k !== i) {
                    swap = A[i];
                    A[i] = A[k];
                    A[k] = swap;
                }
                if (A[i][j] !== 1) {
                    this._divide(A, i, j, m);
                }
                this._eliminate(A, i, j, n, m);
                i++;
            }
            j++;
        }
    },
    
    _divide: function PolyRegression_Matrix$_divide(A, i, j, m) {
        for (var q = j + 1; q < m; q++) {
            A[i][q] /= A[i][j];
        }
        A[i][j] = 1;
    },
    
    _eliminate: function PolyRegression_Matrix$_eliminate(A, i, j, n, m) {
        for (var k = 0; k < n; k++) {
            if (k !== i && !!A[k][j]) {
                for (var q = j + 1; q < m; q++) {
                    A[k][q] -= A[k][j] * A[i][q];
                }
                A[k][j] = 0;
            }
        }
    }
}

PolyRegression.Pair = function PolyRegression_Pair(x, y) {
    this._x = x;
    this._y = y;
}
PolyRegression.Pair.prototype = {
    _x: 0,
    
    get_x: function PolyRegression_Pair$get_x() {
        return this._x;
    },
    set_x: function PolyRegression_Pair$set_x(value) {
        this._x = value;
        return value;
    },
    
    _y: 0,
    
    get_y: function PolyRegression_Pair$get_y() {
        return this._y;
    },
    set_y: function PolyRegression_Pair$set_y(value) {
        this._y = value;
        return value;
    }
}


PolyRegression.Matrix.registerClass('PolyRegression.Matrix');
PolyRegression.Pair.registerClass('PolyRegression.Pair');
})();
