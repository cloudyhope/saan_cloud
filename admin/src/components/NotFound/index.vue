<template>
	<div class="loading">
		<img :src="this.$PATH.GET_IMAGE_PATH('Dashboard/notFound.svg')" alt="" />
		<span class="text">نتیجه‌ای پیدا نشد</span>
	</div>
</template>

<script>
export default {
	name: 'NotFound',
};
</script>
<style lang="scss" scoped>
.loading {
    display: flex;
    flex-direction: column;
    justify-content: center;
    .text {
        display: flex;
        justify-content: center;
    }
}
</style>
