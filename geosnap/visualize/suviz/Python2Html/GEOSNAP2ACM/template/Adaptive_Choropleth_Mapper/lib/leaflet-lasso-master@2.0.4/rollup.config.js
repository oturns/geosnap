import pkg from './package.json';
import commonjs from 'rollup-plugin-commonjs';
import resolve from 'rollup-plugin-node-resolve';
import typescript from 'rollup-plugin-typescript2';
import postcss from 'rollup-plugin-postcss';
import visualizer from 'rollup-plugin-visualizer';
import { terser } from 'rollup-plugin-terser';
import autoprefixer from 'autoprefixer';
import assets from 'postcss-assets';

const bundle = (format, filename, options = {}) => ({
  input: 'src/index.ts',
  output: {
    file: filename,
    format: format,
    name: 'LeafletLasso',
    sourcemap: true,
    globals: {
      leaflet: 'L',
    },
  },
  external: [
    ...Object.keys(pkg.peerDependencies),
    ...(!options.resolve ? Object.keys(pkg.dependencies) : []),
  ],
  plugins: [
    ...(options.resolve ? [resolve()] : []),
    commonjs(),
    typescript({
      typescript: require('typescript'),
      clean: options.stats,
    }),
    postcss({ plugins: [autoprefixer(), assets()] }),
    ...(options.minimize ? [terser()] : []),
    ...(options.stats ? [visualizer({
      filename: filename + '.stats.html',
    })] : []),
  ],
});

export default [
  bundle('cjs', pkg.main),
  bundle('es', pkg.module),
  bundle('umd', pkg.browser.replace('.min', ''), { resolve: true, stats: true }),
  bundle('umd', pkg.browser, { resolve: true, minimize: true }),
];
