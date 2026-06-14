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
    </div>

    <!-- ── Tab: From DocType ── -->
    <div v-if="mode === 'doctype'" class="space-y-4">
      <div>
        <label class="block text-xs font-semibold text-ink-gray-6 uppercase tracking-wide mb-1.5">DocType</label>
        <Select
          v-model="selectedDoctype"
          :options="doctypes"
          placeholder="Select DocType"
          size="sm"
          @update:modelValue="onDoctypeChange"
        />
      </div>

      <div v-if="emailFields.length > 1">
        <label class="block text-xs font-semibold text-ink-gray-6 uppercase tracking-wide mb-1.5">Email Field</label>
        <Select
          v-model="selectedField"
          :options="emailFields.map(f => ({ label: `${f.label} (${f.fieldname})`, value: f.fieldname }))"
          placeholder="Select field"
          size="sm"
          @update:modelValue="onFieldChange"
        />
      </div>

      <div v-if="selectedDoctype && selectedField && filterFields.length" class="space-y-3">
        <p class="text-xs font-semibold text-ink-gray-6 uppercase tracking-wide">Filters <span class="font-normal normal-case text-ink-gray-4">(optional, leave blank to include all)</span></p>

        <div v-for="ff in filterFields" :key="ff.fieldname" class="flex items-center gap-3">
          <label class="w-32 flex-shrink-0 text-xs text-ink-gray-6 font-medium truncate" :title="ff.label">{{ ff.label }}</label>

          <Select
            v-if="ff.fieldtype === 'Select'"
            class="flex-1"
            size="sm"
            :model-value="activeFilters[ff.fieldname] || ''"
            :options="[{ label: 'Any', value: '' }, ...ff.options.map(o => ({ label: o, value: o }))]"
            @update:model-value="setFilter(ff.fieldname, $event)"
          />

          <DatePicker
            v-else-if="ff.fieldtype === 'Date' || ff.fieldtype === 'Datetime'"
            class="flex-1"
            size="sm"
            placeholder="On or after…"
            :model-value="activeFilters[ff.fieldname] ? activeFilters[ff.fieldname][1] : ''"
            @update:model-value="setDateFilter(ff.fieldname, $event)"
          />

          <TextInput
            v-else
            class="flex-1"
            size="sm"
            type="text"
            :placeholder="`Filter by ${ff.label}…`"
            :model-value="activeFilters[ff.fieldname] || ''"
            @update:model-value="setFilter(ff.fieldname, $event)"
          />

          <Button
            v-if="activeFilters[ff.fieldname] !== undefined && activeFilters[ff.fieldname] !== ''"
            variant="ghost"
            icon="x"
            size="sm"
            class="!text-ink-gray-3 hover:!text-ink-red-3"
            @click="clearFilter(ff.fieldname)"
          />
        </div>

        <div class="flex items-center gap-2 pt-1">
          <Button
            variant="ghost"
            size="sm"
            :label="countLoading ? 'Counting…' : 'Preview recipient count'"
            :disabled="countLoading"
            @click="previewCount"
          />
          <span v-if="recipientCount !== null" class="text-xs text-ink-gray-6 font-medium">
            → {{ recipientCount }} recipient{{ recipientCount === 1 ? "" : "s" }}
          </span>
        </div>
      </div>

      <p v-if="selectedDoctype && selectedField && !filterFields.length && !loadingFilters" class="text-xs text-ink-gray-4">
        No filterable fields found for this DocType.
      </p>
    </div>

    <!-- Live summary -->
    <p class="text-xs text-ink-gray-5 border-t border-outline-gray-1 pt-3">
      <template v-if="summaryText">{{ summaryText }}</template>
      <template v-else>Configure who will receive this campaign.</template>
    </p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { TabButtons, Textarea, Select, DatePicker, TextInput, FeatherIcon, Button } from "frappe-ui";

const props = defineProps({
  modelValue: { type: Object, default: null }, // current recipient config (or null)
});
const emit = defineEmits(["update:modelValue"]);

// ── Tabs ──────────────────────────────────────────────────────────────────────
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
const parsedPasted = computed(() =>
  pastedEmails.value
    .split(/[\n,;]/)
    .map((e) => e.trim().toLowerCase())
    .filter((e) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e))
);

// ── DocType picker ────────────────────────────────────────────────────────────
const doctypes        = ref([]);
const selectedDoctype = ref("");
const emailFields     = ref([]);
const selectedField   = ref("");
const filterFields    = ref([]);
const activeFilters   = ref({});
const loadingFilters  = ref(false);
const recipientCount  = ref(null);
const countLoading    = ref(false);

async function loadDoctypes() {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_doctypes_with_email_fields" });
    doctypes.value = (res.message || []).map(d => ({ label: d, value: d }));
  } catch { /* paste still works */ }
}

async function onDoctypeChange() {
  selectedField.value = "";
  filterFields.value  = [];
  activeFilters.value = {};
  recipientCount.value = null;
  emailFields.value = [];
  if (!selectedDoctype.value) return;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_email_fields",
      args: { doctype: selectedDoctype.value },
    });
    emailFields.value = res.message || [];
    if (emailFields.value.length === 1) {
      selectedField.value = emailFields.value[0].fieldname;
      await loadFilterFields();
    }
  } catch { emailFields.value = []; }
}

async function onFieldChange() {
  filterFields.value  = [];
  activeFilters.value = {};
  recipientCount.value = null;
  await loadFilterFields();
}

async function loadFilterFields() {
  if (!selectedDoctype.value) return;
  loadingFilters.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_doctype_filter_fields",
      args: { doctype: selectedDoctype.value },
    });
    filterFields.value = res.message || [];
  } catch {
    filterFields.value = [];
  } finally {
    loadingFilters.value = false;
  }
}

function setFilter(fieldname, value) {
  if (!value) {
    const f = { ...activeFilters.value };
    delete f[fieldname];
    activeFilters.value = f;
  } else {
    activeFilters.value = { ...activeFilters.value, [fieldname]: value };
  }
  recipientCount.value = null;
}

function setDateFilter(fieldname, value) {
  if (!value) {
    clearFilter(fieldname);
    return;
  }
  activeFilters.value = { ...activeFilters.value, [fieldname]: [">=", value] };
  recipientCount.value = null;
}

function clearFilter(fieldname) {
  const f = { ...activeFilters.value };
  delete f[fieldname];
  activeFilters.value = f;
  recipientCount.value = null;
}

async function previewCount() {
  if (!selectedDoctype.value || !selectedField.value) return;
  countLoading.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.count_doctype_recipients",
      args: {
        doctype:     selectedDoctype.value,
        email_field: selectedField.value,
        filters:     JSON.stringify(activeFilters.value),
      },
    });
    recipientCount.value = res.message?.count ?? 0;
  } catch {
    recipientCount.value = null;
  } finally {
    countLoading.value = false;
  }
}

// ── Summary / current config ──────────────────────────────────────────────────
const summaryText = computed(() => {
  if (mode.value === "group" && selectedGroup.value) {
    const g = emailGroups.value.find(x => x.name === selectedGroup.value);
    return g ? `Email Group: "${g.title || g.name}" (${g.count} subscribers)` : null;
  }
  if (mode.value === "paste" && parsedPasted.value.length) {
    return `${parsedPasted.value.length} email${parsedPasted.value.length === 1 ? "" : "s"} pasted`;
  }
  if (mode.value === "doctype" && selectedDoctype.value && selectedField.value) {
    const filterCount = Object.keys(activeFilters.value).length;
    return `${selectedDoctype.value} › ${selectedField.value}${filterCount ? ` (${filterCount} filter${filterCount === 1 ? "" : "s"})` : ""}`;
  }
  return null;
});

// Recipient config for the current selection, or null if incomplete.
const currentConfig = computed(() => {
  if (mode.value === "group") {
    return selectedGroup.value ? { type: "group", email_group: selectedGroup.value } : null;
  }
  if (mode.value === "paste") {
    return parsedPasted.value.length ? { type: "paste", recipients: parsedPasted.value } : null;
  }
  if (mode.value === "doctype" && selectedDoctype.value && selectedField.value) {
    return {
      type: "doctype",
      doctype: selectedDoctype.value,
      email_field: selectedField.value,
      filters: activeFilters.value,
    };
  }
  return null;
});

// Push selection changes up live (host dialog persists on close, no Save button).
watch(currentConfig, (cfg) => emit("update:modelValue", cfg), { deep: true });

// Restore a previously-chosen config when reopened.
function hydrate(cfg) {
  if (!cfg) return;
  if (cfg.type === "group") {
    mode.value = "group";
    selectedGroup.value = cfg.email_group || "";
  } else if (cfg.type === "paste") {
    mode.value = "paste";
    pastedEmails.value = (cfg.recipients || []).join("\n");
  } else if (cfg.type === "doctype") {
    mode.value = "doctype";
    selectedDoctype.value = cfg.doctype || "";
    selectedField.value   = cfg.email_field || "";
    activeFilters.value   = cfg.filters || {};
  }
}

onMounted(() => {
  loadEmailGroups();
  loadDoctypes();
  hydrate(props.modelValue);
});
</script>
