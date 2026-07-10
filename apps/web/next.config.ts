import type { NextConfig } from 'next';

let nextConfig: NextConfig = {
  output: 'standalone',
  transpilePackages: ['@astra/shared', '@astra/ui'],
  experimental: {
    optimizePackageImports: ['lucide-react'],
  },
};

if (process.env.ANALYZE === 'true') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const withBundleAnalyzer = require('@next/bundle-analyzer')({ enabled: true });
  nextConfig = withBundleAnalyzer(nextConfig);
}

export default nextConfig;
