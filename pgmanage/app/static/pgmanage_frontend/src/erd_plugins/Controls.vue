<template>
  <div class="position-relative">
    <div
      class="floating-toolbar floating-toolbar--filled floating-toolbar--right-top"
    >
      <span class="floating-toolbar__content">
        <button
          class="btn btn-icon-secondary"
          title="Download a screenshot"
          :disabled="capturingScreenshot"
          @click="$emit('screenshot')"
        >
          <i
            v-if="capturingScreenshot"
            class="fa-solid fa-spinner fa-spin"
            role="status"
          >
            <span class="sr-only">Capturing screenshot...</span>
          </i>
          <i v-else class="fa-solid fa-camera"></i>
        </button>
        <span class="divider"></span>
        <button
          class="btn btn-icon-secondary"
          @click="$emit('reset')"
          title="Reset to default"
        >
          <i class="fa-solid fa-rotate-left"></i>
        </button>

        <span class="divider"></span>

        <!-- Zoom Out -->
        <button
          class="btn btn-icon-secondary"
          @click="$emit('zoom-out')"
          title="Zoom Out"
        >
          <i class="fas fa-search-minus"></i>
        </button>
        <!-- Zoom In -->
        <button
          class="btn btn-icon-secondary"
          @click="$emit('zoom-in')"
          title="Zoom In"
        >
          <i class="fas fa-search-plus"></i>
        </button>

        <button
          type="button"
          class="btn btn-icon-secondary"
          title="Fullscreen"
          @click="$emit('toggle-fullscreen')"
        >
          <i :class="inFullscreen ? 'fas fa-compress' : 'fas fa-expand'"></i>
        </button>
      </span>
    </div>
  </div>
</template>

<script>
export default {
  name: "Controls",
  props: {
    inFullscreen: {
      type: Boolean,
      default: false,
    },
    capturingScreenshot: {
      type: Boolean,
      default: false,
    },
  },
  emits: ["screenshot", "reset", "zoom-in", "zoom-out", "toggle-fullscreen"],
};
</script>
