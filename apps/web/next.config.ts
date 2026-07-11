import type { NextConfig } from 'next';

let nextConfig: NextConfig = {
  output: 'standalone',
  transpilePackages: ['@astra/shared', '@astra/ui'],
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
  webpack(config) {
    config.optimization.splitChunks = {
      ...config.optimization.splitChunks,
      cacheGroups: {
        ...config.optimization.splitChunks?.cacheGroups,
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
          priority: 20,
        },
        common: {
          minChunks: 2,
          priority: 10,
          reuseExistingChunk: true,
        },
      },
    };
    return config;
  },
};

if (process.env.ANALYZE === 'true') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const withBundleAnalyzer = require('@next/bundle-analyzer')({ enabled: true });
  nextConfig = withBundleAnalyzer(nextConfig);
}

export default nextConfig;
