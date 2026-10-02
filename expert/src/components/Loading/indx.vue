<template>
	<div class="loading-container" :class="{ show: show }"></div>
</template>

<script>
export default {
	data() {
		return {
			show: false,
		};
	},
	methods: {
		open() {
			this.show = true;
			document.getElementsByTagName('body')[0].style.overflow = 'hidden';
			this.$emit('onOpened');
		},
	},
};
</script>

<style lang="scss" scoped>
.loading-container {
	width: 100%;
	height: 100vh;
	background: yellow;
	position: fixed;
	top: 0;
	left: 0;
	opacity: 0;
	visibility: hidden;
}
.show {
	opacity: 1;
	visibility: visible;
}
</style>
