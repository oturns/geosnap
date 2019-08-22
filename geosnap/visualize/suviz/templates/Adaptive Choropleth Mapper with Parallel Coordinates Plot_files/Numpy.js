// numpy javascript equivalent
// https://github.com/fernandezajp/PyExtJS

(function() {

window.numpy = function numpy() {
}
numpy.linspace = function numpy$linspace(start, stop, num) {
    if (num == null) {
        num = 50;
    }
    var tmp = [];
    var step = (stop - start) / (num - 1);
    var i = start;
    for (var c = 0; c < num - 1; c++) {
        tmp.add(i);
        i = i + step;
    }
    tmp.add(stop);
    var array = new Array(tmp.length);
    for (var c = 0; c < tmp.length; c++) {
        array[c] = tmp[c];
    }
    return array;
}
numpy.logspace = function numpy$logspace(start, stop, num, endpoint, numericBase) {
    if (endpoint == null) {
        endpoint = true;
    }
    if (numericBase == null) {
        numericBase = 10;
    }
    var y = numpy.linspace(start, stop, num);
    return numpy.power(numericBase, y);
}
numpy.power = function numpy$power(bases, exponents) {
    var basesType = Type.getInstanceType(bases).get_name();
    var exponentsType = Type.getInstanceType(exponents).get_name();
    if (basesType === 'Array' && exponentsType === 'Array') {
        var basesArray = bases;
        var ret = new Array(basesArray.length);
        var baseArray = exponents;
        for (var i = 0; i < basesArray.length; i++) {
            ret[i] = Math.pow(basesArray[i], baseArray[i]);
        }
        return ret;
    }
    if (basesType === 'Array' && exponentsType === 'Number') {
        var basesArray = bases;
        var ret = new Array(basesArray.length);
        var bbase = exponents;
        for (var i = 0; i < basesArray.length; i++) {
            ret[i] = Math.pow(basesArray[i], bbase);
        }
        return ret;
    }
    if (basesType === 'Number' && exponentsType === 'Number') {
        var bbase = bases;
        var exponent = exponents;
        return Math.pow(bbase, exponent);
    }
    if (basesType === 'Number' && exponentsType === 'Array') {
        var bbase = bases;
        var exponentsArray = exponents;
        var ret = new Array(exponentsArray.length);
        for (var i = 0; i < exponentsArray.length; i++) {
            ret[i] = Math.pow(bbase, exponentsArray[i]);
        }
        return ret;
    }
    return 0;
}
numpy.exp = function numpy$exp(x) {
    var type = Type.getInstanceType(x).get_name();
    switch (type) {
        case 'Array':
            var inputarray = x;
            var response = new Array(inputarray.length);
            for (var i = 0; i < inputarray.length; i++) {
                response[i] = Math.exp(inputarray[i]);
            }
            return response;
        default:
            var input = x;
            return Math.exp(input);
    }
}
numpy.arange = function numpy$arange(start, stop, step) {
    var tmp = [];
    if (stop == null && step == null) {
        for (var i = 0; i < start; i++) {
            tmp.add(i);
        }
        var opt1 = new Array(tmp.length);
        for (var i = 0; i < tmp.length; i++) {
            opt1[i] = tmp[i];
        }
        return opt1;
    }
    if (step == null) {
        for (var i = start; i < stop; i++) {
            tmp.add(i);
        }
        var opt2 = new Array(tmp.length);
        for (var i = 0; i < tmp.length; i++) {
            opt2[i] = tmp[i];
        }
        return opt2;
    }
    for (var i = start; i < stop; i = i + step) {
        tmp.add(i);
    }
    var opt3 = new Array(tmp.length);
    for (var i = 0; i < tmp.length; i++) {
        opt3[i] = tmp[i];
    }
    return opt3;
}
numpy.zeros = function numpy$zeros(shape) {
    var type = Type.getInstanceType(shape).get_name();
    switch (type) {
        case 'Array':
            var shapeArray = shape;
            var shapeObjectArray = shape;
            var mult = 1;
            for (var i = 0; i < shapeArray.length; i++) {
                mult *= shapeArray[i];
            }
            var retArray = new Array(mult);
            for (var i = 0; i < mult; i++) {
                retArray[i] = 0;
            }
            return numpy._grouparray(numpy._inversearray(shapeObjectArray), retArray);
        default:
            var input = shape;
            var ret = new Array(input);
            for (var i = 0; i < input; i++) {
                ret[i] = 0;
            }
            return ret;
    }
}
numpy.ones = function numpy$ones(shape) {
    var type = Type.getInstanceType(shape).get_name();
    switch (type) {
        case 'Array':
            var shapeArray = shape;
            var shapeObjectArray = shape;
            var mult = 1;
            for (var i = 0; i < shapeArray.length; i++) {
                mult *= shapeArray[i];
            }
            var retArray = new Array(mult);
            for (var i = 0; i < mult; i++) {
                retArray[i] = 1;
            }
            return numpy._grouparray(numpy._inversearray(shapeObjectArray), retArray);
        default:
            var input = shape;
            var ret = new Array(input);
            for (var i = 0; i < input; i++) {
                ret[i] = 1;
            }
            return ret;
    }
}
numpy.polyfit = function numpy$polyfit(x, y, deg) {
    var data = new Array(x.length);
    for (var i = 0; i < x.length; i++) {
        data[i] = new PolyRegression.Pair(x[i], y[i]);
    }
    var polysolve = new PolyRegression.Matrix();
    var coefs = polysolve.computeCoefficients(data, deg);
    var left = 0;
    var right = coefs.length - 1;
    while (left < right) {
        var temp = coefs[left];
        coefs[left] = coefs[right];
        coefs[right] = temp;
        left++;
        right--;
    }
    return coefs;
}
numpy.array = function numpy$array(a) {
    return a;
}
numpy.getShape = function numpy$getShape(a) {
    /// <param name="a" type="Array" elementType="Object">
    /// </param>
    /// <returns type="Array" elementType="Number" elementInteger="true"></returns>
    var obj = a.shape;
    return Array.toArray(obj);
}
numpy.reshape = function numpy$reshape(a, shape) {
    var assign = true;
    if (this.constructor.name !== 'Function') {
        if (Type.getInstanceType(a).get_name() === 'Array') {
            shape = Array.toArray(a);
        }
        else {
            if (arguments.length > 0) {
                shape = Array.toArray(arguments);
            }
        }
        a = this;
        assign = false;
    }
    var array = Array.toArray(a);
    var objlist = [];
    numpy._plainarray(objlist, array);
    var plain = new Array(objlist.length);
    for (var i = 0; i < objlist.length; i++) {
        plain[i] = objlist[i];
    }
    var fixedshape = numpy._inversearray(Array.toArray(shape));
    var response = numpy._grouparray(Array.toArray(fixedshape), plain);
    if (assign) {
        a.clear();
        for (var i = 0; i < response.length; i++) {
            a.push(response[i]);
        }
    }
    return response;
}
numpy._isAligned = function numpy$_isAligned(a, b) {
    /// <param name="a" type="Array" elementType="Object">
    /// </param>
    /// <param name="b" type="Array" elementType="Object">
    /// </param>
    /// <returns type="Boolean"></returns>
    var A_shape = numpy.getShape(a);
    var B_shape = numpy.getShape(b);
    if (A_shape.length !== B_shape.length) {
        return false;
    }
    for (var i = A_shape.length - 1; i > 0; i = i - 2) {
        if (!i) {
            if (A_shape[i] !== B_shape[i]) {
                return false;
            }
        }
        if (A_shape[i] !== B_shape[i - 1]) {
            return false;
        }
    }
    return true;
}
numpy.ravel = function numpy$ravel(a) {
    var array = null;
    if (a == null) {
        array = this;
    }
    else {
        array = a;
    }
    var objlist = [];
    numpy._plainarray(objlist, array);
    var plain = new Array(objlist.length);
    for (var i = 0; i < objlist.length; i++) {
        plain[i] = objlist[i];
    }
    return plain;
}
numpy.gettype = function numpy$gettype(obj) {
    var paramType = Type.getInstanceType(obj).get_name();
    switch (paramType) {
        case 'Number':
            return paramType;
        case 'Array':
            var array = obj;
            var objlist = [];
            numpy._plainarray(objlist, array);
            return Type.getInstanceType(objlist[0]).get_name();
        default:
            return 'undefined';
    }
}
numpy._inversearray = function numpy$_inversearray(array) {
    var newarray = new Array(array.length);
    var j = array.length - 1;
    for (var i = 0; i < array.length; i++) {
        newarray[i] = array[j--];
    }
    return newarray;
}
numpy._plainarray = function numpy$_plainarray(list, a) {
    var $enum1 = ss.IEnumerator.getEnumerator(a);
    while ($enum1.moveNext()) {
        var item = $enum1.current;
        if (Type.getInstanceType(item).get_name() === 'Array') {
            numpy._plainarray(list, item);
        }
        else {
            list.add(item);
        }
    }
}
numpy._grouparray = function numpy$_grouparray(group, array) {
    if (group.length > 1) {
        var objlist = [];
        var size = group[0];
        for (var i = 0; i < array.length; ) {
            var tmp = new Array(size);
            for (var j = 0; j < size; j++) {
                tmp[j] = array[i++];
            }
            objlist.add(tmp);
        }
        var newgroupcount = new Array(group.length - 1);
        for (var i = 1; i < group.length; i++) {
            newgroupcount[i - 1] = group[i];
        }
        var newgroup = new Array(objlist.length);
        for (var i = 0; i < newgroup.length; i++) {
            newgroup[i] = objlist[i];
        }
        return numpy._grouparray(newgroupcount, newgroup);
    }
    else {
        var size = group[0];
        var newgroup = new Array(size);
        for (var i = 0; i < size; i++) {
            newgroup[i] = array[i];
        }
        return newgroup;
    }
}
numpy.getrandom = function numpy$getrandom(size) {
    if (size == null) {
        return Math.random();
    }
    var paramType = Type.getInstanceType(size).get_name();
    switch (paramType) {
        case 'Number':
            var singlesize = size;
            var retsinglearray = new Array(singlesize);
            for (var i = 0; i < singlesize; i++) {
                retsinglearray[i] = Math.random();
            }
            return retsinglearray;
            break;
        case 'Array':
            var sizeArray = size;
            var mult = 1;
            for (var i = 0; i < sizeArray.length; i++) {
                mult *= sizeArray[i];
            }
            var ret = new Array(mult);
            for (var i = 0; i < mult; i++) {
                ret[i] = Math.random();
            }
            return numpy._grouparray(sizeArray, ret);
            break;
    }
    return 0;
}
numpy.dot = function numpy$dot(a, b) {
    if (b == null) {
        b = a;
        a = this;
    }
    if (Type.getInstanceType(a).get_name() === 'Number' && Type.getInstanceType(b).get_name() === 'Array') {
        var b_ndim = numpy.getShape(b).length;
        if (b_ndim === 2) {
            var b_rows = numpy.getShape(b)[0];
            var b_cols = numpy.getShape(b)[1];
            var result = numpy.ones([ b_rows, b_cols ]);
            for (var br = 0; br < b_rows; br++) {
                for (var bc = 0; bc < b_cols; bc++) {
                    result[br][bc] = ((Array.toArray((b)[br]))[bc]) * a;
                }
            }
            return result;
        }
    }
    if (Type.getInstanceType(a).get_name() === 'Array' && Type.getInstanceType(b).get_name() === 'Number') {
        var a_ndim = numpy.getShape(a).length;
        if (a_ndim === 2) {
            var a_rows = numpy.getShape(a)[0];
            var a_cols = numpy.getShape(a)[1];
            var result = numpy.ones([ a_rows, a_cols ]);
            for (var ar = 0; ar < a_rows; ar++) {
                for (var ac = 0; ac < a_cols; ac++) {
                    result[ar][ac] = ((Array.toArray((a)[ar]))[ac]) * b;
                }
            }
            return result;
        }
    }
    if (Type.getInstanceType(a).get_name() === 'Array' && Type.getInstanceType(b).get_name() === 'Array') {
        var a_ndim = numpy.getShape(a).length;
        var b_ndim = numpy.getShape(b).length;
        if ((a_ndim === 2) && (b_ndim === 2)) {
            return numpy._dotMatrix(a, b);
        }
        else {
            return null;
        }
    }
    return null;
}
numpy.add = function numpy$add(a, b) {
    if (b == null) {
        b = a;
        a = this;
    }
    if (Type.getInstanceType(a).get_name() === 'Array' && Type.getInstanceType(b).get_name() === 'Array') {
        var a_ndim = numpy.getShape(a).length;
        var b_ndim = numpy.getShape(b).length;
        if ((a_ndim === 2) && (b_ndim === 2)) {
            return numpy._addMatrix(a, b);
        }
    }
    return null;
}
numpy._tupleCombination = function numpy$_tupleCombination(array) {
    var cardinality = 1;
    for (var i = 0; i < array.length; i++) {
        cardinality *= array[i];
    }
    var result = new Array(cardinality);
    for (var i = 0; i < result.length; i++) {
        result[i] = new Array(array.length);
    }
    for (var j = array.length - 1; j >= 0; j--) {
        var each = 1;
        for (var e = j + 1; e < array.length; e++) {
            each *= array[e];
        }
        var step = 0;
        var val = 0;
        for (var i = 0; i < cardinality; i++) {
            step++;
            var arrayValue = (Type.safeCast(result[i], Object));
            arrayValue[j] = val;
            if (step === each) {
                val = (val + 1) % array[j];
                step = 0;
            }
        }
    }
    return result;
}
numpy._getMatrixFromArray = function numpy$_getMatrixFromArray(matrix, positions, shape, numElements) {
    var m_shape = numpy.getShape(matrix);
    var Nx = m_shape[0];
    var Ny = m_shape[1];
    var plainarray = matrix.ravel();
    var response = numpy.zeros(numElements);
    var value = 0;
    for (var i = 0; i < positions.length; i++) {
        var tmp = 1;
        for (var j = i + 1; j < shape.length; j++) {
            tmp *= shape[j];
        }
        tmp *= numElements * positions[i];
        value += tmp;
    }
    var pos = 0;
    for (var i = value; i < numElements + value; i++) {
        response[pos++] = plainarray[i];
    }
    return response;
}
numpy._dotMatrix = function numpy$_dotMatrix(a, b) {
    if (numpy._isAligned(a, b)) {
        var nDimA = a.ndim;
        var nDimB = b.ndim;
        var a_rows = numpy.getShape(a)[0];
        var a_cols = numpy.getShape(a)[1];
        var b_rows = numpy.getShape(b)[0];
        var b_cols = numpy.getShape(b)[1];
        var c = numpy.zeros([ a_rows, b_cols + 1 ]);
        var matrixC = numpy.reshape(c, [ a_rows, b_cols ]);
        for (var ar = 0; ar < a_rows; ar++) {
            for (var bc = 0; bc < b_cols; bc++) {
                var value = 0;
                for (var ac = 0; ac < a_cols; ac++) {
                    var A_ar_ac = (Array.toArray(a[ar]))[ac];
                    var B_ac_ar = (Array.toArray(b[ac]))[bc];
                    value += A_ar_ac * B_ac_ar;
                }
                matrixC[ar][bc] = value;
            }
        }
        return matrixC;
    }
    return null;
}
numpy._addMatrix = function numpy$_addMatrix(a, b) {
    if (numpy._isAligned(a, b)) {
        var nDimA = a.ndim;
        var nDimB = b.ndim;
        var a_rows = numpy.getShape(a)[0];
        var a_cols = numpy.getShape(a)[1];
        var b_rows = numpy.getShape(b)[0];
        var b_cols = numpy.getShape(b)[1];
        var zeros = numpy.zeros([ a_rows, b_cols + 1 ]);
        var matrixC = numpy.reshape(zeros, [ a_rows, b_cols ]);
        for (var r = 0; r < a_rows; r++) {
            for (var c = 0; c < b_cols; c++) {
                var A_ar_ac = (Array.toArray(a[r]))[c];
                var B_br_bc = (Array.toArray(b[r]))[c];
                matrixC[r][c] = A_ar_ac + B_br_bc;
            }
        }
        return matrixC;
    }
    return null;
}
numpy.concatenate = function numpy$concatenate(pparams) {
    if (arguments.length > 1) {
        var join = [];
        for (var i = 0; i < arguments.length; i++) {
            var obj = arguments[i];
            switch (Type.getInstanceType(obj).get_name()) {
                case 'Array':
                    var objArray = obj;
                    for (var j = 0; j < objArray.length; j++) {
                        join.add(objArray[j]);
                    }
                    break;
                default:
                    join.add(obj);
                    break;
            }
        }
        return join;
    }
    return pparams;
}
numpy.sin = function numpy$sin(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.sin(data[i]);
            }
            return numpy.reshape(data, shape);
        default:
            return Math.sin(value);
    }
}
numpy.cos = function numpy$cos(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.cos(data[i]);
            }
            return numpy.reshape(data, shape);
        default:
            return Math.cos(value);
    }
}
numpy.tan = function numpy$tan(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.tan(data[i]);
            }
            return numpy.reshape(data, shape);
        default:
            return Math.tan(value);
    }
}
numpy.arcsin = function numpy$arcsin(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.asin(data[i]);
            }
            return numpy.reshape(data, shape);
        default:
            return Math.asin(value);
    }
}
numpy.arccos = function numpy$arccos(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.acos(data[i]);
            }
            return numpy.reshape(data, shape);
        default:
            return Math.acos(value);
    }
}
numpy.arctan = function numpy$arctan(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.atan(data[i]);
            }
            return numpy.reshape(data, shape);
        default:
            return Math.atan(value);
    }
}
numpy.hypot = function numpy$hypot(x, y) {
    var xtype = Type.getInstanceType(x).get_name();
    var ytype = Type.getInstanceType(y).get_name();
    if ((xtype === 'Number') && (ytype === 'Number')) {
        return Math.sqrt((x) * (x) + (y) * (y));
    }
    if ((xtype === 'Number') && (ytype === 'Array')) {
        var yshape = numpy.getShape(y);
        var data = y.ravel();
        for (var i = 0; i < data.length; i++) {
            data[i] = Math.sqrt((x) * (x) + (data[i]) * (data[i]));
        }
        return numpy.reshape(data, yshape);
    }
    if ((xtype === 'Array') && (ytype === 'Number')) {
        var xshape = numpy.getShape(x);
        var data = x.ravel();
        for (var i = 0; i < data.length; i++) {
            data[i] = Math.sqrt((data[i]) * (data[i]) + (y) * (y));
        }
        return numpy.reshape(data, xshape);
    }
    if ((xtype === 'Array') && (ytype === 'Array')) {
        var xshape = numpy.getShape(x);
        var xdata = x.ravel();
        var yshape = numpy.getShape(y);
        var ydata = y.ravel();
        var data = numpy.arange(xdata.length);
        for (var i = 0; i < xdata.length; i++) {
            data[i] = Math.sqrt((xdata[i]) * (xdata[i]) + (ydata[i]) * (ydata[i]));
        }
        return numpy.reshape(Array.toArray(data), xshape);
    }
    return null;
}
numpy.arctan2 = function numpy$arctan2(x, y) {
    var xtype = Type.getInstanceType(x).get_name();
    var ytype = Type.getInstanceType(y).get_name();
    if ((xtype === 'Number') && (ytype === 'Number')) {
        return Math.atan2(x, y);
    }
    if ((xtype === 'Number') && (ytype === 'Array')) {
        var yshape = numpy.getShape(y);
        var data = y.ravel();
        for (var i = 0; i < data.length; i++) {
            data[i] = Math.atan2(x, data[i]);
        }
        return numpy.reshape(data, yshape);
    }
    if ((xtype === 'Array') && (ytype === 'Number')) {
        var xshape = numpy.getShape(x);
        var data = x.ravel();
        for (var i = 0; i < data.length; i++) {
            data[i] = Math.atan2(data[i], y);
        }
        return numpy.reshape(data, xshape);
    }
    if ((xtype === 'Array') && (ytype === 'Array')) {
        var xshape = numpy.getShape(x);
        var xdata = x.ravel();
        var yshape = numpy.getShape(y);
        var ydata = y.ravel();
        var data = numpy.arange(xdata.length);
        for (var i = 0; i < xdata.length; i++) {
            data[i] = Math.atan2(xdata[i], ydata[i]);
        }
        return numpy.reshape(Array.toArray(data), xshape);
    }
    return null;
}
numpy.degrees = function numpy$degrees(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = (data[i]) * (180 / Math.PI);
            }
            return numpy.reshape(data, shape);
        default:
            return (value) * (180 / Math.PI);
    }
}
numpy.radians = function numpy$radians(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.PI * (data[i]) / 180;
            }
            return numpy.reshape(data, shape);
        default:
            return (value) * (180 / Math.PI);
    }
}
numpy.rad2deg = function numpy$rad2deg(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = (data[i]) * (180 / Math.PI);
            }
            return numpy.reshape(data, shape);
        default:
            return (value) * (180 / Math.PI);
    }
}
numpy.deg2rad = function numpy$deg2rad(value) {
    var type = Type.getInstanceType(value).get_name();
    switch (type) {
        case 'Array':
            var shape = numpy.getShape(value);
            var data = value.ravel();
            for (var i = 0; i < data.length; i++) {
                data[i] = Math.PI * (data[i]) / 180;
            }
            return numpy.reshape(data, shape);
        default:
            return (value) * (180 / Math.PI);
    }
}

numpy.registerClass('numpy');
Object.defineProperty(Array.prototype, "size", {
  get: function () {
    __$$tmP = this.shape;

    var thesize=1;
    for(var i=0;i<__$$tmP.length;i++)
        thesize*=__$$tmP[i];
    return thesize;
  }
});
Object.defineProperty(Array.prototype, "shape", {
  get: function () {
    __$$tmP = this;
    var dim = [];
    for (;;) {
        dim.push(__$$tmP.length);

        if (Array.isArray(__$$tmP[0])) {
            __$$tmP = __$$tmP[0];
        } else {
            break;
        }
    }
    return dim;
  }
});
Object.defineProperty(Array.prototype, "strides", {
  get: function () {
    var shp = this.shape;
    var dim = [];
    for (var i=1;i<shp.length;i++) {
        var acum = 1;
        for(var j=i;j<shp.length;j++) {
            acum*=shp[j];
        }
        dim.push(acum);
    }
    dim.push(1);
    return dim;
  }
});
Object.defineProperty(Array.prototype, "ndim", {
  get: function () {
    __$$tmP = this;
    return __$$tmP.shape.length;
  }
});
Object.defineProperty(Array.prototype, "dtype", {
  get: function () {
    return numpy.gettype(this);
  }
});
Object.defineProperty(Array.prototype, "T", {
  get: function () {
    return this.transpose();
  }
});
Array.prototype.resize = function numpy$_resize(shape) {
    a = this;
    a = numpy.reshape(a,shape);
    this.clear();
    for(var i=0;i<a.length;i++)
        this.push(a[i]);
    return a;
};
Array.prototype.transpose = function numpy$_transpose() {
  var _data = this.ravel();
  var _dest = _data.clone();

  var recipient = new Array(this.size);
  var sh = this.shape.reverse();
  var dstStride = this.strides.reverse();

  generatelist(recipient,sh);
  transport(_data,_dest,recipient,dstStride);

  _dest=_dest.reshape(sh);
  return _dest;
};
Array.prototype.flatten = function numpy$_flatten() {
  return this.ravel();
};
function generatelist(recipient,sh)
{
    var start = new Array(sh.length);
    var size = sh.length;

    for(var i=0;i<sh.length;i++){
        start[i]=0;
    }

    for(var i=0;i<recipient.length;i++){
        recipient[i] = new Array(sh.length);
        for(var j=0;j<sh.length;j++)
            recipient[i][j] = start[j];

        increment(start,sh);
    }
};
function increment(start,sh){
    for(var i=sh.length-1;i>=0;i--){
        if (start[i]<sh[i]-1){
            start[i]++;
            return;
        }
        start[i]=0;
    }
};
function transport(data,dest,recipient,dstStride)
{
    for(var i=0;i<recipient.length;i++){
        var position;
        var positionArray = recipient[i];
        for(var j=0;j<dstStride.length;j++)
            positionArray[j] = recipient[i][j]*dstStride[j];
        var position = positionArray.reduce(function(a, b) { return a + b; }, 0);
        dest[i]=data[position];
    }
};
np = numpy;
numpy.pi = Math.PI;
numpy.range = numpy.arange;
Array.prototype.exp = numpy.exp;
Array.prototype.reshape = numpy.reshape;
Array.prototype.ravel = numpy.ravel;
Array.prototype.dtype = numpy.dtype;
Number.prototype.dtype = numpy.dtype;
Array.prototype.dot = numpy.dot;
numpy.random = numpy.getrandom;
numpy.random.random = numpy.getrandom;
ndarray = Array;
})();
