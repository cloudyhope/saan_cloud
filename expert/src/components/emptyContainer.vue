<template>
    <div :style="style">
    </div>
</template>
<script>
export default {
    props: ['height'],
    data() {
        return {
            fixHeight: '100px;'
        }
    },
    computed: {
      style () {
        if(this.height === undefined) {
            return 'height: ' + this.fixHeight
        } else {
            return 'height: ' + this.height
        }
      }
    },
}
</script>
