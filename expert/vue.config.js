const { defineConfig } = require('@vue/cli-service');

module.exports = defineConfig({
  configureWebpack: process.env.SAAN_WATCH_POLL === 'true'
    ? { watchOptions: { poll: 1000, ignored: /node_modules/ } }
    : {},
  pwa: {
    name: 'سان اپ',
    themeColor: '#164A68',
    msTileColor: '#164A68',
    manifestOptions: {
      name: 'سان اپ | خدمات آسانسور',
      short_name: 'سان اپ',
      lang: 'fa',
      dir: 'rtl',
      display: 'standalone',
      background_color: '#F5F9FB',
      theme_color: '#164A68',
      icons: [
        { src: './img/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
        { src: './img/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
      ],
    },
    iconPaths: {
      favicon16: './img/icons/favicon16.png',
      favicon32: './img/icons/favicon32.png',
      appleTouchIcon: './img/icons/icon-192x192.png',
      maskIcon: null,
      msTileImage: null,
    },
    workboxPluginMode: 'GenerateSW',
  },
});
