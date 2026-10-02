module.exports = {
	devServer: {
		historyApiFallback: true,
		...(process.env.SAAN_WATCH_POLL === 'true'
			? { watchOptions: { poll: 1000, ignored: /node_modules/ }, public: 'http://localhost:18120', sockPort: 18120 }
			: {}),
	},
};
