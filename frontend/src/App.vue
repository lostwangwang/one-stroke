<template>
  <div id="app">
    <GameCanvas />
  </div>
</template>

<script setup>
import GameCanvas from "./components/GameCanvas.vue";
</script>

<style>
html,
body,
#app {
  height: 100%;
  margin: 0;
}
#app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
</style>
