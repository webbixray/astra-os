import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
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

export default nextConfig;
