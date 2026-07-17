<template>
  <div class="grid">
    <div v-for="d in dirs" :key="d" class="cell">
      <div class="label mono">{{ d }}</div>
      <div class="fact mono" :class="streams[d]?.fresh ? 'fresh' : 'waiting'">
        {{ streams[d]?.fresh ? `frame ${streams[d].last_frame_age_s}s ago` : "no fresh frame" }}
      </div>
      <img class="feed" :src="`/api/video/${d}.mjpg`" :alt="`${d} annotated stream`" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { StreamFact } from "../api/ws";

defineProps<{ streams: Record<string, StreamFact> }>();
const dirs = ["N", "S", "E", "W"] as const;
</script>

<style scoped>
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.cell { background: #0b0d11; border: 1px solid #222833; border-radius: 10px; overflow: hidden; position: relative; }
.label, .fact { position: absolute; top: 8px; z-index: 2; background: rgba(0,0,0,.72); padding: 2px 8px; border-radius: 6px; font-size: 12px; }
.label { left: 8px; color: #dbe1ff; }
.fact { right: 8px; }
.fact.fresh { color: #69db7c; }
.fact.waiting { color: #ffd43b; }
.feed { width: 100%; height: 220px; object-fit: cover; display: block; background: #000; }
@media (max-width: 640px) { .grid { grid-template-columns: 1fr; } }
</style>
