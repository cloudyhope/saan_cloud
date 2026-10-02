<template>
	<div>
		<iframe
			:src="iframeLink"
			frameborder="0"
			style="
				overflow: hidden;
				overflow-x: hidden;
				overflow-y: hidden;
				height: 80%;
				width: 80%;
				position: absolute;
			"
			height="150%"
			width="150%"
		></iframe>
	</div>
</template>
<script>
export default {
	data() {
		return {
			iframeLink: null,
			queryStates: window.location.href.split('/').slice(-1)[0],
		};
	},
	async mounted() {
		await this.getProjectList();
		this.$router.afterEach(this.handleUrlChange);
	},
	methods: {
		async handleUrlChange(to, from) {
			'sss', to.params.id, from.params.id;
			this.queryStates = to.params.id;

			await this.getProjectList();
		},
		async getProjectList() {
			// const url = window.location.href;
			// const lastParam = url.split('/').slice(-1)[0];
			const res = await this.$ApiServiceLayer.get(
				this.$PATH.RELATIVE_PATH.MULTI.MENU_EDIT_LISTS +
					this.queryStates +
					'/' +
					'?p=' +
					this.queryStates,
				this.$PATH.SERVICE_NAME.AUTH,
			);
			if (res.status === 200) {
				this.iframeLink = res.data.iframe_link;
			}
		},
	},
	watch: {
		queryStates: {
			handler(value) {
				value;
			},
		},
		immediate: true, // This ensures the watcher is triggered upon creation
	},
};
</script>
