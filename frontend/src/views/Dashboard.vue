<template>
  <div class="page">
    <header class="top">
      <div>
        <div class="title">车流量自适应 · 十字路口</div>
        <div class="sub">YOLOv8 + 两相位 · WebSocket 下发</div>
      </div>
      <div class="status">
        <el-tag :type="wsOk ? 'success' : 'danger'" effect="dark" class="mono">
          UI WS {{ wsOk ? "CONNECTED" : "DISCONNECTED" }}
        </el-tag>
        <div class="phase mono">{{ state.phase }}</div>
        <div class="hint mono">device clients {{ state.ws_clients?.device ?? 0 }} · connection count only</div>
        <div class="countdown mono">{{ state.remain_s }}s</div>
        <el-progress
          class="prog"
          :percentage="progress"
          :stroke-width="10"
          :show-text="false"
          color="#3aa8ff"
        />
        <div class="hint mono">total {{ state.total_s }}s · yellow {{ state.yellow_s }}s</div>
      </div>
      <div class="cards mono">
        <div class="card">
          <div class="k">g_NS</div>
          <div class="v">{{ state.green_ns_next ?? "—" }}s</div>
        </div>
        <div class="card">
          <div class="k">g_EW</div>
          <div class="v">{{ state.green_ew_next ?? "—" }}s</div>
        </div>
      </div>
    </header>

    <main class="main">
      <section class="left">
        <el-card shadow="never" class="panel">
          <template #header>路口灯（逻辑同步）</template>
          <IntersectionLight :phase="state.phase" />
        </el-card>
      </section>
      <section class="right">
        <el-card shadow="never" class="panel">
          <template #header>四路视频（带检测框）</template>
          <VideoPanel :streams="streams" />
        </el-card>
      </section>
    </main>

    <footer class="foot">
      <el-card shadow="never" class="panel wide">
        <template #header>车流量（过线计数，辆/分钟）</template>
        <div class="flowline mono">
          <span>N {{ state.flow_per_min.N ?? 0 }}</span>
          <span>S {{ state.flow_per_min.S ?? 0 }}</span>
          <span>E {{ state.flow_per_min.E ?? 0 }}</span>
          <span>W {{ state.flow_per_min.W ?? 0 }}</span>
        </div>
        <TrafficStat :history="history" />
      </el-card>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { connectUi, type StreamFact, type TrafficState } from "../api/ws";
import IntersectionLight from "../components/IntersectionLight.vue";
import TrafficStat from "../components/TrafficStat.vue";
import VideoPanel from "../components/VideoPanel.vue";

const wsOk = ref(false);
const state = reactive<TrafficState>({
  type: "state",
  phase: "NS_GREEN",
  remain_s: 0,
  total_s: 0,
  yellow_s: 3,
  flow_per_min: { N: 0, S: 0, E: 0, W: 0 },
  green_ns_next: 0,
  green_ew_next: 0,
});

const streams = reactive<Record<string, StreamFact>>({
  N: { frame_received: false, fresh: false, last_frame_age_s: null },
  S: { frame_received: false, fresh: false, last_frame_age_s: null },
  E: { frame_received: false, fresh: false, last_frame_age_s: null },
  W: { frame_received: false, fresh: false, last_frame_age_s: null },
});

const history = ref<{ t: number; N: number; S: number; E: number; W: number }[]>([]);
let ws: WebSocket | null = null;
let tick: number | null = null;

const progress = computed(() => {
  if (!state.total_s) return 0;
  return Math.min(100, Math.round((state.remain_s / state.total_s) * 100));
});

onMounted(() => {
  ws = connectUi(
    (s) => {
      Object.assign(state, s);
      history.value.push({
        t: Date.now(),
        N: s.flow_per_min?.N ?? 0,
        S: s.flow_per_min?.S ?? 0,
        E: s.flow_per_min?.E ?? 0,
        W: s.flow_per_min?.W ?? 0,
      });
      if (history.value.length > 300) history.value.splice(0, history.value.length - 300);
    },
    () => (wsOk.value = true),
    () => (wsOk.value = false),
  );
  tick = window.setInterval(async () => {
    try {
      const r = await fetch("/api/status");
      if (r.ok) {
        const j = (await r.json()) as TrafficState;
        Object.assign(state, j);
        const runtime = await fetch("/api/runtime");
        if (runtime.ok) {
          const facts = await runtime.json() as { streams?: Record<string, StreamFact> };
          if (facts.streams) Object.assign(streams, facts.streams);
        }
      }
    } catch {
      /* ignore */
    }
  }, 2000);
});

onBeforeUnmount(() => {
  ws?.close();
  if (tick) window.clearInterval(tick);
});
</script>

<style scoped>
.page {
  min-height: 100%;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.top {
  display: grid;
  grid-template-columns: 1.2fr 1.4fr 0.6fr;
  gap: 12px;
  align-items: start;
  padding: 14px 16px;
  border: 1px solid #222833;
  border-radius: 14px;
  background: linear-gradient(180deg, #121622, #0f121a);
}
.title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.2px;
}
.sub {
  margin-top: 6px;
  color: #8b93a7;
  font-size: 13px;
}
.status {
  display: grid;
  gap: 8px;
}
.phase {
  font-size: 14px;
  color: #c9d2ea;
}
.countdown {
  font-size: 44px;
  line-height: 1;
  font-weight: 700;
  color: #e8eaef;
}
.prog {
  width: 100%;
}
.hint {
  color: #8b93a7;
  font-size: 12px;
}
.cards {
  display: grid;
  gap: 10px;
}
.card {
  border: 1px solid #222833;
  background: #0b0d11;
  border-radius: 12px;
  padding: 10px 12px;
}
.k {
  color: #8b93a7;
  font-size: 12px;
}
.v {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 800;
  color: #3aa8ff;
}
.main {
  display: grid;
  grid-template-columns: 0.95fr 1.05fr;
  gap: 12px;
  align-items: start;
}
.panel {
  background: #141821 !important;
  border: 1px solid #222833 !important;
  color: #e8eaef !important;
}
.panel :deep(.el-card__header) {
  border-bottom: 1px solid #222833 !important;
  color: #dbe1ff !important;
  font-weight: 700;
}
.foot .wide {
  width: 100%;
}
.flowline {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 8px;
  color: #dbe1ff;
}
@media (max-width: 980px) {
  .top {
    grid-template-columns: 1fr;
  }
  .main {
    grid-template-columns: 1fr;
  }
}
</style>
