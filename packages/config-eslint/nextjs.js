module.exports = {
  extends: [
    './base',
    'next/core-web-vitals',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  plugins: ['react'],
  rules: {
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    '@next/next/no-img-element': 'warn',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
