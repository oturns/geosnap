'use strict';

Object.defineProperty(exports, '__esModule', { value: true });

/* @flow */

/**
 * [Simple linear regression](http://en.wikipedia.org/wiki/Simple_linear_regression)
 * is a simple way to find a fitted line
 * between a set of coordinates. This algorithm finds the slope and y-intercept of a regression line
 * using the least sum of squares.
 *
 * @param {Array<Array<number>>} data an array of two-element of arrays,
 * like `[[0, 1], [2, 3]]`
 * @returns {Object} object containing slope and intersect of regression line
 * @example
 * linearRegression([[0, 0], [1, 1]]); // => { m: 1, b: 0 }
 */
function linearRegression(data/*: Array<Array<number>> */)/*: { m: number, b: number } */ {

    var m, b;

    // Store data length in a local variable to reduce
    // repeated object property lookups
    var dataLength = data.length;

    //if there's only one point, arbitrarily choose a slope of 0
    //and a y-intercept of whatever the y of the initial point is
    if (dataLength === 1) {
        m = 0;
        b = data[0][1];
    } else {
        // Initialize our sums and scope the `m` and `b`
        // variables that define the line.
        var sumX = 0, sumY = 0,
            sumXX = 0, sumXY = 0;

        // Use local variables to grab point values
        // with minimal object property lookups
        var point, x, y;

        // Gather the sum of all x values, the sum of all
        // y values, and the sum of x^2 and (x*y) for each
        // value.
        //
        // In math notation, these would be SS_x, SS_y, SS_xx, and SS_xy
        for (var i = 0; i < dataLength; i++) {
            point = data[i];
            x = point[0];
            y = point[1];

            sumX += x;
            sumY += y;

            sumXX += x * x;
            sumXY += x * y;
        }

        // `m` is the slope of the regression line
        m = ((dataLength * sumXY) - (sumX * sumY)) /
            ((dataLength * sumXX) - (sumX * sumX));

        // `b` is the y-intercept of the line.
        b = (sumY / dataLength) - ((m * sumX) / dataLength);
    }

    // Return both values as an object.
    return {
        m: m,
        b: b
    };
}

/* @flow */

/**
 * Given the output of `linearRegression`: an object
 * with `m` and `b` values indicating slope and intercept,
 * respectively, generate a line function that translates
 * x values into y values.
 *
 * @param {Object} mb object with `m` and `b` members, representing
 * slope and intersect of desired line
 * @returns {Function} method that computes y-value at any given
 * x-value on the line.
 * @example
 * var l = linearRegressionLine(linearRegression([[0, 0], [1, 1]]));
 * l(0) // = 0
 * l(2) // = 2
 * linearRegressionLine({ b: 0, m: 1 })(1); // => 1
 * linearRegressionLine({ b: 1, m: 1 })(1); // => 2
 */
function linearRegressionLine(mb/*: { b: number, m: number }*/)/*: Function */ {
    // Return a function that computes a `y` value for each
    // x value it is given, based on the values of `b` and `a`
    // that we just computed.
    return function(x) {
        return mb.b + (mb.m * x);
    };
}

/* @flow */

/**
 * Our default sum is the [Kahan-Babuska algorithm](https://pdfs.semanticscholar.org/1760/7d467cda1d0277ad272deb2113533131dc09.pdf).
 * This method is an improvement over the classical
 * [Kahan summation algorithm](https://en.wikipedia.org/wiki/Kahan_summation_algorithm).
 * It aims at computing the sum of a list of numbers while correcting for
 * floating-point errors. Traditionally, sums are calculated as many
 * successive additions, each one with its own floating-point roundoff. These
 * losses in precision add up as the number of numbers increases. This alternative
 * algorithm is more accurate than the simple way of calculating sums by simple
 * addition.
 *
 * This runs on `O(n)`, linear time in respect to the array.
 *
 * @param {Array<number>} x input
 * @return {number} sum of all input numbers
 * @example
 * sum([1, 2, 3]); // => 6
 */
function sum(x/*: Array<number> */)/*: number */ {

    // If the array is empty, we needn't bother computing its sum
    if (x.length === 0) {
        return 0;
    }

    // Initializing the sum as the first number in the array
    var sum = x[0];

    // Keeping track of the floating-point error correction
    var correction = 0;

    var transition;

    for (var i = 1; i < x.length; i++) {
        transition = sum + x[i];

        // Here we need to update the correction in a different fashion
        // if the new absolute value is greater than the absolute sum
        if (Math.abs(sum) >= Math.abs(x[i])) {
            correction += ((sum - transition) + x[i]);
        }
        else {
            correction += ((x[i] - transition) + sum);
        }

        sum = transition;
    }

    // Returning the corrected sum
    return sum + correction;
}

/* @flow */

/**
 * The mean, _also known as average_,
 * is the sum of all values over the number of values.
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x sample of one or more data points
 * @throws {Error} if the the length of x is less than one
 * @returns {number} mean
 * @example
 * mean([0, 10]); // => 5
 */
function mean(x /*: Array<number> */)/*: number */ {
    // The mean of no numbers is null
    if (x.length === 0) {
        throw new Error('mean requires at least one data point');
    }

    return sum(x) / x.length;
}

/* @flow */

/**
 * The sum of deviations to the Nth power.
 * When n=2 it's the sum of squared deviations.
 * When n=3 it's the sum of cubed deviations.
 *
 * @param {Array<number>} x
 * @param {number} n power
 * @returns {number} sum of nth power deviations
 *
 * @example
 * var input = [1, 2, 3];
 * // since the variance of a set is the mean squared
 * // deviations, we can calculate that with sumNthPowerDeviations:
 * sumNthPowerDeviations(input, 2) / input.length;
 */
function sumNthPowerDeviations(x/*: Array<number> */, n/*: number */)/*: number */ {
    var meanValue = mean(x),
        sum = 0,
        tempValue,
        i;

    // This is an optimization: when n is 2 (we're computing a number squared),
    // multiplying the number by itself is significantly faster than using
    // the Math.pow method.
    if (n === 2) {
        for (i = 0; i < x.length; i++) {
            tempValue = x[i] - meanValue;
            sum += tempValue * tempValue;
        }
    } else {
        for (i = 0; i < x.length; i++) {
            sum += Math.pow(x[i] - meanValue, n);
        }
    }

    return sum;
}

/* @flow */

/**
 * The [variance](http://en.wikipedia.org/wiki/Variance)
 * is the sum of squared deviations from the mean.
 *
 * This is an implementation of variance, not sample variance:
 * see the `sampleVariance` method if you want a sample measure.
 *
 * @param {Array<number>} x a population of one or more data points
 * @returns {number} variance: a value greater than or equal to zero.
 * zero indicates that all values are identical.
 * @throws {Error} if x's length is 0
 * @example
 * variance([1, 2, 3, 4, 5, 6]); // => 2.9166666666666665
 */
function variance(x/*: Array<number> */)/*:number*/ {
    // The variance of no numbers is null
    if (x.length === 0) {
        throw new Error('variance requires at least one data point');
    }

    // Find the mean of squared deviations between the
    // mean value and each value.
    return sumNthPowerDeviations(x, 2) / x.length;
}

/* @flow */

/**
 * The [standard deviation](http://en.wikipedia.org/wiki/Standard_deviation)
 * is the square root of the variance. This is also known as the population
 * standard deviation. It's useful for measuring the amount
 * of variation or dispersion in a set of values.
 *
 * Standard deviation is only appropriate for full-population knowledge: for
 * samples of a population, {@link sampleStandardDeviation} is
 * more appropriate.
 *
 * @param {Array<number>} x input
 * @returns {number} standard deviation
 * @example
 * variance([2, 4, 4, 4, 5, 5, 7, 9]); // => 4
 * standardDeviation([2, 4, 4, 4, 5, 5, 7, 9]); // => 2
 */
function standardDeviation(x /*: Array<number> */)/*:number*/ {
    if (x.length === 1) {
        return 0;
    }
    var v = variance(x);
    return Math.sqrt(v);
}

/* @flow */

/**
 * The [R Squared](http://en.wikipedia.org/wiki/Coefficient_of_determination)
 * value of data compared with a function `f`
 * is the sum of the squared differences between the prediction
 * and the actual value.
 *
 * @param {Array<Array<number>>} x input data: this should be doubly-nested
 * @param {Function} func function called on `[i][0]` values within the dataset
 * @returns {number} r-squared value
 * @example
 * var samples = [[0, 0], [1, 1]];
 * var regressionLine = linearRegressionLine(linearRegression(samples));
 * rSquared(samples, regressionLine); // = 1 this line is a perfect fit
 */
function rSquared(x /*: Array<Array<number>> */, func /*: Function */) /*: number */ {
    if (x.length < 2) { return 1; }

    // Compute the average y value for the actual
    // data set in order to compute the
    // _total sum of squares_
    var sum = 0, average;
    for (var i = 0; i < x.length; i++) {
        sum += x[i][1];
    }
    average = sum / x.length;

    // Compute the total sum of squares - the
    // squared difference between each point
    // and the average of all points.
    var sumOfSquares = 0;
    for (var j = 0; j < x.length; j++) {
        sumOfSquares += Math.pow(average - x[j][1], 2);
    }

    // Finally estimate the error: the squared
    // difference between the estimate and the actual data
    // value at each point.
    var err = 0;
    for (var k = 0; k < x.length; k++) {
        err += Math.pow(x[k][1] - func(x[k][0]), 2);
    }

    // As the error grows larger, its ratio to the
    // sum of squares increases and the r squared
    // value grows lower.
    return 1 - err / sumOfSquares;
}

/* @flow */

/**
 * The [mode](http://bit.ly/W5K4Yt) is the number that appears in a list the highest number of times.
 * There can be multiple modes in a list: in the event of a tie, this
 * algorithm will return the most recently seen mode.
 *
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * This runs in `O(n)` because the input is sorted.
 *
 * @param {Array<number>} sorted a sample of one or more data points
 * @returns {number} mode
 * @throws {Error} if sorted is empty
 * @example
 * modeSorted([0, 0, 1]); // => 0
 */
function modeSorted(sorted /*: Array<number> */)/*:number*/ {

    // Handle edge cases:
    // The mode of an empty list is undefined
    if (sorted.length === 0) {
        throw new Error('mode requires at least one data point');
    } else if (sorted.length === 1) {
        return sorted[0];
    }

    // This assumes it is dealing with an array of size > 1, since size
    // 0 and 1 are handled immediately. Hence it starts at index 1 in the
    // array.
    var last = sorted[0],
        // store the mode as we find new modes
        value = NaN,
        // store how many times we've seen the mode
        maxSeen = 0,
        // how many times the current candidate for the mode
        // has been seen
        seenThis = 1;

    // end at sorted.length + 1 to fix the case in which the mode is
    // the highest number that occurs in the sequence. the last iteration
    // compares sorted[i], which is undefined, to the highest number
    // in the series
    for (var i = 1; i < sorted.length + 1; i++) {
        // we're seeing a new number pass by
        if (sorted[i] !== last) {
            // the last number is the new mode since we saw it more
            // often than the old one
            if (seenThis > maxSeen) {
                maxSeen = seenThis;
                value = last;
            }
            seenThis = 1;
            last = sorted[i];
        // if this isn't a new number, it's one more occurrence of
        // the potential mode
        } else { seenThis++; }
    }
    return value;
}

/* @flow */

/**
 * Sort an array of numbers by their numeric value, ensuring that the
 * array is not changed in place.
 *
 * This is necessary because the default behavior of .sort
 * in JavaScript is to sort arrays as string values
 *
 *     [1, 10, 12, 102, 20].sort()
 *     // output
 *     [1, 10, 102, 12, 20]
 *
 * @param {Array<number>} x input array
 * @return {Array<number>} sorted array
 * @private
 * @example
 * numericSort([3, 2, 1]) // => [1, 2, 3]
 */
function numericSort(x /*: Array<number> */) /*: Array<number> */ {
    return x
        // ensure the array is not changed in-place
        .slice()
        // comparator function that treats input as numeric
        .sort(function(a, b) {
            return a - b;
        });
}

/* @flow */

/**
 * The [mode](http://bit.ly/W5K4Yt) is the number that appears in a list the highest number of times.
 * There can be multiple modes in a list: in the event of a tie, this
 * algorithm will return the most recently seen mode.
 *
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * This runs on `O(nlog(n))` because it needs to sort the array internally
 * before running an `O(n)` search to find the mode.
 *
 * @param {Array<number>} x input
 * @returns {number} mode
 * @example
 * mode([0, 0, 1]); // => 0
 */
function mode(x /*: Array<number> */)/*:number*/ {
    // Sorting the array lets us iterate through it below and be sure
    // that every time we see a new number it's new and we'll never
    // see the same number twice
    return modeSorted(numericSort(x));
}

/* @flow */
/* globals Map: false */

/**
 * The [mode](http://bit.ly/W5K4Yt) is the number that appears in a list the highest number of times.
 * There can be multiple modes in a list: in the event of a tie, this
 * algorithm will return the most recently seen mode.
 *
 * modeFast uses a Map object to keep track of the mode, instead of the approach
 * used with `mode`, a sorted array. As a result, it is faster
 * than `mode` and supports any data type that can be compared with `==`.
 * It also requires a
 * [JavaScript environment with support for Map](https://kangax.github.io/compat-table/es6/#test-Map),
 * and will throw an error if Map is not available.
 *
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * @param {Array<*>} x a sample of one or more data points
 * @returns {?*} mode
 * @throws {ReferenceError} if the JavaScript environment doesn't support Map
 * @throws {Error} if x is empty
 * @example
 * modeFast(['rabbits', 'rabbits', 'squirrels']); // => 'rabbits'
 */
function modeFast/*::<T>*/(x /*: Array<T> */)/*: ?T */ {

    // This index will reflect the incidence of different values, indexing
    // them like
    // { value: count }
    var index = new Map();

    // A running `mode` and the number of times it has been encountered.
    var mode;
    var modeCount = 0;

    for (var i = 0; i < x.length; i++) {
        var newCount = index.get(x[i]);
        if (newCount === undefined) {
            newCount = 1;
        } else {
            newCount++;
        }
        if (newCount > modeCount) {
            mode = x[i];
            modeCount = newCount;
        }
        index.set(x[i], newCount);
    }

    if (modeCount === 0) {
        throw new Error('mode requires at last one data point');
    }

    return mode;
}

/* @flow */

/**
 * The min is the lowest number in the array. This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x sample of one or more data points
 * @throws {Error} if the the length of x is less than one
 * @returns {number} minimum value
 * @example
 * min([1, 5, -10, 100, 2]); // => -10
 */
function min(x /*: Array<number> */)/*:number*/ {

    if (x.length === 0) {
        throw new Error('min requires at least one data point');
    }

    var value = x[0];
    for (var i = 1; i < x.length; i++) {
        // On the first iteration of this loop, min is
        // undefined and is thus made the minimum element in the array
        if (x[i] < value) {
            value = x[i];
        }
    }
    return value;
}

/* @flow */

/**
 * This computes the maximum number in an array.
 *
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x sample of one or more data points
 * @returns {number} maximum value
 * @throws {Error} if the the length of x is less than one
 * @example
 * max([1, 2, 3, 4]);
 * // => 4
 */
function max(x /*: Array<number> */) /*:number*/ {

    if (x.length === 0) {
        throw new Error('max requires at least one data point');
    }

    var value = x[0];
    for (var i = 1; i < x.length; i++) {
        // On the first iteration of this loop, max is
        // undefined and is thus made the maximum element in the array
        if (x[i] > value) {
            value = x[i];
        }
    }
    return value;
}

/* @flow */

/**
 * This computes the minimum & maximum number in an array.
 *
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x sample of one or more data points
 * @returns {Array<number>} minimum & maximum value
 * @throws {Error} if the the length of x is less than one
 * @example
 * extent([1, 2, 3, 4]);
 * // => [1, 4]
 */
function extent(x /*: Array<number> */) /*:Array<number>*/ {

    if (x.length === 0) {
        throw new Error('extent requires at least one data point');
    }

    var min = x[0];
    var max = x[0];
    for (var i = 1; i < x.length; i++) {
        if (x[i] > max) {
            max = x[i];
        }
        if (x[i] < min) {
            min = x[i];
        }
    }
    return [min, max];
}

/* @flow */

/**
 * The minimum is the lowest number in the array. With a sorted array,
 * the first element in the array is always the smallest, so this calculation
 * can be done in one step, or constant time.
 *
 * @param {Array<number>} x input
 * @returns {number} minimum value
 * @example
 * minSorted([-100, -10, 1, 2, 5]); // => -100
 */
function minSorted(x /*: Array<number> */)/*: number */ {
    return x[0];
}

/* @flow */

/**
 * The maximum is the highest number in the array. With a sorted array,
 * the last element in the array is always the largest, so this calculation
 * can be done in one step, or constant time.
 *
 * @param {Array<number>} x input
 * @returns {number} maximum value
 * @example
 * maxSorted([-100, -10, 1, 2, 5]); // => 5
 */
function maxSorted(x /*: Array<number> */)/*:number*/ {
    return x[x.length - 1];
}

/* @flow */

/**
 * The extent is the lowest & highest number in the array. With a sorted array,
 * the first element in the array is always the lowest while the last element is always the largest, so this calculation
 * can be done in one step, or constant time.
 *
 * @param {Array<number>} x input
 * @returns {Array<number>} minimum & maximum value
 * @example
 * extentSorted([-100, -10, 1, 2, 5]); // => [-100, 5]
 */
function extentSorted(x /*: Array<number> */)/*:Array<number>*/ {
    return [x[0], x[x.length - 1]];
}

/* @flow */

/**
 * The simple [sum](https://en.wikipedia.org/wiki/Summation) of an array
 * is the result of adding all numbers together, starting from zero.
 *
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x input
 * @return {number} sum of all input numbers
 * @example
 * sumSimple([1, 2, 3]); // => 6
 */
function sumSimple(x/*: Array<number> */)/*: number */ {
    var value = 0;
    for (var i = 0; i < x.length; i++) {
        value += x[i];
    }
    return value;
}

/* @flow */

/**
 * The [product](https://en.wikipedia.org/wiki/Product_(mathematics)) of an array
 * is the result of multiplying all numbers together, starting using one as the multiplicative identity.
 *
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x input
 * @return {number} product of all input numbers
 * @example
 * product([1, 2, 3, 4]); // => 24
 */
function product(x/*: Array<number> */)/*: number */ {
    var value = 1;
    for (var i = 0; i < x.length; i++) {
        value *= x[i];
    }
    return value;
}

/* @flow */

/**
 * This is the internal implementation of quantiles: when you know
 * that the order is sorted, you don't need to re-sort it, and the computations
 * are faster.
 *
 * @param {Array<number>} x sample of one or more data points
 * @param {number} p desired quantile: a number between 0 to 1, inclusive
 * @returns {number} quantile value
 * @throws {Error} if p ix outside of the range from 0 to 1
 * @throws {Error} if x is empty
 * @example
 * quantileSorted([3, 6, 7, 8, 8, 9, 10, 13, 15, 16, 20], 0.5); // => 9
 */
function quantileSorted(x /*: Array<number> */, p /*: number */)/*: number */ {
    var idx = x.length * p;
    if (x.length === 0) {
        throw new Error('quantile requires at least one data point.');
    } else if (p < 0 || p > 1) {
        throw new Error('quantiles must be between 0 and 1');
    } else if (p === 1) {
        // If p is 1, directly return the last element
        return x[x.length - 1];
    } else if (p === 0) {
        // If p is 0, directly return the first element
        return x[0];
    } else if (idx % 1 !== 0) {
        // If p is not integer, return the next element in array
        return x[Math.ceil(idx) - 1];
    } else if (x.length % 2 === 0) {
        // If the list has even-length, we'll take the average of this number
        // and the next value, if there is one
        return (x[idx - 1] + x[idx]) / 2;
    } else {
        // Finally, in the simple case of an integer value
        // with an odd-length list, return the x value at the index.
        return x[idx];
    }
}

/* @flow */

/**
 * Rearrange items in `arr` so that all items in `[left, k]` range are the smallest.
 * The `k`-th element will have the `(k - left + 1)`-th smallest value in `[left, right]`.
 *
 * Implements Floyd-Rivest selection algorithm https://en.wikipedia.org/wiki/Floyd-Rivest_algorithm
 *
 * @param {Array<number>} arr input array
 * @param {number} k pivot index
 * @param {number} [left] left index
 * @param {number} [right] right index
 * @returns {void} mutates input array
 * @example
 * var arr = [65, 28, 59, 33, 21, 56, 22, 95, 50, 12, 90, 53, 28, 77, 39];
 * quickselect(arr, 8);
 * // = [39, 28, 28, 33, 21, 12, 22, 50, 53, 56, 59, 65, 90, 77, 95]
 */
function quickselect(arr/*: Array<number> */, k/*: number */, left/*: ?number */, right/*: ?number */)/*: void */ {
    left = left || 0;
    right = right || (arr.length - 1);

    while (right > left) {
        // 600 and 0.5 are arbitrary constants chosen in the original paper to minimize execution time
        if (right - left > 600) {
            var n = right - left + 1;
            var m = k - left + 1;
            var z = Math.log(n);
            var s = 0.5 * Math.exp(2 * z / 3);
            var sd = 0.5 * Math.sqrt(z * s * (n - s) / n);
            if (m - n / 2 < 0) sd *= -1;
            var newLeft = Math.max(left, Math.floor(k - m * s / n + sd));
            var newRight = Math.min(right, Math.floor(k + (n - m) * s / n + sd));
            quickselect(arr, k, newLeft, newRight);
        }

        var t = arr[k];
        var i = left;
        var j = right;

        swap(arr, left, k);
        if (arr[right] > t) swap(arr, left, right);

        while (i < j) {
            swap(arr, i, j);
            i++;
            j--;
            while (arr[i] < t) i++;
            while (arr[j] > t) j--;
        }

        if (arr[left] === t) swap(arr, left, j);
        else {
            j++;
            swap(arr, j, right);
        }

        if (j <= k) left = j + 1;
        if (k <= j) right = j - 1;
    }
}

function swap(arr, i, j) {
    var tmp = arr[i];
    arr[i] = arr[j];
    arr[j] = tmp;
}

/* @flow */

/**
 * The [quantile](https://en.wikipedia.org/wiki/Quantile):
 * this is a population quantile, since we assume to know the entire
 * dataset in this library. This is an implementation of the
 * [Quantiles of a Population](http://en.wikipedia.org/wiki/Quantile#Quantiles_of_a_population)
 * algorithm from wikipedia.
 *
 * Sample is a one-dimensional array of numbers,
 * and p is either a decimal number from 0 to 1 or an array of decimal
 * numbers from 0 to 1.
 * In terms of a k/q quantile, p = k/q - it's just dealing with fractions or dealing
 * with decimal values.
 * When p is an array, the result of the function is also an array containing the appropriate
 * quantiles in input order
 *
 * @param {Array<number>} x sample of one or more numbers
 * @param {Array<number> | number} p the desired quantile, as a number between 0 and 1
 * @returns {number} quantile
 * @example
 * quantile([3, 6, 7, 8, 8, 9, 10, 13, 15, 16, 20], 0.5); // => 9
 */
function quantile(x/*: Array<number> */, p/*: Array<number> | number */)/*: Array<number> | number */ {
    var copy = x.slice();

    if (Array.isArray(p)) {
        // rearrange elements so that each element corresponding to a requested
        // quantile is on a place it would be if the array was fully sorted
        multiQuantileSelect(copy, p);
        // Initialize the result array
        var results = [];
        // For each requested quantile
        for (var i = 0; i < p.length; i++) {
            results[i] = quantileSorted(copy, p[i]);
        }
        return results;
    } else {
        var idx = quantileIndex(copy.length, p);
        quantileSelect(copy, idx, 0, copy.length - 1);
        return quantileSorted(copy, p);
    }
}

function quantileSelect(arr, k, left, right) {
    if (k % 1 === 0) {
        quickselect(arr, k, left, right);
    } else {
        k = Math.floor(k);
        quickselect(arr, k, left, right);
        quickselect(arr, k + 1, k + 1, right);
    }
}

function multiQuantileSelect(arr, p) {
    var indices = [0];
    for (var i = 0; i < p.length; i++) {
        indices.push(quantileIndex(arr.length, p[i]));
    }
    indices.push(arr.length - 1);
    indices.sort(compare);

    var stack = [0, indices.length - 1];

    while (stack.length) {
        var r = Math.ceil(stack.pop());
        var l = Math.floor(stack.pop());
        if (r - l <= 1) continue;

        var m = Math.floor((l + r) / 2);
        quantileSelect(arr, indices[m], indices[l], indices[r]);

        stack.push(l, m, m, r);
    }
}

function compare(a, b) {
    return a - b;
}

function quantileIndex(len /*: number */, p /*: number */)/*:number*/ {
    var idx = len * p;
    if (p === 1) {
        // If p is 1, directly return the last index
        return len - 1;
    } else if (p === 0) {
        // If p is 0, directly return the first index
        return 0;
    } else if (idx % 1 !== 0) {
        // If index is not integer, return the next index in array
        return Math.ceil(idx) - 1;
    } else if (len % 2 === 0) {
        // If the list has even-length, we'll return the middle of two indices
        // around quantile to indicate that we need an average value of the two
        return idx - 0.5;
    } else {
        // Finally, in the simple case of an integer index
        // with an odd-length list, return the index
        return idx;
    }
}

/* @flow */
/* eslint no-bitwise: 0 */

/**
 * This function returns the quantile in which one would find the given value in
 * the given array. With a sorted array, leveraging binary search, we can find
 * this information in logarithmic time.
 *
 * @param {Array<number>} x input
 * @returns {number} value value
 * @example
 * quantileRankSorted([1, 2, 3, 4], 3); // => 0.75
 * quantileRankSorted([1, 2, 3, 3, 4], 3); // => 0.7
 * quantileRankSorted([1, 2, 3, 4], 6); // => 1
 * quantileRankSorted([1, 2, 3, 3, 5], 4); // => 0.8
 */
function quantileRankSorted(
    x /*: Array<number> */,
    value /*: number */)/*: number */ {

    // Value is lesser than any value in the array
    if (value < x[0]) {
        return 0;
    }

    // Value is greater than any value in the array
    if (value > x[x.length - 1]) {
        return 1;
    }

    var l = lowerBound(x, value);

    // Value is not in the array
    if (x[l] !== value) {
        return l / x.length;
    }

    l++;

    var u = upperBound(x, value);

    // The value exists only once in the array
    if (u === l) {
        return l / x.length;
    }

    // Here, we are basically computing the mean of the range of indices
    // containing our searched value. But, instead, of initializing an
    // array and looping over it, there is a dedicated math formula that
    // we apply below to get the result.
    var r = u - l + 1;
    var sum = (r * (u + l)) / 2;
    var mean = sum / r;

    return mean / x.length;
}

function lowerBound(x, value) {
    var mid = 0;
    var lo = 0;
    var hi = x.length;

    while (lo < hi) {
        mid = (lo + hi) >>> 1;

        if (value <= x[mid]) {
            hi = mid;
        }
        else {
            lo = -~mid;
        }
    }

    return lo;
}

function upperBound(x, value) {
    var mid = 0;
    var lo = 0;
    var hi = x.length;

    while (lo < hi) {
        mid = (lo + hi) >>> 1;

        if (value >= x[mid]) {
            lo = -~mid;
        }
        else {
            hi = mid;
        }
    }

    return lo;
}

/* @flow */

/**
 * This function returns the quantile in which one would find the given value in
 * the given array. It will require to copy and sort your array beforehand, so
 * if you know your array is already sorted, you would rather use
 * `quantileRankSorted`.
 *
 * @param {Array<number>} x input
 * @returns {number} value value
 * @example
 * quantileRank([4, 3, 1, 2], 3); // => 0.75
 * quantileRank([4, 3, 2, 3, 1], 3); // => 0.7
 * quantileRank([2, 4, 1, 3], 6); // => 1
 * quantileRank([5, 3, 1, 2, 3], 4); // => 0.8
 */
function quantileRank(
    x /*: Array<number> */,
    value /*: number */)/*: number */ {

    // Cloning and sorting the array
    var sortedCopy = numericSort(x);

    return quantileRankSorted(sortedCopy, value);
}

/* @flow */

/**
 * The [Interquartile range](http://en.wikipedia.org/wiki/Interquartile_range) is
 * a measure of statistical dispersion, or how scattered, spread, or
 * concentrated a distribution is. It's computed as the difference between
 * the third quartile and first quartile.
 *
 * @param {Array<number>} x sample of one or more numbers
 * @returns {number} interquartile range: the span between lower and upper quartile,
 * 0.25 and 0.75
 * @example
 * interquartileRange([0, 1, 2, 3]); // => 2
 */
function interquartileRange(x/*: Array<number> */) {
    // Interquartile range is the span between the upper quartile,
    // at `0.75`, and lower quartile, `0.25`
    var q1 = quantile(x, 0.75),
        q2 = quantile(x, 0.25);

    if (typeof q1 === 'number' && typeof q2 === 'number') {
        return q1 - q2;
    }
}

/* @flow */

/**
 * The [median](http://en.wikipedia.org/wiki/Median) is
 * the middle number of a list. This is often a good indicator of 'the middle'
 * when there are outliers that skew the `mean()` value.
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * The median isn't necessarily one of the elements in the list: the value
 * can be the average of two elements if the list has an even length
 * and the two central values are different.
 *
 * @param {Array<number>} x input
 * @returns {number} median value
 * @example
 * median([10, 2, 5, 100, 2, 1]); // => 3.5
 */
function median(x /*: Array<number> */)/*: number */ {
    return +quantile(x, 0.5);
}

/* @flow */

/**
 * The [Median Absolute Deviation](http://en.wikipedia.org/wiki/Median_absolute_deviation) is
 * a robust measure of statistical
 * dispersion. It is more resilient to outliers than the standard deviation.
 *
 * @param {Array<number>} x input array
 * @returns {number} median absolute deviation
 * @example
 * medianAbsoluteDeviation([1, 1, 2, 2, 4, 6, 9]); // => 1
 */
function medianAbsoluteDeviation(x/*: Array<number> */)/*: number */ {
    // The mad of nothing is null
    var medianValue = median(x),
        medianAbsoluteDeviations = [];

    // Make a list of absolute deviations from the median
    for (var i = 0; i < x.length; i++) {
        medianAbsoluteDeviations.push(Math.abs(x[i] - medianValue));
    }

    // Find the median value of that list
    return median(medianAbsoluteDeviations);
}

/* @flow */

/**
 * Split an array into chunks of a specified size. This function
 * has the same behavior as [PHP's array_chunk](http://php.net/manual/en/function.array-chunk.php)
 * function, and thus will insert smaller-sized chunks at the end if
 * the input size is not divisible by the chunk size.
 *
 * `x` is expected to be an array, and `chunkSize` a number.
 * The `x` array can contain any kind of data.
 *
 * @param {Array} x a sample
 * @param {number} chunkSize size of each output array. must be a positive integer
 * @returns {Array<Array>} a chunked array
 * @throws {Error} if chunk size is less than 1 or not an integer
 * @example
 * chunk([1, 2, 3, 4, 5, 6], 2);
 * // => [[1, 2], [3, 4], [5, 6]]
 */
function chunk(x/*:Array<any>*/, chunkSize/*:number*/)/*:?Array<Array<any>>*/ {

    // a list of result chunks, as arrays in an array
    var output = [];

    // `chunkSize` must be zero or higher - otherwise the loop below,
    // in which we call `start += chunkSize`, will loop infinitely.
    // So, we'll detect and throw in that case to indicate
    // invalid input.
    if (chunkSize < 1) {
        throw new Error('chunk size must be a positive number');
    }

    if (Math.floor(chunkSize) !== chunkSize) {
        throw new Error('chunk size must be an integer');
    }

    // `start` is the index at which `.slice` will start selecting
    // new array elements
    for (var start = 0; start < x.length; start += chunkSize) {

        // for each chunk, slice that part of the array and add it
        // to the output. The `.slice` function does not change
        // the original array.
        output.push(x.slice(start, start + chunkSize));
    }
    return output;
}

/* @flow */

/**
 * Sampling with replacement is a type of sampling that allows the same
 * item to be picked out of a population more than once.
 *
 * @param {Array<*>} x an array of any kind of value
 * @param {number} n count of how many elements to take
 * @param {Function} [randomSource=Math.random] an optional entropy source that
 * returns numbers between 0 inclusive and 1 exclusive: the range [0, 1)
 * @return {Array} n sampled items from the population
 * @example
 * var values = [1, 2, 3, 4];
 * sampleWithReplacement(values, 2); // returns 2 random values, like [2, 4];
 */
function sampleWithReplacement/*::<T>*/(
    x/*: Array<T> */,
    n/*: number */,
    randomSource/*: ?Function */) {

    if (x.length === 0) {
        return [];
    }

    // a custom random number source can be provided if you want to use
    // a fixed seed or another random number generator, like
    // [random-js](https://www.npmjs.org/package/random-js)
    randomSource = randomSource || Math.random;

    var length = x.length;
    var sample = [];

    for (var i = 0; i < n; i++) {
        var index = Math.floor(randomSource() * length);

        sample.push(x[index]);
    }

    return sample;
}

/* @flow */

/**
 * A [Fisher-Yates shuffle](http://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle)
 * in-place - which means that it **will change the order of the original
 * array by reference**.
 *
 * This is an algorithm that generates a random [permutation](https://en.wikipedia.org/wiki/Permutation)
 * of a set.
 *
 * @param {Array} x sample of one or more numbers
 * @param {Function} [randomSource=Math.random] an optional entropy source that
 * returns numbers between 0 inclusive and 1 exclusive: the range [0, 1)
 * @returns {Array} x
 * @example
 * var x = [1, 2, 3, 4];
 * shuffleInPlace(x);
 * // x is shuffled to a value like [2, 1, 4, 3]
 */
function shuffleInPlace(x/*: Array<any> */, randomSource/*: ?Function */)/*: Array<any> */ {

    // a custom random number source can be provided if you want to use
    // a fixed seed or another random number generator, like
    // [random-js](https://www.npmjs.org/package/random-js)
    randomSource = randomSource || Math.random;

    // store the current length of the x to determine
    // when no elements remain to shuffle.
    var length = x.length;

    // temporary is used to hold an item when it is being
    // swapped between indices.
    var temporary;

    // The index to swap at each stage.
    var index;

    // While there are still items to shuffle
    while (length > 0) {
        // chose a random index within the subset of the array
        // that is not yet shuffled
        index = Math.floor(randomSource() * length--);

        // store the value that we'll move temporarily
        temporary = x[length];

        // swap the value at `x[length]` with `x[index]`
        x[length] = x[index];
        x[index] = temporary;
    }

    return x;
}

/* @flow */

/**
 * A [Fisher-Yates shuffle](http://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle)
 * is a fast way to create a random permutation of a finite set. This is
 * a function around `shuffle_in_place` that adds the guarantee that
 * it will not modify its input.
 *
 * @param {Array} x sample of 0 or more numbers
 * @param {Function} [randomSource=Math.random] an optional entropy source that
 * returns numbers between 0 inclusive and 1 exclusive: the range [0, 1)
 * @return {Array} shuffled version of input
 * @example
 * var shuffled = shuffle([1, 2, 3, 4]);
 * shuffled; // = [2, 3, 1, 4] or any other random permutation
 */
function shuffle/*::<T>*/(x/*: Array<T> */, randomSource/*: ?Function */) {
    // slice the original array so that it is not modified
    var sample = x.slice();

    // and then shuffle that shallow-copied array, in place
    return shuffleInPlace(sample.slice(), randomSource);
}

/* @flow */

/**
 * Create a [simple random sample](http://en.wikipedia.org/wiki/Simple_random_sample)
 * from a given array of `n` elements.
 *
 * The sampled values will be in any order, not necessarily the order
 * they appear in the input.
 *
 * @param {Array<any>} x input array. can contain any type
 * @param {number} n count of how many elements to take
 * @param {Function} [randomSource=Math.random] an optional entropy source that
 * returns numbers between 0 inclusive and 1 exclusive: the range [0, 1)
 * @return {Array} subset of n elements in original array
 *
 * @example
 * var values = [1, 2, 4, 5, 6, 7, 8, 9];
 * sample(values, 3); // returns 3 random values, like [2, 5, 8];
 */
function sample/*:: <T> */(
    x /*: Array<T> */,
    n /*: number */,
    randomSource /*: ?Function */) /*: Array<T> */ {
    // shuffle the original array using a fisher-yates shuffle
    var shuffled = shuffle(x, randomSource);

    // and then return a subset of it - the first `n` elements.
    return shuffled.slice(0, n);
}

/* @flow */

/**
 * For a sorted input, counting the number of unique values
 * is possible in constant time and constant memory. This is
 * a simple implementation of the algorithm.
 *
 * Values are compared with `===`, so objects and non-primitive objects
 * are not handled in any special way.
 *
 * @param {Array<*>} x an array of any kind of value
 * @returns {number} count of unique values
 * @example
 * uniqueCountSorted([1, 2, 3]); // => 3
 * uniqueCountSorted([1, 1, 1]); // => 1
 */
function uniqueCountSorted(x/*: Array<any>*/)/*: number */ {
    var uniqueValueCount = 0,
        lastSeenValue;
    for (var i = 0; i < x.length; i++) {
        if (i === 0 || x[i] !== lastSeenValue) {
            lastSeenValue = x[i];
            uniqueValueCount++;
        }
    }
    return uniqueValueCount;
}

/* @flow */

/**
 * Create a new column x row matrix.
 *
 * @private
 * @param {number} columns
 * @param {number} rows
 * @return {Array<Array<number>>} matrix
 * @example
 * makeMatrix(10, 10);
 */
function makeMatrix(columns, rows) {
    var matrix = [];
    for (var i = 0; i < columns; i++) {
        var column = [];
        for (var j = 0; j < rows; j++) {
            column.push(0);
        }
        matrix.push(column);
    }
    return matrix;
}

/**
 * Generates incrementally computed values based on the sums and sums of
 * squares for the data array
 *
 * @private
 * @param {number} j
 * @param {number} i
 * @param {Array<number>} sums
 * @param {Array<number>} sumsOfSquares
 * @return {number}
 * @example
 * ssq(0, 1, [-1, 0, 2], [1, 1, 5]);
 */
function ssq(j, i, sums, sumsOfSquares) {
    var sji; // s(j, i)
    if (j > 0) {
        var muji = (sums[i] - sums[j - 1]) / (i - j + 1); // mu(j, i)
        sji = sumsOfSquares[i] - sumsOfSquares[j - 1] - (i - j + 1) * muji * muji;
    } else {
        sji = sumsOfSquares[i] - sums[i] * sums[i] / (i + 1);
    }
    if (sji < 0) {
        return 0;
    }
    return sji;
}

/**
 * Function that recursively divides and conquers computations
 * for cluster j
 *
 * @private
 * @param {number} iMin Minimum index in cluster to be computed
 * @param {number} iMax Maximum index in cluster to be computed
 * @param {number} cluster Index of the cluster currently being computed
 * @param {Array<Array<number>>} matrix
 * @param {Array<Array<number>>} backtrackMatrix
 * @param {Array<number>} sums
 * @param {Array<number>} sumsOfSquares
 */
function fillMatrixColumn(iMin, iMax, cluster, matrix, backtrackMatrix, sums, sumsOfSquares) {
    if (iMin > iMax) {
        return;
    }

    // Start at midpoint between iMin and iMax
    var i = Math.floor((iMin + iMax) / 2);

    matrix[cluster][i] = matrix[cluster - 1][i - 1];
    backtrackMatrix[cluster][i] = i;

    var jlow = cluster; // the lower end for j

    if (iMin > cluster) {
        jlow = Math.max(jlow, backtrackMatrix[cluster][iMin - 1] || 0);
    }
    jlow = Math.max(jlow, backtrackMatrix[cluster - 1][i] || 0);

    var jhigh = i - 1; // the upper end for j
    if (iMax < matrix.length - 1) {
        jhigh = Math.min(jhigh, backtrackMatrix[cluster][iMax + 1] || 0);
    }

    var sji;
    var sjlowi;
    var ssqjlow;
    var ssqj;
    for (var j = jhigh; j >= jlow; --j) {
        sji = ssq(j, i, sums, sumsOfSquares);

        if (sji + matrix[cluster - 1][jlow - 1] >= matrix[cluster][i]) {
            break;
        }

        // Examine the lower bound of the cluster border
        sjlowi = ssq(jlow, i, sums, sumsOfSquares);

        ssqjlow = sjlowi + matrix[cluster - 1][jlow - 1];

        if (ssqjlow < matrix[cluster][i]) {
            // Shrink the lower bound
            matrix[cluster][i] = ssqjlow;
            backtrackMatrix[cluster][i] = jlow;
        }
        jlow++;

        ssqj = sji + matrix[cluster - 1][j - 1];
        if (ssqj < matrix[cluster][i]) {
            matrix[cluster][i] = ssqj;
            backtrackMatrix[cluster][i] = j;
        }
    }

    fillMatrixColumn(iMin, i - 1, cluster, matrix, backtrackMatrix, sums, sumsOfSquares);
    fillMatrixColumn(i + 1, iMax, cluster, matrix, backtrackMatrix, sums, sumsOfSquares);
}

/**
 * Initializes the main matrices used in Ckmeans and kicks
 * off the divide and conquer cluster computation strategy
 *
 * @private
 * @param {Array<number>} data sorted array of values
 * @param {Array<Array<number>>} matrix
 * @param {Array<Array<number>>} backtrackMatrix
 */
function fillMatrices(data, matrix, backtrackMatrix) {
    var nValues = matrix[0].length;

    // Shift values by the median to improve numeric stability
    var shift = data[Math.floor(nValues / 2)];

    // Cumulative sum and cumulative sum of squares for all values in data array
    var sums = [];
    var sumsOfSquares = [];

    // Initialize first column in matrix & backtrackMatrix
    for (var i = 0, shiftedValue; i < nValues; ++i) {
        shiftedValue = data[i] - shift;
        if (i === 0) {
            sums.push(shiftedValue);
            sumsOfSquares.push(shiftedValue * shiftedValue);
        } else {
            sums.push(sums[i - 1] + shiftedValue);
            sumsOfSquares.push(sumsOfSquares[i - 1] + shiftedValue * shiftedValue);
        }

        // Initialize for cluster = 0
        matrix[0][i] = ssq(0, i, sums, sumsOfSquares);
        backtrackMatrix[0][i] = 0;
    }

    // Initialize the rest of the columns
    var iMin;
    for (var cluster = 1; cluster < matrix.length; ++cluster) {
        if (cluster < matrix.length - 1) {
            iMin = cluster;
        } else {
            // No need to compute matrix[K-1][0] ... matrix[K-1][N-2]
            iMin = nValues - 1;
        }

        fillMatrixColumn(iMin, nValues - 1, cluster, matrix, backtrackMatrix, sums, sumsOfSquares);
    }
}

/**
 * Ckmeans clustering is an improvement on heuristic-based clustering
 * approaches like Jenks. The algorithm was developed in
 * [Haizhou Wang and Mingzhou Song](http://journal.r-project.org/archive/2011-2/RJournal_2011-2_Wang+Song.pdf)
 * as a [dynamic programming](https://en.wikipedia.org/wiki/Dynamic_programming) approach
 * to the problem of clustering numeric data into groups with the least
 * within-group sum-of-squared-deviations.
 *
 * Minimizing the difference within groups - what Wang & Song refer to as
 * `withinss`, or within sum-of-squares, means that groups are optimally
 * homogenous within and the data is split into representative groups.
 * This is very useful for visualization, where you may want to represent
 * a continuous variable in discrete color or style groups. This function
 * can provide groups that emphasize differences between data.
 *
 * Being a dynamic approach, this algorithm is based on two matrices that
 * store incrementally-computed values for squared deviations and backtracking
 * indexes.
 *
 * This implementation is based on Ckmeans 3.4.6, which introduced a new divide
 * and conquer approach that improved runtime from O(kn^2) to O(kn log(n)).
 *
 * Unlike the [original implementation](https://cran.r-project.org/web/packages/Ckmeans.1d.dp/index.html),
 * this implementation does not include any code to automatically determine
 * the optimal number of clusters: this information needs to be explicitly
 * provided.
 *
 * ### References
 * _Ckmeans.1d.dp: Optimal k-means Clustering in One Dimension by Dynamic
 * Programming_ Haizhou Wang and Mingzhou Song ISSN 2073-4859
 *
 * from The R Journal Vol. 3/2, December 2011
 * @param {Array<number>} x input data, as an array of number values
 * @param {number} nClusters number of desired classes. This cannot be
 * greater than the number of values in the data array.
 * @returns {Array<Array<number>>} clustered input
 * @throws {Error} if the number of requested clusters is higher than the size of the data
 * @example
 * ckmeans([-1, 2, -1, 2, 4, 5, 6, -1, 2, -1], 3);
 * // The input, clustered into groups of similar numbers.
 * //= [[-1, -1, -1, -1], [2, 2, 2], [4, 5, 6]]);
 */
function ckmeans(
    x/*: Array<number> */,
    nClusters/*: number */)/*: Array<Array<number>> */ {

    if (nClusters > x.length) {
        throw new Error('cannot generate more classes than there are data values');
    }

    var sorted = numericSort(x),
        // we'll use this as the maximum number of clusters
        uniqueCount = uniqueCountSorted(sorted);

    // if all of the input values are identical, there's one cluster
    // with all of the input in it.
    if (uniqueCount === 1) {
        return [sorted];
    }

    // named 'S' originally
    var matrix = makeMatrix(nClusters, sorted.length),
        // named 'J' originally
        backtrackMatrix = makeMatrix(nClusters, sorted.length);

    // This is a dynamic programming way to solve the problem of minimizing
    // within-cluster sum of squares. It's similar to linear regression
    // in this way, and this calculation incrementally computes the
    // sum of squares that are later read.
    fillMatrices(sorted, matrix, backtrackMatrix);

    // The real work of Ckmeans clustering happens in the matrix generation:
    // the generated matrices encode all possible clustering combinations, and
    // once they're generated we can solve for the best clustering groups
    // very quickly.
    var clusters = [],
        clusterRight = backtrackMatrix[0].length - 1;

    // Backtrack the clusters from the dynamic programming matrix. This
    // starts at the bottom-right corner of the matrix (if the top-left is 0, 0),
    // and moves the cluster target with the loop.
    for (var cluster = backtrackMatrix.length - 1; cluster >= 0; cluster--) {

        var clusterLeft = backtrackMatrix[cluster][clusterRight];

        // fill the cluster from the sorted input by taking a slice of the
        // array. the backtrack matrix makes this easy - it stores the
        // indexes where the cluster should start and end.
        clusters[cluster] = sorted.slice(clusterLeft, clusterRight + 1);

        if (cluster > 0) {
            clusterRight = clusterLeft - 1;
        }
    }

    return clusters;
}

/* @flow */

/**
 * Given an array of x, this will find the extent of the
 * x and return an array of breaks that can be used
 * to categorize the x into a number of classes. The
 * returned array will always be 1 longer than the number of
 * classes because it includes the minimum value.
 *
 * @param {Array<number>} x an array of number values
 * @param {number} nClasses number of desired classes
 * @returns {Array<number>} array of class break positions
 * @example
 * equalIntervalBreaks([1, 2, 3, 4, 5, 6], 4); // => [1, 2.25, 3.5, 4.75, 6]
 */
function equalIntervalBreaks(x/*: Array<number> */, nClasses/*:number*/)/*: Array<number> */ {

    if (x.length < 2) {
        return x;
    }

    var theMin = min(x);
    var theMax = max(x);

    // the first break will always be the minimum value
    // in the xset
    var breaks = [theMin];

    // The size of each break is the full range of the x
    // divided by the number of classes requested
    var breakSize = (theMax - theMin) / nClasses;

    // In the case of nClasses = 1, this loop won't run
    // and the returned breaks will be [min, max]
    for (var i = 1; i < nClasses; i++) {
        breaks.push(breaks[0] + breakSize * i);
    }

    // the last break will always be the
    // maximum.
    breaks.push(theMax);

    return breaks;
}

/* @flow */

/**
 * [Sample covariance](https://en.wikipedia.org/wiki/Sample_mean_and_sampleCovariance) of two datasets:
 * how much do the two datasets move together?
 * x and y are two datasets, represented as arrays of numbers.
 *
 * @param {Array<number>} x a sample of two or more data points
 * @param {Array<number>} y a sample of two or more data points
 * @throws {Error} if x and y do not have equal lengths
 * @throws {Error} if x or y have length of one or less
 * @returns {number} sample covariance
 * @example
 * sampleCovariance([1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1]); // => -3.5
 */
function sampleCovariance(x /*:Array<number>*/, y /*:Array<number>*/)/*:number*/ {

    // The two datasets must have the same length which must be more than 1
    if (x.length !== y.length) {
        throw new Error('sampleCovariance requires samples with equal lengths');
    }

    if (x.length < 2) {
        throw new Error('sampleCovariance requires at least two data points in each sample');
    }

    // determine the mean of each dataset so that we can judge each
    // value of the dataset fairly as the difference from the mean. this
    // way, if one dataset is [1, 2, 3] and [2, 3, 4], their covariance
    // does not suffer because of the difference in absolute values
    var xmean = mean(x),
        ymean = mean(y),
        sum = 0;

    // for each pair of values, the covariance increases when their
    // difference from the mean is associated - if both are well above
    // or if both are well below
    // the mean, the covariance increases significantly.
    for (var i = 0; i < x.length; i++) {
        sum += (x[i] - xmean) * (y[i] - ymean);
    }

    // this is Bessels' Correction: an adjustment made to sample statistics
    // that allows for the reduced degree of freedom entailed in calculating
    // values from samples rather than complete populations.
    var besselsCorrection = x.length - 1;

    // the covariance is weighted by the length of the datasets.
    return sum / besselsCorrection;
}

/* @flow */

/**
 * The [sample variance](https://en.wikipedia.org/wiki/Variance#Sample_variance)
 * is the sum of squared deviations from the mean. The sample variance
 * is distinguished from the variance by the usage of [Bessel's Correction](https://en.wikipedia.org/wiki/Bessel's_correction):
 * instead of dividing the sum of squared deviations by the length of the input,
 * it is divided by the length minus one. This corrects the bias in estimating
 * a value from a set that you don't know if full.
 *
 * References:
 * * [Wolfram MathWorld on Sample Variance](http://mathworld.wolfram.com/SampleVariance.html)
 *
 * @param {Array<number>} x a sample of two or more data points
 * @throws {Error} if the length of x is less than 2
 * @return {number} sample variance
 * @example
 * sampleVariance([1, 2, 3, 4, 5]); // => 2.5
 */
function sampleVariance(x /*: Array<number> */)/*:number*/ {
    // The variance of no numbers is null
    if (x.length < 2) {
        throw new Error('sampleVariance requires at least two data points');
    }

    var sumSquaredDeviationsValue = sumNthPowerDeviations(x, 2);

    // this is Bessels' Correction: an adjustment made to sample statistics
    // that allows for the reduced degree of freedom entailed in calculating
    // values from samples rather than complete populations.
    var besselsCorrection = x.length - 1;

    // Find the mean value of that list
    return sumSquaredDeviationsValue / besselsCorrection;
}

/* @flow */

/**
 * The [sample standard deviation](http://en.wikipedia.org/wiki/Standard_deviation#Sample_standard_deviation)
 * is the square root of the sample variance.
 *
 * @param {Array<number>} x input array
 * @returns {number} sample standard deviation
 * @example
 * sampleStandardDeviation([2, 4, 4, 4, 5, 5, 7, 9]).toFixed(2);
 * // => '2.14'
 */
function sampleStandardDeviation(x/*:Array<number>*/)/*:number*/ {
    // The standard deviation of no numbers is null
    var sampleVarianceX = sampleVariance(x);
    return Math.sqrt(sampleVarianceX);
}

/* @flow */

/**
 * The [correlation](http://en.wikipedia.org/wiki/Correlation_and_dependence) is
 * a measure of how correlated two datasets are, between -1 and 1
 *
 * @param {Array<number>} x first input
 * @param {Array<number>} y second input
 * @returns {number} sample correlation
 * @example
 * sampleCorrelation([1, 2, 3, 4, 5, 6], [2, 2, 3, 4, 5, 60]).toFixed(2);
 * // => '0.69'
 */
function sampleCorrelation(x/*: Array<number> */, y/*: Array<number> */)/*:number*/ {
    var cov = sampleCovariance(x, y),
        xstd = sampleStandardDeviation(x),
        ystd = sampleStandardDeviation(y);

    return cov / xstd / ystd;
}

/* @flow */

/**
 * [Skewness](http://en.wikipedia.org/wiki/Skewness) is
 * a measure of the extent to which a probability distribution of a
 * real-valued random variable "leans" to one side of the mean.
 * The skewness value can be positive or negative, or even undefined.
 *
 * Implementation is based on the adjusted Fisher-Pearson standardized
 * moment coefficient, which is the version found in Excel and several
 * statistical packages including Minitab, SAS and SPSS.
 *
 * @since 4.1.0
 * @param {Array<number>} x a sample of 3 or more data points
 * @returns {number} sample skewness
 * @throws {Error} if x has length less than 3
 * @example
 * sampleSkewness([2, 4, 6, 3, 1]); // => 0.590128656384365
 */
function sampleSkewness(x /*: Array<number> */)/*:number*/ {

    if (x.length < 3) {
        throw new Error('sampleSkewness requires at least three data points');
    }

    var meanValue = mean(x);
    var tempValue;
    var sumSquaredDeviations = 0;
    var sumCubedDeviations = 0;

    for (var i = 0; i < x.length; i++) {
        tempValue = x[i] - meanValue;
        sumSquaredDeviations += tempValue * tempValue;
        sumCubedDeviations += tempValue * tempValue * tempValue;
    }

    // this is Bessels' Correction: an adjustment made to sample statistics
    // that allows for the reduced degree of freedom entailed in calculating
    // values from samples rather than complete populations.
    var besselsCorrection = x.length - 1;

    // Find the mean value of that list
    var theSampleStandardDeviation = Math.sqrt(sumSquaredDeviations / besselsCorrection);

    var n = x.length,
        cubedS = Math.pow(theSampleStandardDeviation, 3);

    return n * sumCubedDeviations / ((n - 1) * (n - 2) * cubedS);
}

/* @flow */

/**
 * [Kurtosis](http://en.wikipedia.org/wiki/Kurtosis) is
 * a measure of the heaviness of a distribution's tails relative to its
 * variance. The kurtosis value can be positive or negative, or even undefined.
 *
 * Implementation is based on Fisher's excess kurtosis definition and uses
 * unbiased moment estimators. This is the version found in Excel and available
 * in several statistical packages, including SAS and SciPy.
 *
 * @param {Array<number>} x a sample of 4 or more data points
 * @returns {number} sample kurtosis
 * @throws {Error} if x has length less than 4
 * @example
 * sampleKurtosis([1, 2, 2, 3, 5]); // => 1.4555765595463122
 */
function sampleKurtosis(x /*: Array<number> */)/*:number*/ {

    var n = x.length;

    if (n < 4) {
        throw new Error('sampleKurtosis requires at least four data points');
    }

    var meanValue = mean(x);
    var tempValue;
    var secondCentralMoment = 0;
    var fourthCentralMoment = 0;

    for (var i = 0; i < n; i++) {
        tempValue = x[i] - meanValue;
        secondCentralMoment += tempValue * tempValue;
        fourthCentralMoment += tempValue * tempValue * tempValue * tempValue;
    }

    return (n - 1) / ((n - 2) * (n - 3)) *
        (n * (n + 1) * fourthCentralMoment / (secondCentralMoment * secondCentralMoment) - 3 * (n - 1));
}

/* @flow */

/**
 * Implementation of [Heap's Algorithm](https://en.wikipedia.org/wiki/Heap%27s_algorithm)
 * for generating permutations.
 *
 * @param {Array} elements any type of data
 * @returns {Array<Array>} array of permutations
 */
function permutationsHeap/*:: <T> */(elements /*: Array<T> */)/*: Array<Array<T>> */ {
    var indexes = new Array(elements.length);
    var permutations = [elements.slice()];

    for (var i = 0; i < elements.length; i++) {
        indexes[i] = 0;
    }

    for (i = 0; i < elements.length;) {
        if (indexes[i] < i) {

            // At odd indexes, swap from indexes[i] instead
            // of from the beginning of the array
            var swapFrom = 0;
            if (i % 2 !== 0) {
                swapFrom = indexes[i];
            }

            // swap between swapFrom and i, using
            // a temporary variable as storage.
            var temp = elements[swapFrom];
            elements[swapFrom] = elements[i];
            elements[i] = temp;

            permutations.push(elements.slice());
            indexes[i]++;
            i = 0;

        } else {
            indexes[i] = 0;
            i++;
        }
    }

    return permutations;
}

/* @flow */

/**
 * Implementation of Combinations
 * Combinations are unique subsets of a collection - in this case, k x from a collection at a time.
 * https://en.wikipedia.org/wiki/Combination
 * @param {Array} x any type of data
 * @param {int} k the number of objects in each group (without replacement)
 * @returns {Array<Array>} array of permutations
 * @example
 * combinations([1, 2, 3], 2); // => [[1,2], [1,3], [2,3]]
 */

function combinations(
    x/*: Array<any> */,
    k/*: number */)/*: Array<Array<any>> */ {
    var i;
    var subI;
    var combinationList = [];
    var subsetCombinations;
    var next;

    for (i = 0; i < x.length; i++) {
        if (k === 1) {
            combinationList.push([x[i]]);
        } else {
            subsetCombinations = combinations(x.slice( i + 1, x.length ), k - 1);
            for (subI = 0; subI < subsetCombinations.length; subI++) {
                next = subsetCombinations[subI];
                next.unshift(x[i]);
                combinationList.push(next);
            }
        }
    }
    return combinationList;
}

/* @flow */

/**
 * Implementation of [Combinations](https://en.wikipedia.org/wiki/Combination) with replacement
 * Combinations are unique subsets of a collection - in this case, k x from a collection at a time.
 * 'With replacement' means that a given element can be chosen multiple times.
 * Unlike permutation, order doesn't matter for combinations.
 *
 * @param {Array} x any type of data
 * @param {int} k the number of objects in each group (without replacement)
 * @returns {Array<Array>} array of permutations
 * @example
 * combinationsReplacement([1, 2], 2); // => [[1, 1], [1, 2], [2, 2]]
 */
function combinationsReplacement(
    x /*: Array<any> */,
    k /*: number */)/*: Array<Array<any>> */ {

    var combinationList = [];

    for (var i = 0; i < x.length; i++) {
        if (k === 1) {
            // If we're requested to find only one element, we don't need
            // to recurse: just push `x[i]` onto the list of combinations.
            combinationList.push([x[i]]);
        } else {
            // Otherwise, recursively find combinations, given `k - 1`. Note that
            // we request `k - 1`, so if you were looking for k=3 combinations, we're
            // requesting k=2. This -1 gets reversed in the for loop right after this
            // code, since we concatenate `x[i]` onto the selected combinations,
            // bringing `k` back up to your requested level.
            // This recursion may go many levels deep, since it only stops once
            // k=1.
            var subsetCombinations = combinationsReplacement(
                x.slice(i, x.length),
                k - 1);

            for (var j = 0; j < subsetCombinations.length; j++) {
                combinationList.push([x[i]]
                    .concat(subsetCombinations[j]));
            }
        }
    }

    return combinationList;
}

/* @flow */

/**
 * When adding a new value to a list, one does not have to necessary
 * recompute the mean of the list in linear time. They can instead use
 * this function to compute the new mean by providing the current mean,
 * the number of elements in the list that produced it and the new
 * value to add.
 *
 * @since 2.5.0
 * @param {number} mean current mean
 * @param {number} n number of items in the list
 * @param {number} newValue the added value
 * @returns {number} the new mean
 *
 * @example
 * addToMean(14, 5, 53); // => 20.5
 */
function addToMean(mean /*: number*/, n/*: number */, newValue/*: number */)/*: number */ {
    return mean + ((newValue - mean) / (n + 1));
}

/* @flow */

/**
 * When combining two lists of values for which one already knows the means,
 * one does not have to necessary recompute the mean of the combined lists in
 * linear time. They can instead use this function to compute the combined
 * mean by providing the mean & number of values of the first list and the mean
 * & number of values of the second list.
 *
 * @since 3.0.0
 * @param {number} mean1 mean of the first list
 * @param {number} n1 number of items in the first list
 * @param {number} mean2 mean of the second list
 * @param {number} n2 number of items in the second list
 * @returns {number} the combined mean
 *
 * @example
 * combineMeans(5, 3, 4, 3); // => 4.5
 */
function combineMeans(mean1 /*: number*/, n1/*: number */, mean2 /*: number*/, n2/*: number */)/*: number */ {
    return (mean1 * n1 + mean2 * n2) / (n1 + n2);
}

/* @flow */

/**
 * When combining two lists of values for which one already knows the variances,
 * one does not have to necessary recompute the variance of the combined lists
 * in linear time. They can instead use this function to compute the combined
 * variance by providing the variance, mean & number of values of the first list
 * and the variance, mean & number of values of the second list.
 *
 * @since 3.0.0
 * @param {number} variance1 variance of the first list
 * @param {number} mean1 mean of the first list
 * @param {number} n1 number of items in the first list
 * @param {number} variance2 variance of the second list
 * @param {number} mean2 mean of the second list
 * @param {number} n2 number of items in the second list
 * @returns {number} the combined mean
 *
 * @example
 * combineVariances(14 / 3, 5, 3, 8 / 3, 4, 3); // => 47 / 12
 */
function combineVariances(
    variance1 /*: number*/,
    mean1 /*: number*/,
    n1/*: number */,
    variance2 /*: number*/,
    mean2 /*: number*/,
    n2/*: number */)/*: number */ {

    var newMean = combineMeans(mean1, n1, mean2, n2);

    return (
        n1 * (variance1 + Math.pow(mean1 - newMean, 2)) +
        n2 * (variance2 + Math.pow(mean2 - newMean, 2))
    ) / (n1 + n2);
}

/* @flow */

/**
 * The [Geometric Mean](https://en.wikipedia.org/wiki/Geometric_mean) is
 * a mean function that is more useful for numbers in different
 * ranges.
 *
 * This is the nth root of the input numbers multiplied by each other.
 *
 * The geometric mean is often useful for
 * **[proportional growth](https://en.wikipedia.org/wiki/Geometric_mean#Proportional_growth)**: given
 * growth rates for multiple years, like _80%, 16.66% and 42.85%_, a simple
 * mean will incorrectly estimate an average growth rate, whereas a geometric
 * mean will correctly estimate a growth rate that, over those years,
 * will yield the same end value.
 *
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x sample of one or more data points
 * @returns {number} geometric mean
 * @throws {Error} if x is empty
 * @throws {Error} if x contains a negative number
 * @example
 * var growthRates = [1.80, 1.166666, 1.428571];
 * var averageGrowth = ss.geometricMean(growthRates);
 * var averageGrowthRates = [averageGrowth, averageGrowth, averageGrowth];
 * var startingValue = 10;
 * var startingValueMean = 10;
 * growthRates.forEach(function(rate) {
 *   startingValue *= rate;
 * });
 * averageGrowthRates.forEach(function(rate) {
 *   startingValueMean *= rate;
 * });
 * startingValueMean === startingValue;
 */
function geometricMean(x /*: Array<number> */)/*: number */ {
    // The mean of no numbers is null
    if (x.length === 0) {
        throw new Error('geometricMean requires at least one data point');
    }

    // the starting value.
    var value = 1;

    for (var i = 0; i < x.length; i++) {
        // the geometric mean is only valid for positive numbers
        if (x[i] <= 0) {
            throw new Error('geometricMean requires only positive numbers as input');
        }

        // repeatedly multiply the value by each number
        value *= x[i];
    }

    return Math.pow(value, 1 / x.length);
}

/* @flow */

/**
 * The [Harmonic Mean](https://en.wikipedia.org/wiki/Harmonic_mean) is
 * a mean function typically used to find the average of rates.
 * This mean is calculated by taking the reciprocal of the arithmetic mean
 * of the reciprocals of the input numbers.
 *
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * This runs on `O(n)`, linear time in respect to the array.
 *
 * @param {Array<number>} x sample of one or more data points
 * @returns {number} harmonic mean
 * @throws {Error} if x is empty
 * @throws {Error} if x contains a negative number
 * @example
 * harmonicMean([2, 3]).toFixed(2) // => '2.40'
 */
function harmonicMean(x /*: Array<number> */)/*: number */ {
    // The mean of no numbers is null
    if (x.length === 0) {
        throw new Error('harmonicMean requires at least one data point');
    }

    var reciprocalSum = 0;

    for (var i = 0; i < x.length; i++) {
        // the harmonic mean is only valid for positive numbers
        if (x[i] <= 0) {
            throw new Error('harmonicMean requires only positive numbers as input');
        }

        reciprocalSum += 1 / x[i];
    }

    // divide n by the the reciprocal sum
    return x.length / reciprocalSum;
}

/* @flow */

/**
 * The [median](http://en.wikipedia.org/wiki/Median) is
 * the middle number of a list. This is often a good indicator of 'the middle'
 * when there are outliers that skew the `mean()` value.
 * This is a [measure of central tendency](https://en.wikipedia.org/wiki/Central_tendency):
 * a method of finding a typical or central value of a set of numbers.
 *
 * The median isn't necessarily one of the elements in the list: the value
 * can be the average of two elements if the list has an even length
 * and the two central values are different.
 *
 * @param {Array<number>} sorted input
 * @returns {number} median value
 * @example
 * medianSorted([10, 2, 5, 100, 2, 1]); // => 52.5
 */
function medianSorted(sorted /*: Array<number> */)/*:number*/ {
    return quantileSorted(sorted, 0.5);
}

/* @flow */

/**
 * When removing a value from a list, one does not have to necessary
 * recompute the mean of the list in linear time. They can instead use
 * this function to compute the new mean by providing the current mean,
 * the number of elements in the list that produced it and the value to remove.
 *
 * @since 3.0.0
 * @param {number} mean current mean
 * @param {number} n number of items in the list
 * @param {number} value the value to remove
 * @returns {number} the new mean
 *
 * @example
 * subtractFromMean(20.5, 6, 53); // => 14
 */
function subtractFromMean(mean /*: number*/, n/*: number */, value/*: number */)/*: number */ {
    return ((mean * n) - value) / (n - 1);
}

/* @flow */

/**
 * The Root Mean Square (RMS) is
 * a mean function used as a measure of the magnitude of a set
 * of numbers, regardless of their sign.
 * This is the square root of the mean of the squares of the
 * input numbers.
 * This runs on `O(n)`, linear time in respect to the array
 *
 * @param {Array<number>} x a sample of one or more data points
 * @returns {number} root mean square
 * @throws {Error} if x is empty
 * @example
 * rootMeanSquare([-1, 1, -1, 1]); // => 1
 */
function rootMeanSquare(x /*: Array<number> */)/*:number*/ {
    if (x.length === 0) {
        throw new Error('rootMeanSquare requires at least one data point');
    }

    var sumOfSquares = 0;
    for (var i = 0; i < x.length; i++) {
        sumOfSquares += Math.pow(x[i], 2);
    }

    return Math.sqrt(sumOfSquares / x.length);
}

/* @flow */

/**
 * This is to compute [a one-sample t-test](https://en.wikipedia.org/wiki/Student%27s_t-test#One-sample_t-test), comparing the mean
 * of a sample to a known value, x.
 *
 * in this case, we're trying to determine whether the
 * population mean is equal to the value that we know, which is `x`
 * here. usually the results here are used to look up a
 * [p-value](http://en.wikipedia.org/wiki/P-value), which, for
 * a certain level of significance, will let you determine that the
 * null hypothesis can or cannot be rejected.
 *
 * @param {Array<number>} x sample of one or more numbers
 * @param {number} expectedValue expected value of the population mean
 * @returns {number} value
 * @example
 * tTest([1, 2, 3, 4, 5, 6], 3.385).toFixed(2); // => '0.16'
 */
function tTest(x/*: Array<number> */, expectedValue/*: number */)/*:number*/ {
    // The mean of the sample
    var sampleMean = mean(x);

    // The standard deviation of the sample
    var sd = standardDeviation(x);

    // Square root the length of the sample
    var rootN = Math.sqrt(x.length);

    // returning the t value
    return (sampleMean - expectedValue) / (sd / rootN);
}

/* @flow */

/**
 * This is to compute [two sample t-test](http://en.wikipedia.org/wiki/Student's_t-test).
 * Tests whether "mean(X)-mean(Y) = difference", (
 * in the most common case, we often have `difference == 0` to test if two samples
 * are likely to be taken from populations with the same mean value) with
 * no prior knowledge on standard deviations of both samples
 * other than the fact that they have the same standard deviation.
 *
 * Usually the results here are used to look up a
 * [p-value](http://en.wikipedia.org/wiki/P-value), which, for
 * a certain level of significance, will let you determine that the
 * null hypothesis can or cannot be rejected.
 *
 * `diff` can be omitted if it equals 0.
 *
 * [This is used to confirm or deny](http://www.monarchlab.org/Lab/Research/Stats/2SampleT.aspx)
 * a null hypothesis that the two populations that have been sampled into
 * `sampleX` and `sampleY` are equal to each other.
 *
 * @param {Array<number>} sampleX a sample as an array of numbers
 * @param {Array<number>} sampleY a sample as an array of numbers
 * @param {number} [difference=0]
 * @returns {number|null} test result
 *
 * @example
 * tTestTwoSample([1, 2, 3, 4], [3, 4, 5, 6], 0); // => -2.1908902300206643
 */
function tTestTwoSample(
    sampleX/*: Array<number> */,
    sampleY/*: Array<number> */,
    difference/*: ?number */)/*: ?number */ {
    var n = sampleX.length,
        m = sampleY.length;

    // If either sample doesn't actually have any values, we can't
    // compute this at all, so we return `null`.
    if (!n || !m) { return null; }

    // default difference (mu) is zero
    if (!difference) {
        difference = 0;
    }

    var meanX = mean(sampleX),
        meanY = mean(sampleY),
        sampleVarianceX = sampleVariance(sampleX),
        sampleVarianceY = sampleVariance(sampleY);

    if (typeof meanX === 'number' &&
        typeof meanY === 'number' &&
        typeof sampleVarianceX === 'number' &&
        typeof sampleVarianceY === 'number') {
        var weightedVariance = ((n - 1) * sampleVarianceX +
            (m - 1) * sampleVarianceY) / (n + m - 2);

        return (meanX - meanY - difference) /
            Math.sqrt(weightedVariance * (1 / n + 1 / m));
    }
}

/* @flow */

/**
 * [Bayesian Classifier](http://en.wikipedia.org/wiki/Naive_Bayes_classifier)
 *
 * This is a naïve bayesian classifier that takes
 * singly-nested objects.
 *
 * @class
 * @example
 * var bayes = new BayesianClassifier();
 * bayes.train({
 *   species: 'Cat'
 * }, 'animal');
 * var result = bayes.score({
 *   species: 'Cat'
 * })
 * // result
 * // {
 * //   animal: 1
 * // }
 */
function BayesianClassifier() {
    // The number of items that are currently
    // classified in the model
    this.totalCount = 0;
    // Every item classified in the model
    this.data = {};
}

/**
 * Train the classifier with a new item, which has a single
 * dimension of Javascript literal keys and values.
 *
 * @param {Object} item an object with singly-deep properties
 * @param {string} category the category this item belongs to
 * @return {undefined} adds the item to the classifier
 */
BayesianClassifier.prototype.train = function(item, category) {
    // If the data object doesn't have any values
    // for this category, create a new object for it.
    if (!this.data[category]) {
        this.data[category] = {};
    }

    // Iterate through each key in the item.
    for (var k in item) {
        var v = item[k];
        // Initialize the nested object `data[category][k][item[k]]`
        // with an object of keys that equal 0.
        if (this.data[category][k] === undefined) {
            this.data[category][k] = {};
        }
        if (this.data[category][k][v] === undefined) {
            this.data[category][k][v] = 0;
        }

        // And increment the key for this key/value combination.
        this.data[category][k][v]++;
    }

    // Increment the number of items classified
    this.totalCount++;
};

/**
 * Generate a score of how well this item matches all
 * possible categories based on its attributes
 *
 * @param {Object} item an item in the same format as with train
 * @returns {Object} of probabilities that this item belongs to a
 * given category.
 */
BayesianClassifier.prototype.score = function(item) {
    // Initialize an empty array of odds per category.
    var odds = {}, category;
    // Iterate through each key in the item,
    // then iterate through each category that has been used
    // in previous calls to `.train()`
    for (var k in item) {
        var v = item[k];
        for (category in this.data) {
            // Create an empty object for storing key - value combinations
            // for this category.
            odds[category] = {};

            // If this item doesn't even have a property, it counts for nothing,
            // but if it does have the property that we're looking for from
            // the item to categorize, it counts based on how popular it is
            // versus the whole population.
            if (this.data[category][k]) {
                odds[category][k + '_' + v] = (this.data[category][k][v] || 0) / this.totalCount;
            } else {
                odds[category][k + '_' + v] = 0;
            }
        }
    }

    // Set up a new object that will contain sums of these odds by category
    var oddsSums = {};

    for (category in odds) {
        // Tally all of the odds for each category-combination pair -
        // the non-existence of a category does not add anything to the
        // score.
        oddsSums[category] = 0;
        for (var combination in odds[category]) {
            oddsSums[category] += odds[category][combination];
        }
    }

    return oddsSums;
};

/* @flow */

/**
 * This is a single-layer [Perceptron Classifier](http://en.wikipedia.org/wiki/Perceptron) that takes
 * arrays of numbers and predicts whether they should be classified
 * as either 0 or 1 (negative or positive examples).
 * @class
 * @example
 * // Create the model
 * var p = new PerceptronModel();
 * // Train the model with input with a diagonal boundary.
 * for (var i = 0; i < 5; i++) {
 *     p.train([1, 1], 1);
 *     p.train([0, 1], 0);
 *     p.train([1, 0], 0);
 *     p.train([0, 0], 0);
 * }
 * p.predict([0, 0]); // 0
 * p.predict([0, 1]); // 0
 * p.predict([1, 0]); // 0
 * p.predict([1, 1]); // 1
 */
function PerceptronModel() {
    // The weights, or coefficients of the model;
    // weights are only populated when training with data.
    this.weights = [];
    // The bias term, or intercept; it is also a weight but
    // it's stored separately for convenience as it is always
    // multiplied by one.
    this.bias = 0;
}

/**
 * **Predict**: Use an array of features with the weight array and bias
 * to predict whether an example is labeled 0 or 1.
 *
 * @param {Array<number>} features an array of features as numbers
 * @returns {number} 1 if the score is over 0, otherwise 0
 */
PerceptronModel.prototype.predict = function(features) {

    // Only predict if previously trained
    // on the same size feature array(s).
    if (features.length !== this.weights.length) { return null; }

    // Calculate the sum of features times weights,
    // with the bias added (implicitly times one).
    var score = 0;
    for (var i = 0; i < this.weights.length; i++) {
        score += this.weights[i] * features[i];
    }
    score += this.bias;

    // Classify as 1 if the score is over 0, otherwise 0.
    if (score > 0) {
        return 1;
    } else {
        return 0;
    }
};

/**
 * **Train** the classifier with a new example, which is
 * a numeric array of features and a 0 or 1 label.
 *
 * @param {Array<number>} features an array of features as numbers
 * @param {number} label either 0 or 1
 * @returns {PerceptronModel} this
 */
PerceptronModel.prototype.train = function(features, label) {
    // Require that only labels of 0 or 1 are considered.
    if (label !== 0 && label !== 1) { return null; }
    // The length of the feature array determines
    // the length of the weight array.
    // The perceptron will continue learning as long as
    // it keeps seeing feature arrays of the same length.
    // When it sees a new data shape, it initializes.
    if (features.length !== this.weights.length) {
        this.weights = features;
        this.bias = 1;
    }
    // Make a prediction based on current weights.
    var prediction = this.predict(features);
    // Update the weights if the prediction is wrong.
    if (prediction !== label) {
        var gradient = label - prediction;
        for (var i = 0; i < this.weights.length; i++) {
            this.weights[i] += gradient * features[i];
        }
        this.bias += gradient;
    }
    return this;
};

/* @flow */

/**
 * We use `ε`, epsilon, as a stopping criterion when we want to iterate
 * until we're "close enough". Epsilon is a very small number: for
 * simple statistics, that number is **0.0001**
 *
 * This is used in calculations like the binomialDistribution, in which
 * the process of finding a value is [iterative](https://en.wikipedia.org/wiki/Iterative_method):
 * it progresses until it is close enough.
 *
 * Below is an example of using epsilon in [gradient descent](https://en.wikipedia.org/wiki/Gradient_descent),
 * where we're trying to find a local minimum of a function's derivative,
 * given by the `fDerivative` method.
 *
 * @example
 * // From calculation, we expect that the local minimum occurs at x=9/4
 * var x_old = 0;
 * // The algorithm starts at x=6
 * var x_new = 6;
 * var stepSize = 0.01;
 *
 * function fDerivative(x) {
 *   return 4 * Math.pow(x, 3) - 9 * Math.pow(x, 2);
 * }
 *
 * // The loop runs until the difference between the previous
 * // value and the current value is smaller than epsilon - a rough
 * // meaure of 'close enough'
 * while (Math.abs(x_new - x_old) > ss.epsilon) {
 *   x_old = x_new;
 *   x_new = x_old - stepSize * fDerivative(x_old);
 * }
 *
 * console.log('Local minimum occurs at', x_new);
 */
var epsilon = 0.0001;

/* @flow */

/**
 * A [Factorial](https://en.wikipedia.org/wiki/Factorial), usually written n!, is the product of all positive
 * integers less than or equal to n. Often factorial is implemented
 * recursively, but this iterative approach is significantly faster
 * and simpler.
 *
 * @param {number} n input, must be an integer number 1 or greater
 * @returns {number} factorial: n!
 * @throws {Error} if n is less than 0 or not an integer
 * @example
 * factorial(5); // => 120
 */
function factorial(n /*: number */)/*: number */ {

    // factorial is mathematically undefined for negative numbers
    if (n < 0) {
        throw new Error('factorial requires a non-negative value');
    }

    if (Math.floor(n) !== n) {
        throw new Error('factorial requires an integer input');
    }

    // typically you'll expand the factorial function going down, like
    // 5! = 5 * 4 * 3 * 2 * 1. This is going in the opposite direction,
    // counting from 2 up to the number in question, and since anything
    // multiplied by 1 is itself, the loop only needs to start at 2.
    var accumulator = 1;
    for (var i = 2; i <= n; i++) {
        // for each number up to and including the number `n`, multiply
        // the accumulator my that number.
        accumulator *= i;
    }
    return accumulator;
}

/* @flow */

/**
 * Compute the [gamma function](https://en.wikipedia.org/wiki/Gamma_function) of a value using Nemes' approximation.
 * The gamma of n is equivalent to (n-1)!, but unlike the factorial function, gamma is defined for all real n except zero 
 * and negative integers (where NaN is returned). Note, the gamma function is also well-defined for complex numbers, 
 * though this implementation currently does not handle complex numbers as input values.
 * Nemes' approximation is defined [here](https://arxiv.org/abs/1003.6020) as Theorem 2.2.
 * Negative values use [Euler's reflection formula](https://en.wikipedia.org/wiki/Gamma_function#Properties) for computation.
 *
 * @param {number} n Any real number except for zero and negative integers.
 * @returns {number} The gamma of the input value.
 *
 * @example
 * gamma(11.5); // 11899423.084037038
 * gamma(-11.5); // 2.29575810481609e-8 
 * gamma(5); // 24 
 */
function gamma(n /*: number */ ) /*: number */ {

    if (isInteger(n)) {
        if (n <= 0) {
            // gamma not defined for zero or negative integers
            return NaN;
        } else {
            // use factorial for integer inputs 
            return factorial(n - 1);
        }
    }

    // Decrement n, because approximation is defined for n - 1
    n--;


    if (n < 0) {
        // Use Euler's reflection formula for negative inputs
        // see:  https://en.wikipedia.org/wiki/Gamma_function#Properties
        return Math.PI / (Math.sin(Math.PI * -n) * gamma(-n));

    } else {
        // Nemes' expansion approximation
        var seriesCoefficient = Math.pow((n / Math.E), n) * Math.sqrt(2 * Math.PI * (n + (1 / 6)));

        var seriesDenom = n + 1 / 4;

        var seriesExpansion = (1 +
            (1 / 144) / Math.pow(seriesDenom, 2) -
            (1 / 12960) / Math.pow(seriesDenom, 3) -
            (257 / 207360) / Math.pow(seriesDenom, 4) -
            (52 / 2612736) / Math.pow(seriesDenom, 5) +
            (5741173 / 9405849600) / Math.pow(seriesDenom, 6) +
            (37529 / 18811699200) / Math.pow(seriesDenom, 7));

        return seriesCoefficient * seriesExpansion;
    }

}

function isInteger(value) {
    return typeof value === 'number' &&
        isFinite(value) &&
        Math.floor(value) === value;
}

/* @flow */

/**
 * The [Bernoulli distribution](http://en.wikipedia.org/wiki/Bernoulli_distribution)
 * is the probability discrete
 * distribution of a random variable which takes value 1 with success
 * probability `p` and value 0 with failure
 * probability `q` = 1 - `p`. It can be used, for example, to represent the
 * toss of a coin, where "1" is defined to mean "heads" and "0" is defined
 * to mean "tails" (or vice versa). It is
 * a special case of a Binomial Distribution
 * where `n` = 1.
 *
 * @param {number} p input value, between 0 and 1 inclusive
 * @returns {number[]} values of bernoulli distribution at this point
 * @throws {Error} if p is outside 0 and 1
 * @example
 * bernoulliDistribution(0.3); // => [0.7, 0.3]
 */
function bernoulliDistribution(p/*: number */) /*: number[] */ {
    // Check that `p` is a valid probability (0 ≤ p ≤ 1)
    if (p < 0 || p > 1 ) {
        throw new Error('bernoulliDistribution requires probability to be between 0 and 1 inclusive');
    }

    return [1 - p, p];
}

/* @flow */

/**
 * The [Binomial Distribution](http://en.wikipedia.org/wiki/Binomial_distribution) is the discrete probability
 * distribution of the number of successes in a sequence of n independent yes/no experiments, each of which yields
 * success with probability `probability`. Such a success/failure experiment is also called a Bernoulli experiment or
 * Bernoulli trial; when trials = 1, the Binomial Distribution is a Bernoulli Distribution.
 *
 * @param {number} trials number of trials to simulate
 * @param {number} probability
 * @returns {number[]} output
 */
function binomialDistribution(
    trials/*: number */,
    probability/*: number */)/*: ?number[] */ {
    // Check that `p` is a valid probability (0 ≤ p ≤ 1),
    // that `n` is an integer, strictly positive.
    if (probability < 0 || probability > 1 ||
        trials <= 0 || trials % 1 !== 0) {
        return undefined;
    }

    // We initialize `x`, the random variable, and `accumulator`, an accumulator
    // for the cumulative distribution function to 0. `distribution_functions`
    // is the object we'll return with the `probability_of_x` and the
    // `cumulativeProbability_of_x`, as well as the calculated mean &
    // variance. We iterate until the `cumulativeProbability_of_x` is
    // within `epsilon` of 1.0.
    var x = 0,
        cumulativeProbability = 0,
        cells = [],
        binomialCoefficient = 1;

    // This algorithm iterates through each potential outcome,
    // until the `cumulativeProbability` is very close to 1, at
    // which point we've defined the vast majority of outcomes
    do {
        // a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function)
        cells[x] = binomialCoefficient *
            Math.pow(probability, x) * Math.pow(1 - probability, trials - x);
        cumulativeProbability += cells[x];
        x++;
        binomialCoefficient = binomialCoefficient * (trials - x + 1) / x;
    // when the cumulativeProbability is nearly 1, we've calculated
    // the useful range of this distribution
    } while (cumulativeProbability < 1 - epsilon);

    return cells;
}

/* @flow */

/**
 * The [Poisson Distribution](http://en.wikipedia.org/wiki/Poisson_distribution)
 * is a discrete probability distribution that expresses the probability
 * of a given number of events occurring in a fixed interval of time
 * and/or space if these events occur with a known average rate and
 * independently of the time since the last event.
 *
 * The Poisson Distribution is characterized by the strictly positive
 * mean arrival or occurrence rate, `λ`.
 *
 * @param {number} lambda location poisson distribution
 * @returns {number[]} values of poisson distribution at that point
 */
function poissonDistribution(lambda/*: number */) /*: ?number[] */ {
    // Check that lambda is strictly positive
    if (lambda <= 0) { return undefined; }

    // our current place in the distribution
    var x = 0,
        // and we keep track of the current cumulative probability, in
        // order to know when to stop calculating chances.
        cumulativeProbability = 0,
        // the calculated cells to be returned
        cells = [],
        factorialX = 1;

    // This algorithm iterates through each potential outcome,
    // until the `cumulativeProbability` is very close to 1, at
    // which point we've defined the vast majority of outcomes
    do {
        // a [probability mass function](https://en.wikipedia.org/wiki/Probability_mass_function)
        cells[x] = (Math.exp(-lambda) * Math.pow(lambda, x)) / factorialX;
        cumulativeProbability += cells[x];
        x++;
        factorialX *= x;
    // when the cumulativeProbability is nearly 1, we've calculated
    // the useful range of this distribution
    } while (cumulativeProbability < 1 - epsilon);

    return cells;
}

/* @flow */

/**
 * **Percentage Points of the χ2 (Chi-Squared) Distribution**
 *
 * The [χ2 (Chi-Squared) Distribution](http://en.wikipedia.org/wiki/Chi-squared_distribution) is used in the common
 * chi-squared tests for goodness of fit of an observed distribution to a theoretical one, the independence of two
 * criteria of classification of qualitative data, and in confidence interval estimation for a population standard
 * deviation of a normal distribution from a sample standard deviation.
 *
 * Values from Appendix 1, Table III of William W. Hines & Douglas C. Montgomery, "Probability and Statistics in
 * Engineering and Management Science", Wiley (1980).
 */
var chiSquaredDistributionTable = {
    '1': {
        '0.995': 0,
        '0.99': 0,
        '0.975': 0,
        '0.95': 0,
        '0.9': 0.02,
        '0.5': 0.45,
        '0.1': 2.71,
        '0.05': 3.84,
        '0.025': 5.02,
        '0.01': 6.63,
        '0.005': 7.88
    },
    '2': {
        '0.995': 0.01,
        '0.99': 0.02,
        '0.975': 0.05,
        '0.95': 0.1,
        '0.9': 0.21,
        '0.5': 1.39,
        '0.1': 4.61,
        '0.05': 5.99,
        '0.025': 7.38,
        '0.01': 9.21,
        '0.005': 10.6
    },
    '3': {
        '0.995': 0.07,
        '0.99': 0.11,
        '0.975': 0.22,
        '0.95': 0.35,
        '0.9': 0.58,
        '0.5': 2.37,
        '0.1': 6.25,
        '0.05': 7.81,
        '0.025': 9.35,
        '0.01': 11.34,
        '0.005': 12.84
    },
    '4': {
        '0.995': 0.21,
        '0.99': 0.3,
        '0.975': 0.48,
        '0.95': 0.71,
        '0.9': 1.06,
        '0.5': 3.36,
        '0.1': 7.78,
        '0.05': 9.49,
        '0.025': 11.14,
        '0.01': 13.28,
        '0.005': 14.86
    },
    '5': {
        '0.995': 0.41,
        '0.99': 0.55,
        '0.975': 0.83,
        '0.95': 1.15,
        '0.9': 1.61,
        '0.5': 4.35,
        '0.1': 9.24,
        '0.05': 11.07,
        '0.025': 12.83,
        '0.01': 15.09,
        '0.005': 16.75
    },
    '6': {
        '0.995': 0.68,
        '0.99': 0.87,
        '0.975': 1.24,
        '0.95': 1.64,
        '0.9': 2.2,
        '0.5': 5.35,
        '0.1': 10.65,
        '0.05': 12.59,
        '0.025': 14.45,
        '0.01': 16.81,
        '0.005': 18.55
    },
    '7': {
        '0.995': 0.99,
        '0.99': 1.25,
        '0.975': 1.69,
        '0.95': 2.17,
        '0.9': 2.83,
        '0.5': 6.35,
        '0.1': 12.02,
        '0.05': 14.07,
        '0.025': 16.01,
        '0.01': 18.48,
        '0.005': 20.28
    },
    '8': {
        '0.995': 1.34,
        '0.99': 1.65,
        '0.975': 2.18,
        '0.95': 2.73,
        '0.9': 3.49,
        '0.5': 7.34,
        '0.1': 13.36,
        '0.05': 15.51,
        '0.025': 17.53,
        '0.01': 20.09,
        '0.005': 21.96
    },
    '9': {
        '0.995': 1.73,
        '0.99': 2.09,
        '0.975': 2.7,
        '0.95': 3.33,
        '0.9': 4.17,
        '0.5': 8.34,
        '0.1': 14.68,
        '0.05': 16.92,
        '0.025': 19.02,
        '0.01': 21.67,
        '0.005': 23.59
    },
    '10': {
        '0.995': 2.16,
        '0.99': 2.56,
        '0.975': 3.25,
        '0.95': 3.94,
        '0.9': 4.87,
        '0.5': 9.34,
        '0.1': 15.99,
        '0.05': 18.31,
        '0.025': 20.48,
        '0.01': 23.21,
        '0.005': 25.19
    },
    '11': {
        '0.995': 2.6,
        '0.99': 3.05,
        '0.975': 3.82,
        '0.95': 4.57,
        '0.9': 5.58,
        '0.5': 10.34,
        '0.1': 17.28,
        '0.05': 19.68,
        '0.025': 21.92,
        '0.01': 24.72,
        '0.005': 26.76
    },
    '12': {
        '0.995': 3.07,
        '0.99': 3.57,
        '0.975': 4.4,
        '0.95': 5.23,
        '0.9': 6.3,
        '0.5': 11.34,
        '0.1': 18.55,
        '0.05': 21.03,
        '0.025': 23.34,
        '0.01': 26.22,
        '0.005': 28.3
    },
    '13': {
        '0.995': 3.57,
        '0.99': 4.11,
        '0.975': 5.01,
        '0.95': 5.89,
        '0.9': 7.04,
        '0.5': 12.34,
        '0.1': 19.81,
        '0.05': 22.36,
        '0.025': 24.74,
        '0.01': 27.69,
        '0.005': 29.82
    },
    '14': {
        '0.995': 4.07,
        '0.99': 4.66,
        '0.975': 5.63,
        '0.95': 6.57,
        '0.9': 7.79,
        '0.5': 13.34,
        '0.1': 21.06,
        '0.05': 23.68,
        '0.025': 26.12,
        '0.01': 29.14,
        '0.005': 31.32
    },
    '15': {
        '0.995': 4.6,
        '0.99': 5.23,
        '0.975': 6.27,
        '0.95': 7.26,
        '0.9': 8.55,
        '0.5': 14.34,
        '0.1': 22.31,
        '0.05': 25,
        '0.025': 27.49,
        '0.01': 30.58,
        '0.005': 32.8
    },
    '16': {
        '0.995': 5.14,
        '0.99': 5.81,
        '0.975': 6.91,
        '0.95': 7.96,
        '0.9': 9.31,
        '0.5': 15.34,
        '0.1': 23.54,
        '0.05': 26.3,
        '0.025': 28.85,
        '0.01': 32,
        '0.005': 34.27
    },
    '17': {
        '0.995': 5.7,
        '0.99': 6.41,
        '0.975': 7.56,
        '0.95': 8.67,
        '0.9': 10.09,
        '0.5': 16.34,
        '0.1': 24.77,
        '0.05': 27.59,
        '0.025': 30.19,
        '0.01': 33.41,
        '0.005': 35.72
    },
    '18': {
        '0.995': 6.26,
        '0.99': 7.01,
        '0.975': 8.23,
        '0.95': 9.39,
        '0.9': 10.87,
        '0.5': 17.34,
        '0.1': 25.99,
        '0.05': 28.87,
        '0.025': 31.53,
        '0.01': 34.81,
        '0.005': 37.16
    },
    '19': {
        '0.995': 6.84,
        '0.99': 7.63,
        '0.975': 8.91,
        '0.95': 10.12,
        '0.9': 11.65,
        '0.5': 18.34,
        '0.1': 27.2,
        '0.05': 30.14,
        '0.025': 32.85,
        '0.01': 36.19,
        '0.005': 38.58
    },
    '20': {
        '0.995': 7.43,
        '0.99': 8.26,
        '0.975': 9.59,
        '0.95': 10.85,
        '0.9': 12.44,
        '0.5': 19.34,
        '0.1': 28.41,
        '0.05': 31.41,
        '0.025': 34.17,
        '0.01': 37.57,
        '0.005': 40
    },
    '21': {
        '0.995': 8.03,
        '0.99': 8.9,
        '0.975': 10.28,
        '0.95': 11.59,
        '0.9': 13.24,
        '0.5': 20.34,
        '0.1': 29.62,
        '0.05': 32.67,
        '0.025': 35.48,
        '0.01': 38.93,
        '0.005': 41.4
    },
    '22': {
        '0.995': 8.64,
        '0.99': 9.54,
        '0.975': 10.98,
        '0.95': 12.34,
        '0.9': 14.04,
        '0.5': 21.34,
        '0.1': 30.81,
        '0.05': 33.92,
        '0.025': 36.78,
        '0.01': 40.29,
        '0.005': 42.8
    },
    '23': {
        '0.995': 9.26,
        '0.99': 10.2,
        '0.975': 11.69,
        '0.95': 13.09,
        '0.9': 14.85,
        '0.5': 22.34,
        '0.1': 32.01,
        '0.05': 35.17,
        '0.025': 38.08,
        '0.01': 41.64,
        '0.005': 44.18
    },
    '24': {
        '0.995': 9.89,
        '0.99': 10.86,
        '0.975': 12.4,
        '0.95': 13.85,
        '0.9': 15.66,
        '0.5': 23.34,
        '0.1': 33.2,
        '0.05': 36.42,
        '0.025': 39.36,
        '0.01': 42.98,
        '0.005': 45.56
    },
    '25': {
        '0.995': 10.52,
        '0.99': 11.52,
        '0.975': 13.12,
        '0.95': 14.61,
        '0.9': 16.47,
        '0.5': 24.34,
        '0.1': 34.28,
        '0.05': 37.65,
        '0.025': 40.65,
        '0.01': 44.31,
        '0.005': 46.93
    },
    '26': {
        '0.995': 11.16,
        '0.99': 12.2,
        '0.975': 13.84,
        '0.95': 15.38,
        '0.9': 17.29,
        '0.5': 25.34,
        '0.1': 35.56,
        '0.05': 38.89,
        '0.025': 41.92,
        '0.01': 45.64,
        '0.005': 48.29
    },
    '27': {
        '0.995': 11.81,
        '0.99': 12.88,
        '0.975': 14.57,
        '0.95': 16.15,
        '0.9': 18.11,
        '0.5': 26.34,
        '0.1': 36.74,
        '0.05': 40.11,
        '0.025': 43.19,
        '0.01': 46.96,
        '0.005': 49.65
    },
    '28': {
        '0.995': 12.46,
        '0.99': 13.57,
        '0.975': 15.31,
        '0.95': 16.93,
        '0.9': 18.94,
        '0.5': 27.34,
        '0.1': 37.92,
        '0.05': 41.34,
        '0.025': 44.46,
        '0.01': 48.28,
        '0.005': 50.99
    },
    '29': {
        '0.995': 13.12,
        '0.99': 14.26,
        '0.975': 16.05,
        '0.95': 17.71,
        '0.9': 19.77,
        '0.5': 28.34,
        '0.1': 39.09,
        '0.05': 42.56,
        '0.025': 45.72,
        '0.01': 49.59,
        '0.005': 52.34
    },
    '30': {
        '0.995': 13.79,
        '0.99': 14.95,
        '0.975': 16.79,
        '0.95': 18.49,
        '0.9': 20.6,
        '0.5': 29.34,
        '0.1': 40.26,
        '0.05': 43.77,
        '0.025': 46.98,
        '0.01': 50.89,
        '0.005': 53.67
    },
    '40': {
        '0.995': 20.71,
        '0.99': 22.16,
        '0.975': 24.43,
        '0.95': 26.51,
        '0.9': 29.05,
        '0.5': 39.34,
        '0.1': 51.81,
        '0.05': 55.76,
        '0.025': 59.34,
        '0.01': 63.69,
        '0.005': 66.77
    },
    '50': {
        '0.995': 27.99,
        '0.99': 29.71,
        '0.975': 32.36,
        '0.95': 34.76,
        '0.9': 37.69,
        '0.5': 49.33,
        '0.1': 63.17,
        '0.05': 67.5,
        '0.025': 71.42,
        '0.01': 76.15,
        '0.005': 79.49
    },
    '60': {
        '0.995': 35.53,
        '0.99': 37.48,
        '0.975': 40.48,
        '0.95': 43.19,
        '0.9': 46.46,
        '0.5': 59.33,
        '0.1': 74.4,
        '0.05': 79.08,
        '0.025': 83.3,
        '0.01': 88.38,
        '0.005': 91.95
    },
    '70': {
        '0.995': 43.28,
        '0.99': 45.44,
        '0.975': 48.76,
        '0.95': 51.74,
        '0.9': 55.33,
        '0.5': 69.33,
        '0.1': 85.53,
        '0.05': 90.53,
        '0.025': 95.02,
        '0.01': 100.42,
        '0.005': 104.22
    },
    '80': {
        '0.995': 51.17,
        '0.99': 53.54,
        '0.975': 57.15,
        '0.95': 60.39,
        '0.9': 64.28,
        '0.5': 79.33,
        '0.1': 96.58,
        '0.05': 101.88,
        '0.025': 106.63,
        '0.01': 112.33,
        '0.005': 116.32
    },
    '90': {
        '0.995': 59.2,
        '0.99': 61.75,
        '0.975': 65.65,
        '0.95': 69.13,
        '0.9': 73.29,
        '0.5': 89.33,
        '0.1': 107.57,
        '0.05': 113.14,
        '0.025': 118.14,
        '0.01': 124.12,
        '0.005': 128.3
    },
    '100': {
        '0.995': 67.33,
        '0.99': 70.06,
        '0.975': 74.22,
        '0.95': 77.93,
        '0.9': 82.36,
        '0.5': 99.33,
        '0.1': 118.5,
        '0.05': 124.34,
        '0.025': 129.56,
        '0.01': 135.81,
        '0.005': 140.17
    }
};

/* @flow */

/**
 * The [χ2 (Chi-Squared) Goodness-of-Fit Test](http://en.wikipedia.org/wiki/Goodness_of_fit#Pearson.27s_chi-squared_test)
 * uses a measure of goodness of fit which is the sum of differences between observed and expected outcome frequencies
 * (that is, counts of observations), each squared and divided by the number of observations expected given the
 * hypothesized distribution. The resulting χ2 statistic, `chiSquared`, can be compared to the chi-squared distribution
 * to determine the goodness of fit. In order to determine the degrees of freedom of the chi-squared distribution, one
 * takes the total number of observed frequencies and subtracts the number of estimated parameters. The test statistic
 * follows, approximately, a chi-square distribution with (k − c) degrees of freedom where `k` is the number of non-empty
 * cells and `c` is the number of estimated parameters for the distribution.
 *
 * @param {Array<number>} data
 * @param {Function} distributionType a function that returns a point in a distribution:
 * for instance, binomial, bernoulli, or poisson
 * @param {number} significance
 * @returns {number} chi squared goodness of fit
 * @example
 * // Data from Poisson goodness-of-fit example 10-19 in William W. Hines & Douglas C. Montgomery,
 * // "Probability and Statistics in Engineering and Management Science", Wiley (1980).
 * var data1019 = [
 *     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
 *     0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
 *     1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
 *     2, 2, 2, 2, 2, 2, 2, 2, 2,
 *     3, 3, 3, 3
 * ];
 * ss.chiSquaredGoodnessOfFit(data1019, ss.poissonDistribution, 0.05); //= false
 */
function chiSquaredGoodnessOfFit(
    data/*: Array<number> */,
    distributionType/*: Function */,
    significance/*: number */)/*: boolean */ {
    // Estimate from the sample data, a weighted mean.
    var inputMean = mean(data),
        // Calculated value of the χ2 statistic.
        chiSquared = 0,
        // Degrees of freedom, calculated as (number of class intervals -
        // number of hypothesized distribution parameters estimated - 1)
        degreesOfFreedom,
        // Number of hypothesized distribution parameters estimated, expected to be supplied in the distribution test.
        // Lose one degree of freedom for estimating `lambda` from the sample data.
        c = 1,
        // The hypothesized distribution.
        // Generate the hypothesized distribution.
        hypothesizedDistribution = distributionType(inputMean),
        observedFrequencies = [],
        expectedFrequencies = [],
        k;

    // Create an array holding a histogram from the sample data, of
    // the form `{ value: numberOfOcurrences }`
    for (var i = 0; i < data.length; i++) {
        if (observedFrequencies[data[i]] === undefined) {
            observedFrequencies[data[i]] = 0;
        }
        observedFrequencies[data[i]]++;
    }

    // The histogram we created might be sparse - there might be gaps
    // between values. So we iterate through the histogram, making
    // sure that instead of undefined, gaps have 0 values.
    for (i = 0; i < observedFrequencies.length; i++) {
        if (observedFrequencies[i] === undefined) {
            observedFrequencies[i] = 0;
        }
    }

    // Create an array holding a histogram of expected data given the
    // sample size and hypothesized distribution.
    for (k in hypothesizedDistribution) {
        if (k in observedFrequencies) {
            expectedFrequencies[+k] = hypothesizedDistribution[k] * data.length;
        }
    }

    // Working backward through the expected frequencies, collapse classes
    // if less than three observations are expected for a class.
    // This transformation is applied to the observed frequencies as well.
    for (k = expectedFrequencies.length - 1; k >= 0; k--) {
        if (expectedFrequencies[k] < 3) {
            expectedFrequencies[k - 1] += expectedFrequencies[k];
            expectedFrequencies.pop();

            observedFrequencies[k - 1] += observedFrequencies[k];
            observedFrequencies.pop();
        }
    }

    // Iterate through the squared differences between observed & expected
    // frequencies, accumulating the `chiSquared` statistic.
    for (k = 0; k < observedFrequencies.length; k++) {
        chiSquared += Math.pow(
            observedFrequencies[k] - expectedFrequencies[k], 2) /
            expectedFrequencies[k];
    }

    // Calculate degrees of freedom for this test and look it up in the
    // `chiSquaredDistributionTable` in order to
    // accept or reject the goodness-of-fit of the hypothesized distribution.
    degreesOfFreedom = observedFrequencies.length - c - 1;
    return chiSquaredDistributionTable[degreesOfFreedom][significance] < chiSquared;
}

/* @flow */

var SQRT_2PI = Math.sqrt(2 * Math.PI);

/**
 * [Well-known kernels](https://en.wikipedia.org/wiki/Kernel_(statistics)#Kernel_functions_in_common_use)
 * @private
 */
var kernels /*: {[string]: (number) => number} */ = {
    /**
     * The gaussian kernel.
     * @private
     */
    gaussian: function (u) {
        return Math.exp(-0.5 * u * u) / SQRT_2PI;
    }
};

/**
 * Well known bandwidth selection methods
 * @private
 */
var bandwidthMethods /*: {[string]: (Array<number>) => number} */ = {
    /**
     * The ["normal reference distribution"
     * rule-of-thumb](https://stat.ethz.ch/R-manual/R-devel/library/MASS/html/bandwidth.nrd.html),
     * a commonly used version of [Silverman's
     * rule-of-thumb](https://en.wikipedia.org/wiki/Kernel_density_estimation#A_rule-of-thumb_bandwidth_estimator).
     * @private
     */
    nrd: function (x /*: Array<number> */) {
        var s = sampleStandardDeviation(x);
        var iqr = interquartileRange(x);
        if (typeof iqr === 'number') {
            s = Math.min(s, iqr / 1.34);
        }
        return 1.06 * s * Math.pow(x.length, -0.2);
    }
};

/**
 * [Kernel density estimation](https://en.wikipedia.org/wiki/Kernel_density_estimation)
 * is a useful tool for, among other things, estimating the shape of the
 * underlying probability distribution from a sample.
 *
 * @name kernelDensityEstimation
 * @param X sample values
 * @param kernel The kernel function to use. If a function is provided, it should return non-negative values and integrate to 1. Defaults to 'gaussian'.
 * @param bandwidthMethod The "bandwidth selection" method to use, or a fixed bandwidth value. Defaults to "nrd", the commonly-used ["normal reference distribution" rule-of-thumb](https://stat.ethz.ch/R-manual/R-devel/library/MASS/html/bandwidth.nrd.html).
 * @returns {Function} An estimated [probability density function](https://en.wikipedia.org/wiki/Probability_density_function) for the given sample. The returned function runs in `O(X.length)`.
 */
function kernelDensityEstimation(
    X /*: Array<number> */,
    kernel /*: $Keys<typeof kernels> | ((number) => number) | void*/,
    bandwidthMethod /*: $Keys<typeof bandwidthMethods> | number | void*/
) {
    var kernelFn/*: (number) => number */;
    if (kernel === undefined) {
        kernelFn = kernels.gaussian;
    } else if (typeof kernel === 'string') {
        if (!kernels[kernel]) {
            throw new Error('Unknown kernel "' + kernel + '"');
        }
        kernelFn = kernels[kernel];
    } else {
        kernelFn = kernel;
    }

    var bandwidth;
    if (typeof bandwidthMethod === 'undefined') {
        bandwidth = bandwidthMethods.nrd(X);
    } else if (typeof bandwidthMethod === 'string') {
        if (!bandwidthMethods[bandwidthMethod]) {
            throw new Error('Unknown bandwidth method "' + bandwidthMethod + '"');
        }
        bandwidth = bandwidthMethods[bandwidthMethod](X);
    } else {
        bandwidth = bandwidthMethod;
    }

    return function (x /*: number*/) {
        var i = 0;
        var sum = 0;
        for (i = 0; i < X.length; i++) {
            sum += kernelFn((x - X[i]) / bandwidth);
        }
        return sum / bandwidth / X.length;
    }
}

/* @flow */

/**
 * The [Z-Score, or Standard Score](http://en.wikipedia.org/wiki/Standard_score).
 *
 * The standard score is the number of standard deviations an observation
 * or datum is above or below the mean. Thus, a positive standard score
 * represents a datum above the mean, while a negative standard score
 * represents a datum below the mean. It is a dimensionless quantity
 * obtained by subtracting the population mean from an individual raw
 * score and then dividing the difference by the population standard
 * deviation.
 *
 * The z-score is only defined if one knows the population parameters;
 * if one only has a sample set, then the analogous computation with
 * sample mean and sample standard deviation yields the
 * Student's t-statistic.
 *
 * @param {number} x
 * @param {number} mean
 * @param {number} standardDeviation
 * @return {number} z score
 * @example
 * zScore(78, 80, 5); // => -0.4
 */
function zScore(x/*:number*/, mean/*:number*/, standardDeviation/*:number*/)/*:number*/ {
    return (x - mean) / standardDeviation;
}

/* @flow */

var SQRT_2PI$1 = Math.sqrt(2 * Math.PI);

function cumulativeDistribution(z) {
    var sum = z,
        tmp = z;

    // 15 iterations are enough for 4-digit precision
    for (var i = 1; i < 15; i++) {
        tmp *= z * z / (2 * i + 1);
        sum += tmp;
    }
    return Math.round((0.5 + (sum / SQRT_2PI$1) * Math.exp(-z * z / 2)) * 1e4) / 1e4;
}

/**
 * A standard normal table, also called the unit normal table or Z table,
 * is a mathematical table for the values of Φ (phi), which are the values of
 * the cumulative distribution function of the normal distribution.
 * It is used to find the probability that a statistic is observed below,
 * above, or between values on the standard normal distribution, and by
 * extension, any normal distribution.
 *
 * The probabilities are calculated using the
 * [Cumulative distribution function](https://en.wikipedia.org/wiki/Normal_distribution#Cumulative_distribution_function).
 * The table used is the cumulative, and not cumulative from 0 to mean
 * (even though the latter has 5 digits precision, instead of 4).
 */
var standardNormalTable/*: Array<number> */ = [];

for (var z = 0; z <= 3.09; z += 0.01) {
    standardNormalTable.push(cumulativeDistribution(z));
}

/* @flow */

/**
 * **[Cumulative Standard Normal Probability](http://en.wikipedia.org/wiki/Standard_normal_table)**
 *
 * Since probability tables cannot be
 * printed for every normal distribution, as there are an infinite variety
 * of normal distributions, it is common practice to convert a normal to a
 * standard normal and then use the standard normal table to find probabilities.
 *
 * You can use `.5 + .5 * errorFunction(x / Math.sqrt(2))` to calculate the probability
 * instead of looking it up in a table.
 *
 * @param {number} z
 * @returns {number} cumulative standard normal probability
 */
function cumulativeStdNormalProbability(z /*:number */)/*:number */ {

    // Calculate the position of this value.
    var absZ = Math.abs(z),
        // Each row begins with a different
        // significant digit: 0.5, 0.6, 0.7, and so on. Each value in the table
        // corresponds to a range of 0.01 in the input values, so the value is
        // multiplied by 100.
        index = Math.min(Math.round(absZ * 100), standardNormalTable.length - 1);

    // The index we calculate must be in the table as a positive value,
    // but we still pay attention to whether the input is positive
    // or negative, and flip the output value as a last step.
    if (z >= 0) {
        return standardNormalTable[index];
    } else {
        // due to floating-point arithmetic, values in the table with
        // 4 significant figures can nevertheless end up as repeating
        // fractions when they're computed here.
        return +(1 - standardNormalTable[index]).toFixed(4);
    }
}

/* @flow */

/**
 * **[Gaussian error function](http://en.wikipedia.org/wiki/Error_function)**
 *
 * The `errorFunction(x/(sd * Math.sqrt(2)))` is the probability that a value in a
 * normal distribution with standard deviation sd is within x of the mean.
 *
 * This function returns a numerical approximation to the exact value.
 *
 * @param {number} x input
 * @return {number} error estimation
 * @example
 * errorFunction(1).toFixed(2); // => '0.84'
 */
function errorFunction(x/*: number */)/*: number */ {
    var t = 1 / (1 + 0.5 * Math.abs(x));
    var tau = t * Math.exp(-Math.pow(x, 2) -
        1.26551223 +
        1.00002368 * t +
        0.37409196 * Math.pow(t, 2) +
        0.09678418 * Math.pow(t, 3) -
        0.18628806 * Math.pow(t, 4) +
        0.27886807 * Math.pow(t, 5) -
        1.13520398 * Math.pow(t, 6) +
        1.48851587 * Math.pow(t, 7) -
        0.82215223 * Math.pow(t, 8) +
        0.17087277 * Math.pow(t, 9));
    if (x >= 0) {
        return 1 - tau;
    } else {
        return tau - 1;
    }
}

/* @flow */

/**
 * The Inverse [Gaussian error function](http://en.wikipedia.org/wiki/Error_function)
 * returns a numerical approximation to the value that would have caused
 * `errorFunction()` to return x.
 *
 * @param {number} x value of error function
 * @returns {number} estimated inverted value
 */
function inverseErrorFunction(x/*: number */)/*: number */ {
    var a = (8 * (Math.PI - 3)) / (3 * Math.PI * (4 - Math.PI));

    var inv = Math.sqrt(Math.sqrt(
        Math.pow(2 / (Math.PI * a) + Math.log(1 - x * x) / 2, 2) -
        Math.log(1 - x * x) / a) -
        (2 / (Math.PI * a) + Math.log(1 - x * x) / 2));

    if (x >= 0) {
        return inv;
    } else {
        return -inv;
    }
}

/* @flow */

/**
 * The [Probit](http://en.wikipedia.org/wiki/Probit)
 * is the inverse of cumulativeStdNormalProbability(),
 * and is also known as the normal quantile function.
 *
 * It returns the number of standard deviations from the mean
 * where the p'th quantile of values can be found in a normal distribution.
 * So, for example, probit(0.5 + 0.6827/2) ≈ 1 because 68.27% of values are
 * normally found within 1 standard deviation above or below the mean.
 *
 * @param {number} p
 * @returns {number} probit
 */
function probit(p /*: number */)/*: number */ {
    if (p === 0) {
        p = epsilon;
    } else if (p >= 1) {
        p = 1 - epsilon;
    }
    return Math.sqrt(2) * inverseErrorFunction(2 * p - 1);
}

/* @flow */

/**
 * Conducts a [permutation test](https://en.wikipedia.org/wiki/Resampling_(statistics)#Permutation_tests)
 * to determine if two data sets are *significantly* different from each other, using
 * the difference of means between the groups as the test statistic. 
 * The function allows for the following hypotheses:
 * - two_tail = Null hypothesis: the two distributions are equal.
 * - greater = Null hypothesis: observations from sampleX tend to be smaller than those from sampleY.
 * - less = Null hypothesis: observations from sampleX tend to be greater than those from sampleY.
 * [Learn more about one-tail vs two-tail tests.](https://en.wikipedia.org/wiki/One-_and_two-tailed_tests)
 *
 * @param {Array<number>} sampleX first dataset (e.g. treatment data)
 * @param {Array<number>} sampleY second dataset (e.g. control data)
 * @param {string} alternative alternative hypothesis, either 'two_sided' (default), 'greater', or 'less'
 * @param {number} k number of values in permutation distribution. 
 * @returns {number} p-value The probability of observing the difference between groups (as or more extreme than what we did), assuming the null hypothesis.
 *
 * @example
 * var control = [2, 5, 3, 6, 7, 2, 5];
 * var treatment = [20, 5, 13, 12, 7, 2, 2];
 * permutationTest(control, treatment); // ~0.1324 
 */
function permutationTest(
    sampleX/*: Array<number> */,
    sampleY/*: Array<number> */,
    alternative/*: string */,
    k/*: number */)/*: ?number */ {
    // Set default arguments
    if (k === undefined) {
        k = 10000;
    }
    if (alternative === undefined) {
        alternative = 'two_side';
    }
    if (alternative !== 'two_side' && alternative !== 'greater' && alternative !== 'less') {
        throw new Error('`alternative` must be either \'two_side\', \'greater\', or \'less\'');
    }

    // init pValue
    var pValue;

    // get means for each sample
    var meanX = mean(sampleX);
    var meanY = mean(sampleY);

    // calculate initial test statistic. This will be our point of comparison with
    // the generated test statistics.
    var testStatistic = meanX - meanY;

    // create test-statistic distribution
    var testStatDsn = new Array(k);
    
    // combine datsets so we can easily shuffle later
    var allData = sampleX.concat(sampleY);
    var midIndex = Math.floor(allData.length / 2);
    
    for (var i = 0; i < k; i++) {
        
        // 1. shuffle data assignments
        shuffleInPlace(allData);
        var permLeft = allData.slice(0, midIndex);
        var permRight = allData.slice(midIndex, allData.length);

        // 2.re-calculate test statistic
        var permTestStatistic = mean(permLeft) - mean(permRight);

        // 3. store test statistic to build test statistic distribution
        testStatDsn[i] = permTestStatistic;
    }

    // Calculate p-value depending on alternative
    // For this test, we calculate the percentage of 'extreme' test statistics (subject to our hypothesis)
    // more info on permutation test p-value calculations: https://onlinecourses.science.psu.edu/stat464/node/35
    var numExtremeTStats = 0;
    if (alternative === 'two_side') {
        for (i = 0; i <= k; i++) {
            if (Math.abs(testStatDsn[i]) >= Math.abs(testStatistic)) {
                numExtremeTStats += 1;
            }
        }
    } else if (alternative === 'greater') {
        for (i = 0; i <= k; i++) {
            if (testStatDsn[i] >= testStatistic) {
                numExtremeTStats += 1;
            }
        }
    } else { // alternative === 'less'
        for (i = 0; i <= k; i++) {
            if (testStatDsn[i] <= testStatistic) {
                numExtremeTStats += 1;
            }
        }
    }

    pValue = numExtremeTStats / k;
            
    return pValue;
        
}

/* @flow */

/**
 * [Sign](https://en.wikipedia.org/wiki/Sign_function) is a function
 * that extracts the sign of a real number
 *
 * @param {number} x input value
 * @returns {number} sign value either 1, 0 or -1
 * @throws {TypeError} if the input argument x is not a number
 * @private
 *
 * @example
 * sign(2); // => 1
 */
function sign(x/*: number */)/*: number */ {
    if (typeof x === 'number') {
        if (x < 0) {
            return -1;
        } else if (x === 0) {
            return 0
        } else {
            return 1;
        }
    } else {
        throw new TypeError('not a number');
    }
}

/* @flow */

/**
 * [Bisection method](https://en.wikipedia.org/wiki/Bisection_method) is a root-finding
 * method that repeatedly bisects an interval to find the root.
 *
 * This function returns a numerical approximation to the exact value.
 *
 * @param {Function} func input function
 * @param {number} start - start of interval
 * @param {number} end - end of interval
 * @param {number} maxIterations - the maximum number of iterations
 * @param {number} errorTolerance - the error tolerance
 * @returns {number} estimated root value
 * @throws {TypeError} Argument func must be a function
 *
 * @example
 * bisect(Math.cos,0,4,100,0.003); // => 1.572265625
 */
function bisect(
    func/*: (x: any) => number */,
    start/*: number */,
    end/*: number */,
    maxIterations/*: number */,
    errorTolerance/*: number */)/*:number*/ {

    if (typeof func !== 'function') throw new TypeError('func must be a function');

    for (var i = 0; i < maxIterations; i++) {
        var output = (start + end) / 2;

        if (func(output) === 0 || Math.abs((end - start) / 2) < errorTolerance) {
            return output;
        }

        if (sign(func(output)) === sign(func(start))) {
            start = output;
        } else {
            end = output;
        }
    }

    throw new Error('maximum number of iterations exceeded');
}

/* @flow */

exports.linearRegression = linearRegression;
exports.linearRegressionLine = linearRegressionLine;
exports.standardDeviation = standardDeviation;
exports.rSquared = rSquared;
exports.mode = mode;
exports.modeFast = modeFast;
exports.modeSorted = modeSorted;
exports.min = min;
exports.max = max;
exports.extent = extent;
exports.minSorted = minSorted;
exports.maxSorted = maxSorted;
exports.extentSorted = extentSorted;
exports.sum = sum;
exports.sumSimple = sumSimple;
exports.product = product;
exports.quantile = quantile;
exports.quantileSorted = quantileSorted;
exports.quantileRank = quantileRank;
exports.quantileRankSorted = quantileRankSorted;
exports.interquartileRange = interquartileRange;
exports.iqr = interquartileRange;
exports.medianAbsoluteDeviation = medianAbsoluteDeviation;
exports.mad = medianAbsoluteDeviation;
exports.chunk = chunk;
exports.sampleWithReplacement = sampleWithReplacement;
exports.shuffle = shuffle;
exports.shuffleInPlace = shuffleInPlace;
exports.sample = sample;
exports.ckmeans = ckmeans;
exports.uniqueCountSorted = uniqueCountSorted;
exports.sumNthPowerDeviations = sumNthPowerDeviations;
exports.equalIntervalBreaks = equalIntervalBreaks;
exports.sampleCovariance = sampleCovariance;
exports.sampleCorrelation = sampleCorrelation;
exports.sampleVariance = sampleVariance;
exports.sampleStandardDeviation = sampleStandardDeviation;
exports.sampleSkewness = sampleSkewness;
exports.sampleKurtosis = sampleKurtosis;
exports.permutationsHeap = permutationsHeap;
exports.combinations = combinations;
exports.combinationsReplacement = combinationsReplacement;
exports.addToMean = addToMean;
exports.combineMeans = combineMeans;
exports.combineVariances = combineVariances;
exports.geometricMean = geometricMean;
exports.harmonicMean = harmonicMean;
exports.average = mean;
exports.mean = mean;
exports.median = median;
exports.medianSorted = medianSorted;
exports.subtractFromMean = subtractFromMean;
exports.rootMeanSquare = rootMeanSquare;
exports.rms = rootMeanSquare;
exports.variance = variance;
exports.tTest = tTest;
exports.tTestTwoSample = tTestTwoSample;
exports.BayesianClassifier = BayesianClassifier;
exports.bayesian = BayesianClassifier;
exports.PerceptronModel = PerceptronModel;
exports.perceptron = PerceptronModel;
exports.epsilon = epsilon;
exports.factorial = factorial;
exports.gamma = gamma;
exports.bernoulliDistribution = bernoulliDistribution;
exports.binomialDistribution = binomialDistribution;
exports.poissonDistribution = poissonDistribution;
exports.chiSquaredDistributionTable = chiSquaredDistributionTable;
exports.chiSquaredGoodnessOfFit = chiSquaredGoodnessOfFit;
exports.kernelDensityEstimation = kernelDensityEstimation;
exports.kde = kernelDensityEstimation;
exports.zScore = zScore;
exports.cumulativeStdNormalProbability = cumulativeStdNormalProbability;
exports.standardNormalTable = standardNormalTable;
exports.errorFunction = errorFunction;
exports.erf = errorFunction;
exports.inverseErrorFunction = inverseErrorFunction;
exports.probit = probit;
exports.permutationTest = permutationTest;
exports.bisect = bisect;
exports.quickselect = quickselect;
exports.sign = sign;
exports.numericSort = numericSort;
//# sourceMappingURL=simple-statistics.js.map