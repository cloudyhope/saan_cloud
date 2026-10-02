<template>
	<div>
		<div class="ma-6">
			<div @mousedown="startDrag"  @mouseup="handleDrag" id="map"></div>
		</div>
		<Loading v-if="loading" />
		<!-- <button class="save-info">Test</button> -->
	</div>
</template>
<script>
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import Loading from '../../components/Loading/index.vue';

export default {
	name: 'MapboxMap',
	components: {
        Loading
    },
	props: {
    defaultLat: {
      type: String,
      default: null
    },
    defaultLng: {
      type: String,
      default: null
    }
  },
	data() {
		// Set initial data, this.createMap() configures event listeners that update data based on user interaction
		return {
			center: { lat: this.defaultLat || "35.768032", lng: this.defaultLng || "51.418596" },
			zoom: 14,
			loading: false,
			isDragging: false,
		};
	},
	mounted() {
		if (mapboxgl.getRTLTextPluginStatus() !== 'loaded') {
			mapboxgl.accessToken =
				process.env.VUE_APP_MAPBOX_ACCESS_TOKEN || '';
			mapboxgl.setRTLTextPlugin(
				'https://api.mapbox.com/mapbox-gl-js/plugins/mapbox-gl-rtl-text/v0.2.3/mapbox-gl-rtl-text.js',
				null,
				true, // Lazy load the plugin
			);
		}
		(window.history);
		// create the map after the component is mounted
		this.createMap();
	},
	methods: {
		startDrag() {
			this.isDragging = true;
		},
		handleDrag() {
            this.loading = true
			if (this.isDragging) {
				setTimeout(() => {
					this.onClick();
				}, 1000);
			}
		},
		endDrag() {
			this.isDragging = false;
		},
		async onClick() {
			await axios
				.get('https://map.ir/reverse/fast-reverse', {
					headers: {
						'x-api-key':
							process.env.VUE_APP_MAP_IR_API_KEY || '',
					},
					params: {
						lat: `${this.center.lat}`,
						lon: `${this.center.lng}`,
					},
				})
				.then((res) => {
					(res);
					if (res.status === 200) {
						('ads', res);
						const dataToSend = res.data;
						this.$emit('child-event', dataToSend);
                        this.loading = false;
					}
				});
		},
		createMap() {
			// instantiate map.  this method runs once after the vue component is mounted to the dom
			this.map = new mapboxgl.Map({
				accessToken:
					process.env.VUE_APP_MAPBOX_ACCESS_TOKEN || '',
				container: 'map',
				style: 'mapbox://styles/mapbox/streets-v11',
				minZoom: 1,
				maxZoom: 18,
				center: this.center, // use initial data as default
				zoom: this.zoom,
			});
			const nav = new mapboxgl.GeolocateControl({
				positionOptions: {
					enableHighAccuracy: true,
				},
				// When active the map will receive updates to the device's location as it changes.
				trackUserLocation: true,
				// Draw an arrow next to the location dot to indicate which direction the device is heading.
				showUserHeading: true,
			});
			this.map.addControl(nav, 'bottom-left');
			var marker = new mapboxgl.Marker({ color: '#357AE1' })
				.setLngLat(this.map.getCenter())
				.addTo(this.map);

			// set mapbox event listeners to update Vue component data
			this.map.on('move', () => {
				// set the vue instance's data.center to the results of the mapbox instance method for getting the center
				this.center = this.map.getCenter();
				marker.setLngLat(this.map.getCenter());
			});
			this.map.on('zoom', () => {
				// set the vue instance's data.zoom to the results of the mapbox instance method for getting the zoom
				this.zoom = this.map.getZoom();
			});
		},
	},
};
</script>

<style>
#map {
	width: 100%;
	height: 50vh;
	border-radius: 8px;
}
.mapboxgl-ctrl-icon {
	background-image: url('../../assets/images/myLocation.svg') !important;
	width: 100%;
	height: 100%;
	display: flex;
	margin: 8px -8px;
	padding: 0 !important;
}
.mapboxgl-ctrl-attrib.mapboxgl-compact {
	display: none !important;
}
.mapboxgl-ctrl-group > button {
	width: 40px;
	height: 40px;
}
.mapboxgl-ctrl-logo {
	display: none !important;
}
.mapboxgl-ctrl-geolocate {
    display: none !important;
}
</style>
