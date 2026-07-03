<template>

    <div class="erd-card__wrap">
      <h3 class="erd-card__title clipped-text">{{ data.label }}</h3>
    </div>

</template>

<script>
export default {
  name: 'TableNode',

  props: {
    id: {
      type: String,
      required: true,
    },

    data: {
      type: Object,
      required: true,
    },

    selected: {
      type: Boolean,
      default: false,
    },
  },
}
</script>
