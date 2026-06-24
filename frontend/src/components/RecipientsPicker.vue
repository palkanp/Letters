<template>
  <div class="space-y-2">

    <div
      v-for="(source, idx) in sources"
      :key="source._id"
      class="rounded-lg border border-outline-gray-2 overflow-hidden"
    >
      <!-- Block header -->
      <div class="flex items-center gap-2 px-3 py-2 border-b border-outline-gray-1 bg-surface-gray-1">
        <!-- Type pills -->
        <div class="flex items-center gap-0.5 bg-surface-gray-2 rounded-md p-0.5">
          <button
            v-for="tab in SOURCE_TABS"
            :key="tab.id"
            class="rounded px-2.5 py-1 text-xs font-medium transition-colors leading-none"
            :class="source.type === tab.id
              ? 'bg-surface-base text-ink-gray-8 shadow-sm'
              : 'text-ink-gray-4 hover:text-ink-gray-6'"
            @click="setSourceType(idx, tab.id)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="ml-auto flex items-center gap-1.5">
          <!-- Count badge -->
          <span
            v-if="sourceCounts[idx] !== null && sourceCounts[idx] !== undefined"
            class="text-xs font-semibold tabular-nums px-2 py-0.5 rounded-full"
            :class="sourceCounts[idx] > 0
              ? 'bg-surface-green-2 text-ink-green-7'
              : 'bg-surface-gray-3 text-ink-gray-5'"
          >
            {{ sourceCounts[idx].toLocaleString() }}
          </span>
          <!-- Remove -->
          <button
            class="size-5 flex items-center justify-center rounded text-ink-gray-3 hover:text-ink-red-4 hover:bg-surface-red-1 transition-colors text-sm leading-none"
            aria-label="Remove source"
            @click="removeSource(idx)"
          >×</button>
        </div>
      </div>

      <!-- Block body -->
      <div class="px-3 py-3 space-y-3">

        <!-- Email Group -->
        <div v-if="source.type === 'group'">
          <div v-if="loadingGroups" class="text-xs text-ink-gray-4 py-1">Loading groups…</div>
          <template v-else>
            <Select
              :model-value="source.email_group || ''"
              :options="emailGroupOptions"
              placeholder="Select email group"
              size="sm"
              @update:model-value="v => setGroupValue(idx, v)"
            />
            <p v-if="emailGroups.length === 0" class="text-xs text-ink-gray-4 mt-2">
              No email groups found. Create one in Frappe first.
            </p>
          </template>
        </div>

        <!-- Paste emails -->
        <div v-else-if="source.type === 'paste'" class="space-y-2">
          <Textarea
            :model-value="source._raw || ''"
            :rows="4"
            placeholder="Paste addresses separated by comma, semicolon, or newline"
            size="sm"
            @update:model-value="v => setPastedValue(idx, v)"
          />
          <div class="flex items-center justify-between">
            <span v-if="sourceCounts[idx] !== null && sourceCounts[idx] !== undefined" class="text-xs text-ink-gray-5">
              {{ sourceCounts[idx] }} valid address{{ sourceCounts[idx] === 1 ? '' : 'es' }}
            </span>
            <span v-else class="text-xs text-ink-gray-3">Paste addresses above</span>
            <Button
              v-if="sourceCounts[idx] > 0"
              variant="ghost"
              size="sm"
              label="Save as email group"
              :loading="savingGroup[idx]"
              class="!text-xs !text-ink-gray-6"
              @click="saveAsEmailGroup(idx)"
            />
          </div>
        </div>

        <!-- DocType -->
        <div v-else-if="source.type === 'doctype'" class="space-y-2">
          <DoctypeTab
            :model-value="source"
            @update:model-value="v => updateDoctype(idx, v)"
            @update:count="v => setDoctypeCount(idx, v)"
          />
          <div v-if="source.doctype && source.email_field" class="flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              label="Save as email group"
              :loading="savingGroup[idx]"
              class="!text-xs !text-ink-gray-6"
              @click="saveAsEmailGroup(idx)"
            />
          </div>
        </div>

      </div>
    </div>

    <!-- Add source -->
    <button
      class="w-full rounded-lg border border-dashed border-outline-gray-2 py-2.5 text-xs text-ink-gray-4 hover:text-ink-gray-6 hover:border-outline-gray-3 hover:bg-surface-gray-1 transition-colors flex items-center justify-center gap-1.5"
      @click="addSource"
    >
      <span class="lucide-plus size-3.5" aria-hidden="true" />
      Add another source
    </button>

    <!-- Total bar (2+ sources only) -->
    <div
      v-if="sources.length > 1 && approximateTotal > 0"
      class="flex items-center justify-between rounded-md bg-surface-gray-2 px-3 py-2 text-xs"
    >
      <span class="text-ink-gray-5">Total across all sources</span>
      <span class="font-medium tabular-nums text-ink-gray-8">~{{ approximateTotal.toLocaleString() }} recipients</span>
    </div>

    <p v-if="sources.length === 0" class="text-xs text-ink-gray-4 pt-1">
      Configure who will receive this letter.
    </p>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { Select, Textarea, Button, toast } from "frappe-ui";
import DoctypeTab from "./DoctypeTab.vue";

const props = defineProps({
  modelValue: { type: [Array, Object], default: null },
});
const emit = defineEmits(["update:modelValue"]);

const SOURCE_TABS = [
  { id: "group",   label: "Email group" },
  { id: "doctype", label: "DocType" },
  { id: "paste",   label: "Paste emails" },
];

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

let _idCounter = 0;
function nextId() { return ++_idCounter; }

// ── State ─────────────────────────────────────────────────────────────────────
const sources       = ref([]);
const emailGroups   = ref([]);
const loadingGroups = ref(false);
const savingGroup   = ref({});

const emailGroupOptions = computed(() =>
  emailGroups.value.map(g => ({
    label: `${g.title || g.name} (${g.count})`,
    value: g.name,
  }))
);

const doctypeCounts = ref({}); // { source._id: count }

function setDoctypeCount(idx, count) {
  const id = sources.value[idx]?._id;
  if (id !== undefined) doctypeCounts.value = { ...doctypeCounts.value, [id]: count };
}

const sourceCounts = computed(() =>
  sources.value.map(src => {
    if (src.type === "group") {
      const g = emailGroups.value.find(x => x.name === src.email_group);
      return g ? g.count : null;
    }
    if (src.type === "paste") {
      const raw = src._raw || "";
      if (!raw.trim()) return null;
      return raw.split(/[\n,;]/).map(e => e.trim().toLowerCase()).filter(e => EMAIL_RE.test(e)).length;
    }
    if (src.type === "doctype") {
      const c = doctypeCounts.value[src._id];
      return c !== undefined ? c : null;
    }
    return null;
  })
);

const approximateTotal = computed(() =>
  sourceCounts.value.reduce((sum, c) => sum + (c ?? 0), 0)
);

// ── Load email groups ─────────────────────────────────────────────────────────
async function loadEmailGroups() {
  loadingGroups.value = true;
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_email_groups" });
    emailGroups.value = res.message || [];
  } catch {
    emailGroups.value = [];
  } finally {
    loadingGroups.value = false;
  }
}

// ── Source CRUD ───────────────────────────────────────────────────────────────
function addSource() {
  sources.value.push({ _id: nextId(), type: "group", email_group: "" });
}

function removeSource(idx) {
  sources.value.splice(idx, 1);
}

function setSourceType(idx, type) {
  sources.value[idx] = { _id: sources.value[idx]._id, type };
}

function setGroupValue(idx, value) {
  sources.value[idx] = { ...sources.value[idx], email_group: value };
}

function setPastedValue(idx, raw) {
  sources.value[idx] = { ...sources.value[idx], _raw: raw };
}

function updateDoctype(idx, config) {
  sources.value[idx] = { ...sources.value[idx], ...config, _id: sources.value[idx]._id };
}

// ── Save as email group ───────────────────────────────────────────────────────
async function saveAsEmailGroup(idx) {
  const src = sources.value[idx];
  const defaultTitle = src.type === "paste"
    ? "Pasted Recipients"
    : src.type === "doctype"
      ? `${src.doctype || "DocType"} Audience`
      : "Audience";

  const title = await promptGroupName(defaultTitle);
  if (!title) return;

  savingGroup.value = { ...savingGroup.value, [idx]: true };
  try {
    const res = await frappe.call({
      method: "letters.letters.api.create_email_group_from_source",
      args: { title, source_config: JSON.stringify(buildSourceConfig(src)) },
    });
    const group = res.message;
    emailGroups.value = [...emailGroups.value, { name: group.name, title: group.title, count: group.count }];
    sources.value[idx] = { _id: sources.value[idx]._id, type: "group", email_group: group.name };
    toast.success(`"${group.title}" created with ${group.count} members.`);
  } catch (e) {
    toast.error(e?.message || "Failed to create email group.");
  } finally {
    savingGroup.value = { ...savingGroup.value, [idx]: false };
  }
}

function promptGroupName(defaultTitle) {
  return new Promise(resolve => {
    frappe.prompt(
      { fieldname: "title", fieldtype: "Data", label: "Group name", default: defaultTitle, reqd: 1 },
      ({ title }) => resolve(title),
      "Save as email group",
      "Save",
    );
  });
}

// ── Serialise ─────────────────────────────────────────────────────────────────
function buildSourceConfig(src) {
  if (src.type === "group") {
    return { type: "group", email_group: src.email_group };
  }
  if (src.type === "paste") {
    const recipients = (src._raw || "")
      .split(/[\n,;]/)
      .map(e => e.trim().toLowerCase())
      .filter(e => EMAIL_RE.test(e));
    return { type: "paste", recipients };
  }
  if (src.type === "doctype") {
    return {
      type:        "doctype",
      doctype:     src.doctype     || "",
      email_field: src.email_field || "",
      filters:     src.filters     || {},
    };
  }
  return null;
}

const currentConfig = computed(() => {
  const valid = sources.value.map(buildSourceConfig).filter(Boolean);
  if (!valid.length) return null;
  return valid.length === 1 ? valid[0] : valid;
});

watch(currentConfig, cfg => emit("update:modelValue", cfg), { deep: true });

// ── Hydrate ───────────────────────────────────────────────────────────────────
function hydrate(cfg) {
  if (!cfg) return;
  const list = Array.isArray(cfg) ? cfg : [cfg];
  sources.value = list.map(src => {
    const base = { _id: nextId(), ...src };
    if (src.type === "paste") base._raw = (src.recipients || []).join("\n");
    return base;
  });
}

onMounted(() => {
  loadEmailGroups();
  if (props.modelValue) hydrate(props.modelValue);
  else addSource();
});
</script>
