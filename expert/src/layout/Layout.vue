<template>
	<div class="layout-container">
		<div class="left-container">
				<BaseTopBar v-if="!isClientPage && !isLandingPage" variant="empty" :paddingTop="0" :z-index="topBarZIndex" />
			<div class="content" :class="{ 'landing-content': isLandingPage }">
				<div class="contdainer">
					<router-view />
				</div>
			</div>
            <Navigation />
		</div>
	</div>
</template>

<script>
import Navigation from '../components/Navigation/index.vue';
import BaseTopBar from '../components/Topbar/BaseTopbar.vue'
export default {
	name: 'layout',
	components: {
		Navigation,
        BaseTopBar
	},

	computed: {
        isLandingPage() { return ['home', 'tasks', 'clientVisitDetail', 'clientSupport', 'onlineChat', 'chatHistory', 'setting', 'notif'].includes(this.$route.name); },
        isClientPage() { return ['home', 'clientVisits', 'clientVisitDetail', 'clientSupport', 'onlineChat', 'chatHistory', 'setting', 'notif'].includes(this.$route.name); },
		title() {
			return this.$route.meta.title
		},
		topBarZIndex() {
			// return this.$route.path === '/tasks' ? 1 : 0
			return ['/tasks', '/home'].includes(this.$route.path) ? 1 : 0
		}
	}
};
</script>
<style>
.content {
	margin: 16px 0;
}
.content.landing-content { margin: 0; }

</style>
