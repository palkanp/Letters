<template>
  <!-- Recipient selection UI (no dialog chrome). Emits the recipient config via
       v-model as the selection changes, so a host dialog needs no Save button. -->
  <div class="space-y-5">

    <!-- Mode tabs -->
    <TabButtons
      :buttons="tabs.map(t => ({ label: t.label, value: t.id }))"
      v-model="mode"
    />

    <!-- ── Tab: Email Group ── -->
    <div v-if="mode === 'group'" class="space-y-4">
      <div v-if="loadingGroups" class="text-xs text-ink-gray-4 py-2">Loading groups…</div>
      <div v-else-if="emailGroups.length === 0" class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-6 text-center">
        <p class="text-sm text-ink-gray-5 font-medium">No Email Groups found</p>
        <p class="text-xs text-ink-gray-4 mt-1">
          Create one via <strong>Email Group</strong> in Frappe to manage subscribers with unsubscribe support.
        </p>
      </div>
      <div v-else class="space-y-2">
        <label
          v-for="g in emailGroups"
          :key="g.name"
          class="flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-colors"
          :class="selectedGroup === g.name ? 'border-outline-gray-5 bg-surface-gray-1' : 'border-outline-gray-2 hover:border-outline-gray-3'"
        >
          <input type="radio" v-model="selectedGroup" :value="g.name" class="accent-ink-gray-9" />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-ink-gray-8">{{ g.title || g.name }}</p>
            <p class="text-xs text-ink-gray-4">{{ g.count }} active subscriber{{ g.count === 1 ? "" : "s" }}</p>
          </div>
          <span v-if="selectedGroup === g.name" class="text-xs text-ink-gray-5 font-medium">Selected</span>
        </label>
      </div>
      <p class="text-xs text-ink-gray-4">Unsubscribe links are added automatically for Email Group sends.</p>
    </div>

    <!-- ── Tab: Paste emails ── -->
    <div v-if="mode === 'paste'" class="space-y-3">
      <Textarea
        v-model="pastedEmails"
        :rows="6"
        placeholder="one@example.com&#10;two@example.com&#10;three@example.com"
        size="sm"
      />
      <p class="text-xs text-ink-gray-4">One email per line, or comma- or semicolon-separated.</p>
      <div v-if="parsedPasted.length > 0" class="text-xs text-ink-gray-5 font-medium">
        {{ parsedPasted.length }} valid email{{ parsedPasted.length === 1 ? "" : "s" }} detected
      </div>
      <div v-if="invalidPasted.length > 0" class="rounded-md bg-red-50 border border-red-200 px-3 py-2 space-y-1">
        <p class="text-xs font-medium text-red-700">
          {{ invalidPasted.length }} invalid address{{ invalidPasted.length === 1 ? "" : "es" }} will be ignored:
        </p>
        <ul class="text-xs text-red-600 space-y-0.5">
          <li v-for="e in invalidPasted" :key="e" class="font-mono">{{ e }}</li>
        </ul>
      </div>
    </div>

    <!-- ── Tab: From DocType ── -->
    <DoctypeTab
      v-if="mode === 'doctype'"
      :model-value="doctypeConfig"
      @update:model-value="doctypeConfig = $event"
    />

    <!-- Live summary -->
    <p class="text-xs text-ink-gray-5 border-t border-outline-gray-1 pt-3">
      <template v-if="summaryText">{{ summaryText }}</template>
      <template v-else>Configure who will receive this campaign.</template>
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { TabButtons, Textarea } from "frappe-ui";
import DoctypeTab from "./DoctypeTab.vue";

const props = defineProps({
  modelValue: { type: Object, default: null },
});
const emit = defineEmits(["update:modelValue"]);

const tabs = [
  { id: "group",   label: "Email Group" },
  { id: "paste",   label: "Paste Emails" },
  { id: "doctype", label: "From DocType" },
];
const mode = ref("group");

// ── Email Group ───────────────────────────────────────────────────────────────
const emailGroups   = ref([]);
const selectedGroup = ref("");
const loadingGroups = ref(false);

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

// ── Paste ─────────────────────────────────────────────────────────────────────
const pastedEmails = ref("");
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const _allPasted = computed(() =>
  pastedEmails.value
    .split(/[\n,;]/)
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean)
);
const parsedPasted  = computed(() => _allPasted.value.filter((e) => EMAIL_RE.test(e)));
const invalidPasted = computed(() => _allPasted.value.filter((e) => !EMAIL_RE.test(e)));

// ── DocType (delegated to DoctypeTab) ─────────────────────────────────────────
const doctypeConfig = ref(null);

// ── Summary / current config ──────────────────────────────────────────────────
const summaryText = computed(() => {
  if (mode.value === "group" && selectedGroup.value) {
    const g = emailGroups.value.find(x => x.name === selectedGroup.value);
    return g ? `Email Group: "${g.title || g.name}" (${g.count} subscribers)` : null;
  }
  if (mode.value === "paste" && parsedPasted.value.length) {
    return `${parsedPasted.value.length} email${parsedPasted.value.length === 1 ? "" : "s"} pasted`;
  }
  if (mode.value === "doctype" && doctypeConfig.value) {
    const { doctype, email_field, filters } = doctypeConfig.value;
    const filterCount = Object.keys(filters || {}).length;
    return `${doctype} › ${email_field}${filterCount ? ` (${filterCount} filter${filterCount === 1 ? "" : "s"})` : ""}`;
  }
  return null;
});

const currentConfig = computed(() => {
  if (mode.value === "group") {
    return selectedGroup.value ? { type: "group", email_group: selectedGroup.value } : null;
  }
  if (mode.value === "paste") {
    return parsedPasted.value.length ? { type: "paste", recipients: parsedPasted.value } : null;
  }
  if (mode.value === "doctype") {
    return doctypeConfig.value || null;
  }
  return null;
});

watch(currentConfig, (cfg) => emit("update:modelValue", cfg), { deep: true });

function hydrate(cfg) {
  if (!cfg) return;
  if (cfg.type === "group") {
    mode.value         = "group";
    selectedGroup.value = cfg.email_group || "";
  } else if (cfg.type === "paste") {
    mode.value         = "paste";
    pastedEmails.value = (cfg.recipients || []).join("\n");
  } else if (cfg.type === "doctype") {
    mode.value      = "doctype";
    doctypeConfig.value = cfg;
  }
}

onMounted(() => {
  loadEmailGroups();
  hydrate(props.modelValue);
});
</script>
