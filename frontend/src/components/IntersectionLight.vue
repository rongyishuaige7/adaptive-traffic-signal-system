<template>
  <svg viewBox="0 0 400 400" class="svg">
    <defs>
      <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="4" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <!-- roads -->
    <rect x="170" y="0" width="60" height="400" fill="#1b2230" />
    <rect x="0" y="170" width="400" height="60" fill="#1b2230" />

    <g v-for="arm in arms" :key="arm.dir" :transform="arm.transform">
      <text :x="arm.tx" :y="arm.ty" class="dir mono">{{ arm.dir }}</text>
      <circle
        cx="0"
        cy="-28"
        r="14"
        :fill="color(arm.dir, 'red')"
        :opacity="lit(arm.dir, 'red') ? 1 : 0.18"
        :filter="lit(arm.dir, 'red') ? 'url(#glow)' : ''"
      />
      <circle
        cx="0"
        cy="0"
        r="14"
        :fill="color(arm.dir, 'yellow')"
        :opacity="lit(arm.dir, 'yellow') ? 1 : 0.18"
        :filter="lit(arm.dir, 'yellow') ? 'url(#glow)' : ''"
      />
      <circle
        cx="0"
        cy="28"
        r="14"
        :fill="color(arm.dir, 'green')"
        :opacity="lit(arm.dir, 'green') ? 1 : 0.18"
        :filter="lit(arm.dir, 'green') ? 'url(#glow)' : ''"
      />
    </g>
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ phase: string }>();

type Lamp = "red" | "yellow" | "green";

const arms = [
  { dir: "N", transform: "translate(200 110) rotate(0)", tx: -10, ty: -52 },
  { dir: "S", transform: "translate(200 290) rotate(180)", tx: -10, ty: -52 },
  { dir: "E", transform: "translate(290 200) rotate(90)", tx: -10, ty: -52 },
  { dir: "W", transform: "translate(110 200) rotate(-90)", tx: -10, ty: -52 },
] as const;

const colors = {
  red: "#ff3b3b",
  yellow: "#ffcc33",
  green: "#2ee59d",
};

function color(_dir: string, lamp: Lamp) {
  return colors[lamp];
}

const p = computed(() => props.phase || "NS_GREEN");

function lit(dir: string, lamp: Lamp): boolean {
  const ph = p.value;
  const ns = dir === "N" || dir === "S";
  const ew = dir === "E" || dir === "W";

  if (ph === "NS_GREEN") {
    if (ns) return lamp === "green";
    if (ew) return lamp === "red";
  }
  if (ph === "NS_YELLOW") {
    if (ns) return lamp === "yellow";
    if (ew) return lamp === "red";
  }
  if (ph === "EW_GREEN") {
    if (ew) return lamp === "green";
    if (ns) return lamp === "red";
  }
  if (ph === "EW_YELLOW") {
    if (ew) return lamp === "yellow";
    if (ns) return lamp === "red";
  }
  return lamp === "red";
}
</script>

<style scoped>
.svg {
  width: 100%;
  max-width: 420px;
  height: auto;
  display: block;
  margin: 0 auto;
}
.dir {
  fill: #c9d2ea;
  font-size: 14px;
  font-weight: 700;
}
</style>
