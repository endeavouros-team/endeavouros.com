// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://endeavouros.com',
  integrations: [sitemap()],
  image: {
    // Responsive by default rather than per-image opt-in. This is what makes
    // the eventual 936 migrated media files tractable.
    layout: 'constrained',
    responsiveStyles: true,
  },
  build: {
    // Astro's default inlines small stylesheets, which forces 'unsafe-inline'
    // in style-src and hollows out the CSP. One extra request is the right
    // trade on a site whose whole premise is "we got injected".
    inlineStylesheets: 'never',
  },
  devToolbar: { enabled: false },
  // The shared data directory lives above this project root.
  vite: { server: { fs: { allow: ['..'] } } },
});
