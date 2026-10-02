<template>
	<div class="layout-container">
		<div class="left-container">
            <div>
                <Navigation />
            </div>
			<div class="content">
				<div class="contdainer">
					<router-view />
				</div>
			</div>
		</div>
	</div>
</template>

<script>
import Navigation from '../components/Navigation/index.vue';
export default {
	name: 'layout',
	components: {
		Navigation,
	},
};
</script>

