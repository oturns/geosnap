PyExtJS
=======
<sup>(Python Extension Packages in Javascript)</sup>  

### Contents  

- <a href="#what-is-pyextjs">What is PyExtJs?</a>
- <a href="#installation">Installation</a>
- <a href="#sourcecode">Latest source code</a>
- <a href="#bugs">Bug reports</a>
- <a href="https://github.com/fernandezajp/PyExtJS/wiki">Wiki</a>
	* <a href="https://github.com/fernandezajp/PyExtJS/wiki/Array-creation-routines">Array creation routines</a>
	* <a href="https://github.com/fernandezajp/PyExtJS/wiki/Array-manipulation-routines">Array manipulation routines</a>
	* <a href="https://github.com/fernandezajp/PyExtJS/wiki/Mathematical-functions">Mathematical functions</a>
- <a href="#performance">Performance</a>

## <a id="what-is-pyextjs">What is PyExtJs?</a>

Python Extension Packages in Javascript is open-source implementation of some common libraries used
in the scientific python programming.  
The main goal of this project is to improve migration of
python language to javascript.

## License

Copyright 2016 Alvaro Fernandez  

License: MIT/X11  

## <a id="installation">Installation</a>

### on node.js  

		$ npm install pyextjs  
<br>

		> require('pyextjs');

		> numpy.linspace(2.0,3.0,5);
<br>

### on the browser  

Just include the following libraries in your html.

    <!doctype html>
    <html>
      <head>
        <script type="text/javascript" src="../js/ss.js"></script>
        <script type="text/javascript" src="../js/Numpy.js"></script>
        <script type="text/javascript" src="../js/PolySolve.js"></script>
        <script type="text/javascript" src="../js/Scipy.js"></script>
        <script type="text/javascript">

           // Use Numpy & Scipy like python in javascript

           function ready() {
               var ls = numpy.linspace(2.0,3.0,5);
           }

        </script>
      </head>
    </html>

## <a id="sourcecode">Latest source code</a>  

<br>
The latest development version of Scipy's sources are always available at:

> [https://github.com/fernandezajp/PyExtJs](https://github.com/fernandezajp/PyExtJs)

## <a id="bugs">Bug reports</a>  
<br>
To search for bugs or report them, please use the Scipy Bug Tracker at:

> [https://github.com/fernandezajp/PyExtJs/issues](https://github.com/fernandezajp/PyExtJs/issues)

##<a href="#performance">Performance</a>

This is very important, the test was executed in a MacBookPro i5

The python Code:

    import time
    import numpy

    def test():
        x = numpy.array([0.0, 1.0, 2.0, 3.0,  4.0,  5.0])
        y = numpy.array([0.0, 0.8, 0.9, 0.1, -0.8, -1.0])

        start = time.time()
        for num in range(1,10000):
            numpy.polyfit(x, y, 3)
        end = time.time()

        microsecs = end - start
        print microsecs * 1000

    test()

<br>
The Javascript Code:

    function test() {
        x = [0.0, 1.0, 2.0, 3.0,  4.0,  5.0];
        y = [0.0, 0.8, 0.9, 0.1, -0.8, -1.0];

        var start = +new Date();
        for (var i=0;i<10000;i++)
            numpy.polyfit(x, y, 3)
        var end =  +new Date();
        var diff = end - start;
        alert(diff);
    }

    test();

<br>

Python: 1604 milliseconds  
Javascript: 14 milliseconds

Javascript! Very fast!!!
