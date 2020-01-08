module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFiles: [
    '<rootDir>/jest-pre.ts',
  ],
  moduleNameMapper: {
    '\\.css$': 'identity-obj-proxy',
  },
  reporters: [
    'default',
    'jest-simple-summary'
  ],
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.test.ts',
  ],
};
