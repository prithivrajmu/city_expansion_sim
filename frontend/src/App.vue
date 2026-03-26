<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

type Scenario = {
  id: string;
  name: string;
  description: string;
  focus: string;
  ticksPerYear: number;
};

type ScenarioDefinition = {
  id: string;
  name: string;
  description: string;
  focus: string;
  horizonTicks: number;
  objectives: Array<{ id: string; title: string; metric: string; target: number; comparator?: string }>;
  events: Array<{ tick: number; title: string; district?: string }>;
  districtStrategies?: Record<string, { mode?: string }>;
  districtAgents?: Record<string, {
    residentDemandBias?: number;
    developerIntensity?: number;
    governmentSupport?: number;
    policyFriction?: number;
    resiliencePriority?: number;
  }>;
};

type ScenarioDetail = {
  scenario: ScenarioDefinition;
  authoring: {
    cellCount: number;
    expectedCellCount: number;
    districtCount: number;
    districts: string[];
    objectiveCount: number;
    eventCount: number;
    waterCellCount: number;
    horizonTicks: number;
  };
  validation: {
    valid: boolean;
    issues: Array<{ level: string; field: string; message: string }>;
    summary: {
      cellCount: number;
      expectedCellCount: number;
      districtCount: number;
      objectiveCount: number;
      eventCount: number;
    };
  };
};

type CampaignStage = {
  id: string;
  title: string;
  scenarioId: string;
  summary: string;
};

type Campaign = {
  id: string;
  name: string;
  description: string;
  stageCount: number;
  stages: CampaignStage[];
};

type CampaignState = {
  runId: string;
  campaignId: string;
  campaignName: string;
  description: string;
  stageIndex: number;
  stageCount: number;
  currentStage: CampaignStage | null;
  completedStages: string[];
  stageResults: Array<{
    stageId: string;
    scenarioId: string;
    headline: string;
    status: string;
    passedObjectives: number;
    totalObjectives: number;
    budget: number;
    politicalCapital: number;
  }>;
  isComplete: boolean;
};

type SaveItem = {
  saveId: string;
  scenarioId: string;
  tick: number;
};

type Intervention = {
  type: string;
  district: string;
  strength: number;
  tick: number;
  touched: number;
  cost?: {
    budget: number;
    politicalCapital: number;
  };
};

type Cell = {
  index: number;
  district: string;
  kind: string;
  urbanized: boolean;
  population: number;
  land_value: number;
  risk: number;
  access: number;
};

type Snapshot = {
  tick: number;
  year: number;
  title: string;
  summary: string;
  metrics: {
    urbanCells: number;
    population: number;
    averageLandValue: number;
    urbanizationRate: number;
    averageRisk: number;
    averageAccess: number;
    interventionCount: number;
    residentPressure: number;
    developerPressure: number;
    governmentPressure: number;
    eventCount: number;
    budget: number;
    politicalCapital: number;
  };
  grid: Cell[];
  events: string[];
  interventions: Intervention[];
  districts: string[];
};

type TimelineEntry = {
  tick: number;
  year: number;
  urbanCells: number;
  population: number;
  averageLandValue: number;
  interventionCount: number;
};

type ReplayState = {
  tick: number;
  year: number;
  metrics: Snapshot["metrics"];
  grid: Cell[];
  events: string[];
  interventions: Intervention[];
  scenarioEvents: Array<{ tick: number; title: string; district: string; touched: number }>;
};

type SessionResponse = {
  sessionId: string;
  scenarioId: string;
  snapshot: Snapshot;
  campaign: CampaignState | null;
};

type Report = {
  headline: string;
  summary: string[];
  growthFrontier: Array<{ district: string; population: number; landValue: number; access: number }>;
  riskWatch: Array<{ district: string; risk: number; landValue: number }>;
  interventions: Intervention[];
  scenarioEvents: Array<{ tick: number; title: string; district: string; touched: number }>;
  recentEvents: string[];
  timeline: TimelineEntry[];
  agentSummary: {
    residents: Record<string, number>;
    developers: Record<string, number>;
    government: Record<string, number>;
  };
  districtAgents: Array<{
    district: string;
    residentDemandBias: number;
    developerIntensity: number;
    governmentSupport: number;
    policyFriction: number;
    resiliencePriority: number;
    growthReadiness: number;
    districtRisk: number;
  }>;
  comparison: {
    baselineTick: number;
    currentTick: number;
    populationDelta: number;
    urbanCellsDelta: number;
    averageLandValueDelta: number;
    averageRiskDelta: number;
    averageAccessDelta: number;
  };
  districtComparison: Array<{
    district: string;
    populationDelta: number;
    landValueDelta: number;
    riskDelta: number;
    accessDelta: number;
    urbanCellsDelta: number;
  }>;
  interventionROI: Array<{
    type: string;
    district: string;
    tick: number;
    valueGain: number;
    populationGain: number;
    riskDelta: number;
    efficiency: number;
  }>;
  resources: {
    budget: number;
    politicalCapital: number;
    startingBudget: number;
    startingPoliticalCapital: number;
  };
  objectives: Array<{
    id: string;
    title: string;
    metric: string;
    current: number;
    target: number;
    comparator: string;
    passed: boolean;
    progress: number;
  }>;
  evaluation: {
    status: string;
    headline: string;
    horizonTicks: number;
    tick: number;
    passedObjectives: number;
    totalObjectives: number;
  };
};

const apiBase = "http://localhost:5001";
const loading = ref(false);
const scenarios = ref<Scenario[]>([]);
const campaigns = ref<Campaign[]>([]);
const saves = ref<SaveItem[]>([]);
const selectedScenarioId = ref("chennai_coastal_corridor");
const selectedCampaignId = ref("southern_growth_arc");
const session = ref<SessionResponse | null>(null);
const scenarioDetail = ref<ScenarioDetail | null>(null);
const report = ref<Report | null>(null);
const timeline = ref<TimelineEntry[]>([]);
const replayTick = ref<number | null>(null);
const replayState = ref<ReplayState | null>(null);
const selectedDistrict = ref("");
const selectedCommand = ref("build_transit");
const commandStrength = ref(0.12);
const saveLabel = ref("");

const activeState = computed(() => replayState.value ?? session.value?.snapshot ?? null);

const gridTemplate = computed(() => {
  const columnCount = 6;
  return `repeat(${columnCount}, minmax(0, 1fr))`;
});

const metricCards = computed(() => {
  if (!activeState.value) {
    return [];
  }

  const metrics = activeState.value.metrics;
  return [
    { label: "Year", value: String(activeState.value.year) },
    { label: "Urban Cells", value: String(metrics.urbanCells) },
    { label: "Population", value: metrics.population.toLocaleString() },
    { label: "Avg. Land Value", value: metrics.averageLandValue.toLocaleString() },
    { label: "Avg. Access", value: String(metrics.averageAccess) },
    { label: "Avg. Risk", value: String(metrics.averageRisk) },
    { label: "Resident Pressure", value: String(metrics.residentPressure) },
    { label: "Developer Pressure", value: String(metrics.developerPressure) },
    { label: "Budget", value: metrics.budget.toLocaleString() },
    { label: "Political Capital", value: metrics.politicalCapital.toLocaleString() }
  ];
});

const districtOptions = computed(() => session.value?.snapshot.districts ?? []);
const activeCampaign = computed(() => session.value?.campaign ?? null);
const canAdvanceCampaign = computed(() => {
  if (!activeCampaign.value || activeCampaign.value.isComplete || !report.value) {
    return false;
  }
  return (
    report.value.evaluation.tick >= report.value.evaluation.horizonTicks &&
    report.value.evaluation.status === "success"
  );
});
const topDistrictDeltas = computed(() => report.value?.districtComparison.slice(0, 4) ?? []);
const topInterventionROI = computed(() => report.value?.interventionROI.slice().reverse().slice(0, 4) ?? []);
const topDistrictAgents = computed(() => report.value?.districtAgents.slice().sort((a, b) => b.growthReadiness - a.growthReadiness).slice(0, 4) ?? []);
const authoringWarnings = computed(
  () => scenarioDetail.value?.validation.issues.filter((item) => item.level !== "error") ?? []
);
const authoringErrors = computed(
  () => scenarioDetail.value?.validation.issues.filter((item) => item.level === "error") ?? []
);
const selectedDistrictCellCount = computed(() => {
  if (!session.value || !selectedDistrict.value) {
    return 0;
  }
  return session.value.snapshot.grid.filter(
    (cell) => cell.district === selectedDistrict.value && cell.kind !== "water"
  ).length;
});
const commandCost = computed(() => {
  const touched = selectedDistrictCellCount.value;
  if (!touched) {
    return { budget: 0, politicalCapital: 0 };
  }

  const factors: Record<
    string,
    { budget: number; politicalCapital: number; strengthBudget: number; strengthPoliticalCapital: number }
  > = {
    build_transit: { budget: 24, politicalCapital: 8, strengthBudget: 180, strengthPoliticalCapital: 60 },
    upzone_district: { budget: 14, politicalCapital: 11, strengthBudget: 120, strengthPoliticalCapital: 90 },
    flood_barrier: { budget: 18, politicalCapital: 9, strengthBudget: 160, strengthPoliticalCapital: 70 }
  };

  const factor = factors[selectedCommand.value];
  return {
    budget: Math.round((factor.budget * touched) + (commandStrength.value * factor.strengthBudget)),
    politicalCapital: Math.round(
      (factor.politicalCapital * touched) + (commandStrength.value * factor.strengthPoliticalCapital)
    )
  };
});
const canAffordCommand = computed(() => {
  if (!session.value) {
    return false;
  }
  return (
    session.value.snapshot.metrics.budget >= commandCost.value.budget &&
    session.value.snapshot.metrics.politicalCapital >= commandCost.value.politicalCapital
  );
});

async function fetchScenarios() {
  const response = await fetch(`${apiBase}/scenarios`);
  const data = await response.json();
  scenarios.value = data.items;
  if (scenarios.value.length > 0 && !scenarios.value.find((item) => item.id === selectedScenarioId.value)) {
    selectedScenarioId.value = scenarios.value[0].id;
  }
}

async function fetchCampaigns() {
  const response = await fetch(`${apiBase}/campaigns`);
  const data = await response.json();
  campaigns.value = data.items;
  if (campaigns.value.length > 0 && !campaigns.value.find((item) => item.id === selectedCampaignId.value)) {
    selectedCampaignId.value = campaigns.value[0].id;
  }
}

async function fetchScenarioDetail() {
  const response = await fetch(`${apiBase}/scenarios/${selectedScenarioId.value}`);
  scenarioDetail.value = await response.json();
}

async function fetchSaves() {
  const response = await fetch(`${apiBase}/saves`);
  const data = await response.json();
  saves.value = data.items;
}

async function refreshTimeline() {
  if (!session.value) {
    timeline.value = [];
    return;
  }

  const response = await fetch(`${apiBase}/sessions/${session.value.sessionId}/timeline`);
  const data = await response.json();
  timeline.value = data.items;
}

async function refreshReport() {
  if (!session.value) {
    report.value = null;
    return;
  }

  const response = await fetch(`${apiBase}/sessions/${session.value.sessionId}/report`);
  report.value = await response.json();
}

async function refreshDerivedState() {
  await Promise.all([refreshReport(), refreshTimeline(), fetchSaves()]);
}

async function createSession() {
  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenarioId: selectedScenarioId.value })
    });
    session.value = await response.json();
    selectedDistrict.value = session.value.snapshot.districts[0] ?? "";
    replayTick.value = null;
    replayState.value = null;
    await refreshDerivedState();
  } finally {
    loading.value = false;
  }
}

async function createCampaignRun() {
  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/campaigns/${selectedCampaignId.value}/runs`, {
      method: "POST"
    });
    session.value = await response.json();
    selectedScenarioId.value = session.value.scenarioId;
    selectedDistrict.value = session.value.snapshot.districts[0] ?? "";
    replayTick.value = null;
    replayState.value = null;
    await refreshDerivedState();
  } finally {
    loading.value = false;
  }
}

async function advanceCampaign() {
  if (!activeCampaign.value) {
    return;
  }

  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/campaign-runs/${activeCampaign.value.runId}/advance`, {
      method: "POST"
    });
    session.value = await response.json();
    selectedScenarioId.value = session.value.scenarioId;
    selectedDistrict.value = session.value.snapshot.districts[0] ?? "";
    replayTick.value = null;
    replayState.value = null;
    await refreshDerivedState();
  } finally {
    loading.value = false;
  }
}

async function loadSave(saveId: string) {
  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/saves/${saveId}/load`, { method: "POST" });
    session.value = await response.json();
    selectedScenarioId.value = session.value.scenarioId;
    selectedDistrict.value = session.value.snapshot.districts[0] ?? "";
    replayTick.value = null;
    replayState.value = null;
    await refreshDerivedState();
  } finally {
    loading.value = false;
  }
}

async function saveSession() {
  if (!session.value) {
    return;
  }

  loading.value = true;
  try {
    await fetch(`${apiBase}/sessions/${session.value.sessionId}/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: saveLabel.value || undefined })
    });
    saveLabel.value = "";
    await fetchSaves();
  } finally {
    loading.value = false;
  }
}

async function tick(steps: number) {
  if (!session.value) {
    return;
  }

  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/sessions/${session.value.sessionId}/tick`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ steps })
    });
    session.value = await response.json();
    replayTick.value = null;
    replayState.value = null;
    await refreshDerivedState();
  } finally {
    loading.value = false;
  }
}

async function applyCommand() {
  if (!session.value || !selectedDistrict.value) {
    return;
  }

  loading.value = true;
  try {
    const response = await fetch(`${apiBase}/sessions/${session.value.sessionId}/commands`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: selectedCommand.value,
        district: selectedDistrict.value,
        strength: commandStrength.value
      })
    });
    session.value = await response.json();
    replayTick.value = null;
    replayState.value = null;
    await refreshDerivedState();
  } finally {
    loading.value = false;
  }
}

async function fetchReplay(tickValue: number | null) {
  if (!session.value || tickValue === null || tickValue === session.value.snapshot.tick) {
    replayState.value = null;
    return;
  }

  const response = await fetch(`${apiBase}/sessions/${session.value.sessionId}/replay/${tickValue}`);
  replayState.value = await response.json();
}

function cellClass(cell: Cell) {
  if (cell.kind === "water") {
    return "tile tile-water";
  }
  if (cell.urbanized) {
    return "tile tile-urban";
  }
  if (cell.risk > 0.55) {
    return "tile tile-risk";
  }
  return "tile tile-growth";
}

function commandLabel(command: string) {
  return command.replaceAll("_", " ");
}

function formatSigned(value: number) {
  return value > 0 ? `+${value}` : `${value}`;
}

function formatObjectiveValue(value: number) {
  return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(3);
}

watch(replayTick, async (value) => {
  await fetchReplay(value);
});

watch(selectedScenarioId, async () => {
  await fetchScenarioDetail();
});

onMounted(async () => {
  await Promise.all([fetchScenarios(), fetchCampaigns(), fetchSaves()]);
  await fetchScenarioDetail();
  await createSession();
});
</script>

<template>
  <main class="app-shell">
    <section class="hero">
      <div>
        <p class="eyebrow">City Expansion Sim</p>
        <h1>Operate, save, and replay a living city-growth sandbox.</h1>
        <p class="hero-copy">
          The current build now includes replayable timeline history, saved sessions, district
          interventions, and generated reports on top of a MiroFish-style session flow.
        </p>
      </div>

      <div class="control-card">
        <label class="label" for="scenario">Scenario</label>
        <select id="scenario" v-model="selectedScenarioId" class="select">
          <option v-for="scenario in scenarios" :key="scenario.id" :value="scenario.id">
            {{ scenario.name }}
          </option>
        </select>

        <p class="support-copy">
          {{ scenarios.find((item) => item.id === selectedScenarioId)?.description }}
        </p>

        <div class="actions">
          <button class="button button-primary" :disabled="loading" @click="createSession">
            New Session
          </button>
          <button class="button" :disabled="loading" @click="createCampaignRun">
            Start Campaign
          </button>
          <button class="button" :disabled="loading || !session" @click="tick(1)">
            Tick +1
          </button>
          <button class="button" :disabled="loading || !session" @click="tick(4)">
            Tick +4
          </button>
        </div>

        <div class="save-row">
          <input v-model="saveLabel" class="select text-input" type="text" placeholder="save label" />
          <button class="button" :disabled="loading || !session" @click="saveSession">Save Session</button>
        </div>

        <label class="label" for="campaign">Campaign</label>
        <select id="campaign" v-model="selectedCampaignId" class="select">
          <option v-for="campaign in campaigns" :key="campaign.id" :value="campaign.id">
            {{ campaign.name }}
          </option>
        </select>
        <p class="support-copy">
          {{ campaigns.find((item) => item.id === selectedCampaignId)?.description }}
        </p>

        <div v-if="scenarioDetail" class="scenario-brief">
          <p class="panel-kicker">Authoring Brief</p>
          <p class="support-copy">
            {{ scenarioDetail.authoring.districtCount }} districts | {{ scenarioDetail.authoring.objectiveCount }}
            objectives | {{ scenarioDetail.authoring.eventCount }} events | grid
            {{ scenarioDetail.authoring.cellCount }}/{{ scenarioDetail.authoring.expectedCellCount }}
          </p>
          <p class="support-copy">
            Validation {{ scenarioDetail.validation.valid ? "clean" : "needs work" }} |
            errors {{ authoringErrors.length }} | warnings {{ authoringWarnings.length }}
          </p>
        </div>
      </div>
    </section>

    <section v-if="session && activeState" class="content-grid">
      <div class="panel panel-world">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Simulation World</p>
            <h2>{{ session.snapshot.title }}</h2>
          </div>
          <span class="pill">
            {{ replayState ? `Replay Tick ${activeState.tick}` : `Live Tick ${session.snapshot.tick}` }}
          </span>
        </div>

        <p class="panel-copy">
          {{ session.snapshot.summary }}
        </p>

        <div class="timeline-panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Timeline</p>
              <h3>Replay Rail</h3>
            </div>
          </div>
          <input
            v-if="timeline.length > 0"
            v-model="replayTick"
            class="range"
            type="range"
            :min="timeline[0].tick"
            :max="timeline[timeline.length - 1].tick"
            step="1"
          />
          <div class="timeline-list">
            <button
              v-for="entry in timeline"
              :key="entry.tick"
              class="timeline-chip"
              :class="{ active: activeState.tick === entry.tick }"
              @click="replayTick = entry.tick"
            >
              T{{ entry.tick }} / Y{{ entry.year }}
            </button>
            <button class="timeline-chip" :class="{ active: !replayState }" @click="replayTick = session.snapshot.tick">
              Live
            </button>
          </div>
        </div>

        <div class="city-grid" :style="{ gridTemplateColumns: gridTemplate }">
          <div v-for="cell in activeState.grid" :key="cell.index" :class="cellClass(cell)">
            <strong>{{ cell.district }}</strong>
            <span>{{ cell.kind }}</span>
            <span>Pop {{ cell.population }}</span>
            <span>Value {{ cell.land_value }}</span>
          </div>
        </div>
      </div>

      <div class="stack">
        <div class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Metrics</p>
              <h2>Growth Readout</h2>
            </div>
          </div>
          <div class="metrics">
            <article v-for="card in metricCards" :key="card.label" class="metric-card">
              <span>{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
            </article>
          </div>
          <p class="focus-line">
            Urbanization Rate {{ activeState.metrics.urbanizationRate }} | Interventions
            {{ activeState.metrics.interventionCount }} | Events {{ activeState.metrics.eventCount }}
          </p>
        </div>

        <div v-if="report" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Comparison</p>
              <h2>Baseline vs Run</h2>
            </div>
          </div>
          <div class="metrics comparison-metrics">
            <article class="metric-card">
              <span>Population Delta</span>
              <strong>{{ formatSigned(report.comparison.populationDelta) }}</strong>
            </article>
            <article class="metric-card">
              <span>Urban Cells Delta</span>
              <strong>{{ formatSigned(report.comparison.urbanCellsDelta) }}</strong>
            </article>
            <article class="metric-card">
              <span>Land Value Delta</span>
              <strong>{{ formatSigned(report.comparison.averageLandValueDelta) }}</strong>
            </article>
            <article class="metric-card">
              <span>Access / Risk</span>
              <strong>
                {{ formatSigned(report.comparison.averageAccessDelta) }} / {{ formatSigned(report.comparison.averageRiskDelta) }}
              </strong>
            </article>
          </div>
          <ul class="event-list compact-list">
            <li v-for="item in topDistrictDeltas" :key="item.district">
              {{ item.district }} | pop {{ formatSigned(item.populationDelta) }} | value {{ formatSigned(item.landValueDelta) }} |
              urban {{ formatSigned(item.urbanCellsDelta) }}
            </li>
          </ul>
        </div>

        <div v-if="report" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Objectives</p>
              <h2>Scenario Scorecard</h2>
            </div>
            <span class="pill" :class="`pill-${report.evaluation.status}`">
              {{ report.evaluation.status }}
            </span>
          </div>
          <p class="panel-copy report-headline">{{ report.evaluation.headline }}</p>
          <p class="focus-line">
            Cleared {{ report.evaluation.passedObjectives }} / {{ report.evaluation.totalObjectives }}
            objectives by tick {{ report.evaluation.tick }} of {{ report.evaluation.horizonTicks }}
          </p>
          <ul class="event-list compact-list">
            <li
              v-for="objective in report.objectives"
              :key="objective.id"
              :class="{ 'objective-pass': objective.passed }"
            >
              {{ objective.title }} |
              {{ formatObjectiveValue(objective.current) }}
              {{ objective.comparator === "at_least" ? ">=" : "<=" }}
              {{ formatObjectiveValue(objective.target) }} |
              progress {{ objective.progress }}
            </li>
          </ul>
        </div>

        <div class="panel">
          <div v-if="scenarioDetail" class="authoring-panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">Scenario Authoring</p>
                <h2>{{ scenarioDetail.scenario.name }}</h2>
              </div>
              <span class="pill" :class="scenarioDetail.validation.valid ? 'pill-success' : 'pill-at_risk'">
                {{ scenarioDetail.validation.valid ? "valid" : "issues" }}
              </span>
            </div>
            <p class="panel-copy">
              {{ scenarioDetail.scenario.focus }}
            </p>
            <div class="two-column">
              <div>
                <p class="mini-heading">Districts</p>
                <ul class="event-list compact-list">
                  <li v-for="district in scenarioDetail.authoring.districts" :key="district">
                    {{ district }}
                    <span v-if="scenarioDetail.scenario.districtStrategies?.[district]">
                      | {{ scenarioDetail.scenario.districtStrategies[district].mode }}
                    </span>
                  </li>
                </ul>
              </div>
              <div>
                <p class="mini-heading">Objectives</p>
                <ul class="event-list compact-list">
                  <li v-for="objective in scenarioDetail.scenario.objectives" :key="objective.id">
                    {{ objective.title }} | {{ objective.metric }} |
                    {{ objective.comparator === "at_most" ? "<=" : ">=" }} {{ objective.target }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="two-column">
              <div>
                <p class="mini-heading">Event Schedule</p>
                <ul class="event-list compact-list">
                  <li v-for="event in scenarioDetail.scenario.events" :key="`${event.tick}-${event.title}`">
                    T{{ event.tick }} | {{ event.title }} | {{ event.district ?? "all" }}
                  </li>
                </ul>
              </div>
              <div>
                <p class="mini-heading">Validation Issues</p>
                <ul class="event-list compact-list">
                  <li v-if="scenarioDetail.validation.issues.length === 0">No issues detected.</li>
                  <li
                    v-for="issue in scenarioDetail.validation.issues.slice(0, 6)"
                    :key="`${issue.field}-${issue.message}`"
                  >
                    {{ issue.level }} | {{ issue.field }} | {{ issue.message }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div v-if="activeCampaign" class="campaign-panel">
            <div class="panel-header">
              <div>
                <p class="panel-kicker">Campaign</p>
                <h2>{{ activeCampaign.campaignName }}</h2>
              </div>
              <span class="pill" :class="{ 'pill-success': activeCampaign.isComplete }">
                {{ activeCampaign.isComplete ? "complete" : `stage ${activeCampaign.stageIndex + 1}/${activeCampaign.stageCount}` }}
              </span>
            </div>
            <p class="panel-copy">
              {{ activeCampaign.currentStage?.summary ?? activeCampaign.description }}
            </p>
            <div class="metrics comparison-metrics">
              <article class="metric-card">
                <span>Completed Stages</span>
                <strong>{{ activeCampaign.completedStages.length }}</strong>
              </article>
              <article class="metric-card">
                <span>Current Stage</span>
                <strong>{{ activeCampaign.currentStage?.title ?? "Finished" }}</strong>
              </article>
            </div>
            <button
              class="button button-primary"
              :disabled="loading || !canAdvanceCampaign"
              @click="advanceCampaign"
            >
              Advance Campaign
            </button>
            <p v-if="!activeCampaign.isComplete && !canAdvanceCampaign && report" class="support-copy">
              Advance unlocks after the current stage reaches its horizon and clears all objectives.
            </p>
            <ul class="event-list compact-list">
              <li v-for="stage in activeCampaign.stageResults.slice().reverse()" :key="stage.stageId">
                {{ stage.stageId }} | {{ stage.passedObjectives }}/{{ stage.totalObjectives }} objectives |
                budget {{ stage.budget }} | policy {{ stage.politicalCapital }}
              </li>
            </ul>
          </div>

          <div class="panel-header">
            <div>
              <p class="panel-kicker">Interventions</p>
              <h2>Policy Console</h2>
            </div>
          </div>
          <div class="form-grid">
            <select v-model="selectedCommand" class="select">
              <option value="build_transit">build transit</option>
              <option value="upzone_district">upzone district</option>
              <option value="flood_barrier">flood barrier</option>
            </select>
            <select v-model="selectedDistrict" class="select">
              <option v-for="district in districtOptions" :key="district" :value="district">
                {{ district }}
              </option>
            </select>
            <label class="slider-label">
              Strength {{ commandStrength.toFixed(2) }}
              <input v-model="commandStrength" class="range" type="range" min="0.05" max="0.25" step="0.01" />
            </label>
            <div class="cost-strip">
              <span>Budget {{ commandCost.budget }}</span>
              <span>Policy {{ commandCost.politicalCapital }}</span>
            </div>
            <button
              class="button button-primary"
              :disabled="loading || !!replayState || !canAffordCommand"
              @click="applyCommand"
            >
              Apply Intervention
            </button>
          </div>
          <p class="support-copy">
            Remaining resources: budget {{ session.snapshot.metrics.budget }} | political capital
            {{ session.snapshot.metrics.politicalCapital }}
          </p>
          <p v-if="!canAffordCommand" class="support-copy warning-copy">
            This intervention is blocked until you recover enough budget and political capital.
          </p>

          <ul class="event-list compact-list">
            <li v-for="entry in session.snapshot.interventions.slice().reverse()" :key="`${entry.tick}-${entry.type}-${entry.district}`">
              {{ commandLabel(entry.type) }} in {{ entry.district }} at tick {{ entry.tick }} |
              budget {{ entry.cost?.budget ?? 0 }} | policy {{ entry.cost?.politicalCapital ?? 0 }}
            </li>
          </ul>

          <div v-if="report && topInterventionROI.length > 0">
            <p class="mini-heading">Intervention ROI</p>
            <ul class="event-list compact-list">
              <li v-for="entry in topInterventionROI" :key="`${entry.tick}-${entry.type}-${entry.district}-roi`">
                {{ commandLabel(entry.type) }} | {{ entry.district }} | value {{ formatSigned(entry.valueGain) }} |
                pop {{ formatSigned(entry.populationGain) }} | eff {{ entry.efficiency }}
              </li>
            </ul>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Saved Sessions</p>
              <h2>Loadout</h2>
            </div>
          </div>
          <ul class="event-list compact-list">
            <li v-for="item in saves" :key="item.saveId">
              <button class="link-button" @click="loadSave(item.saveId)">
                {{ item.saveId }} | {{ item.scenarioId }} | tick {{ item.tick }}
              </button>
            </li>
          </ul>
        </div>

        <div v-if="report" class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Generated Report</p>
              <h2>Decision Summary</h2>
            </div>
          </div>
          <p class="panel-copy report-headline">{{ report.headline }}</p>
          <ul class="event-list compact-list">
            <li v-for="line in report.summary" :key="line">{{ line }}</li>
          </ul>

          <div class="two-column">
            <div>
              <p class="mini-heading">Growth Frontier</p>
              <ul class="event-list compact-list">
                <li v-for="item in report.growthFrontier" :key="`${item.district}-${item.landValue}`">
                  {{ item.district }} | value {{ item.landValue }} | access {{ item.access }}
                </li>
              </ul>
            </div>
            <div>
              <p class="mini-heading">Risk Watch</p>
              <ul class="event-list compact-list">
                <li v-for="item in report.riskWatch" :key="`${item.district}-${item.risk}`">
                  {{ item.district }} | risk {{ item.risk }} | value {{ item.landValue }}
                </li>
              </ul>
            </div>
          </div>

          <div class="two-column">
            <div>
              <p class="mini-heading">Agent Summary</p>
              <ul class="event-list compact-list">
                <li>Residents {{ report.agentSummary.residents.mobility }} / urgency {{ report.agentSummary.residents.housingUrgency }}</li>
                <li>Developers {{ report.agentSummary.developers.capitalAggression }} / speculation {{ report.agentSummary.developers.speculation }}</li>
                <li>Government {{ report.agentSummary.government.deliveryBias }} / coordination {{ report.agentSummary.government.coordination }}</li>
              </ul>
            </div>
            <div>
              <p class="mini-heading">District Agent Pressure</p>
              <ul class="event-list compact-list">
                <li v-for="item in topDistrictAgents" :key="`${item.district}-agent`">
                  {{ item.district }} | growth {{ item.growthReadiness }} | friction {{ item.policyFriction }} |
                  resilience {{ item.resiliencePriority }}
                </li>
              </ul>
            </div>
          </div>

          <div class="two-column">
            <div>
              <p class="mini-heading">Scenario Events</p>
              <ul class="event-list compact-list">
                <li v-for="item in report.scenarioEvents.slice().reverse()" :key="`${item.tick}-${item.title}`">
                  T{{ item.tick }} | {{ item.title }} | {{ item.district }}
                </li>
              </ul>
            </div>
            <div>
              <p class="mini-heading">Authoring Stances</p>
              <ul class="event-list compact-list">
                <li
                  v-for="(stance, district) in scenarioDetail?.scenario.districtAgents ?? {}"
                  :key="`${district}-stance`"
                >
                  {{ district }} | demand {{ stance.residentDemandBias ?? 1 }} | dev {{ stance.developerIntensity ?? 1 }} |
                  gov {{ stance.governmentSupport ?? 1 }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-header">
            <div>
              <p class="panel-kicker">Recent Events</p>
              <h2>{{ replayState ? "Replay Log" : "Session Log" }}</h2>
            </div>
          </div>
          <ul class="event-list">
            <li v-for="event in activeState.events.slice().reverse()" :key="event">{{ event }}</li>
          </ul>
        </div>
      </div>
    </section>
  </main>
</template>
