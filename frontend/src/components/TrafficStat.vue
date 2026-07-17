<template>
  <div ref="host" class="host"></div>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = defineProps<{
  history: { t: number; N: number; S: number; E: number; W: number }[];
}>();

const host = ref<HTMLDivElement | null>(null);
let chart: echarts.ECharts | null = null;

function render() {
  if (!host.value) return;
  if (!chart) chart = echarts.init(host.value);
  const xs = props.history.map((h) => {
    const d = new Date(h.t);
    return `${d.getMinutes().toString().padStart(2, "0")}:${d.getSeconds().toString().padStart(2, "0")}`;
  });
  chart.setOption({
    backgroundColor: "transparent",
    textStyle: { color: "#e8eaef", fontFamily: "JetBrains Mono, monospace" },
    legend: { textStyle: { color: "#c9d2ea" }, top: 0 },
    grid: { left: 40, right: 10, top: 34, bottom: 28 },
    xAxis: {
      type: "category",
      data: xs,
      axisLine: { lineStyle: { color: "#2a3142" } },
      axisLabel: { color: "#8b93a7" },
    },
    yAxis: {
      type: "value",
      name: "辆/分钟",
      nameTextStyle: { color: "#8b93a7" },
      splitLine: { lineStyle: { color: "#222833" } },
      axisLabel: { color: "#8b93a7" },
    },
    series: [
      { name: "N", type: "line", smooth: true, data: props.history.map((h) => h.N) },
      { name: "S", type: "line", smooth: true, data: props.history.map((h) => h.S) },
      { name: "E", type: "line", smooth: true, data: props.history.map((h) => h.E) },
      { name: "W", type: "line", smooth: true, data: props.history.map((h) => h.W) },
    ],
  });
}

onMounted(() => {
  render();
  window.addEventListener("resize", () => chart?.resize());
});

onBeforeUnmount(() => {
  chart?.dispose();
  chart = null;
});

watch(
  () => props.history,
  () => render(),
  { deep: true },
);
</script>

<style scoped>
.host {
  width: 100%;
  height: 260px;
}
</style>
