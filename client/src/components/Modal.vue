<template>
  <transition name="modal">
    <div
      class="fixed z-10 my-12 inset-0 overflow-auto mb-16 animate-fade-in"
      @click.self="emit('close')"
    >
      <div class="flex items-center justify-center">
        <div class="rounded-lg shadow-lg p-8 backdrop-blur-lg sh">
          <Icon
            icon="mdi-close"
            class="x2 text-warning right-2 absolute cp"
            @click="emit('close')"
          />
          <div class="modal-header">
            <slot name="header">
              <!-- Default header content can be placed here -->
            </slot>
          </div>
          <slot name="body">
            <!-- Default body content can be placed here -->
          </slot>
          <div row center>
            <slot name="footer"> </slot>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
const emit = defineEmits(["close"]);
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s;
}

.modal-enter,
.modal-leave-to

/* .modal-leave-active in <2.6 */ {
  opacity: 0;
}
</style>
