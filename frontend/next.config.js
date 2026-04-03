/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['lucide-react'],
  output: 'standalone',
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;