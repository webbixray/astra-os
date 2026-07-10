module.exports = {
  extends: ['./base'],
  rules: {
    'no-restricted-imports': [
      'error',
      {
        patterns: [
          {
            group: ['apps/*'],
            message: 'Libraries should not import from apps',
          },
        ],
      },
    ],
  },
};
