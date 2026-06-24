<template>
  <div class="space-y-3">

    <!-- DocType selector + Filter button on same row -->
    <div class="flex items-center gap-2">
      <Select
        v-model="selectedDoctype"
        :options="doctypes"
        placeholder="Select DocType"
        size="sm"
        class="flex-1"
        @update:modelValue="onDoctypeChange"
      />
      <Button
        v-if="selectedDoctype && selectedField"
        variant="subtle"
        size="sm"
        icon="lucide-list-filter"
        class="!text-xs flex-shrink-0"
        :theme="appliedCount > 0 ? 'blue' : 'gray'"
        @click="toggleFilters"
      >
        Filter
        <span
          v-if="appliedCount > 0"
          class="ml-1 flex size-4 items-center justify-center rounded-full bg-surface-blue-3 text-2xs font-semibold text-white"
        >{{ appliedCount }}</span>
      </Button>
    </div>

    <Select
      v-if="emailFields.length > 1"
      v-model="selectedField"
      :options="emailFields.map(f => ({ label: `${f.label} (${f.fieldname})`, value: f.fieldname }))"
      placeholder="Select email field"
      size="sm"
      @update:modelValue="onFieldChange"
    />

    <div v-if="selectedDoctype && selectedField">

      <!-- Filter panel -->
      <div v-if="showFilters" class="mt-2 rounded-lg border border-outline-gray-2 overflow-hidden">
        <div class="py-1">
          <div
            v-for="(row, i) in filterRows"
            :key="i"
            class="flex items-center gap-2 px-3 py-1.5"
          >
            <!-- Field selector -->
            <Select
              :model-value="row.field"
              :options="filterFieldOptions"
              placeholder="Field"
              size="sm"
              class="w-32 flex-shrink-0"
              @update:model-value="v => setRowField(i, v)"
            />

            <!-- Operator selector -->
            <Select
              :model-value="row.op"
              :options="operatorsFor(row.field)"
              size="sm"
              class="w-36 flex-shrink-0"
              @update:model-value="v => onOpChange(i, v)"
            />

            <!-- Value input -->
            <template v-if="row.op === 'is'">
              <Select
                :model-value="row.value"
                :options="[{ label: 'Set', value: 'set' }, { label: 'Not Set', value: 'not set' }]"
                size="sm"
                class="flex-1"
                @update:model-value="v => (filterRows[i].value = v)"
              />
            </template>

            <template v-else-if="row.op === 'Timespan'">
              <Select
                :model-value="row.value"
                :options="TIMESPAN_OPTIONS"
                placeholder="Select period"
                size="sm"
                class="flex-1"
                @update:model-value="v => (filterRows[i].value = v)"
              />
            </template>

            <template v-else-if="row.op === 'Between' && isDateField(row.field)">
              <DatePicker :model-value="row.value?.[0] || ''" size="sm" placeholder="From" class="flex-1" @update:model-value="v => setBetween(i, 0, v)" />
              <DatePicker :model-value="row.value?.[1] || ''" size="sm" placeholder="To"   class="flex-1" @update:model-value="v => setBetween(i, 1, v)" />
            </template>

            <!-- Select fieldtype — show static options dropdown -->
            <template v-else-if="isSelectField(row.field)">
              <Select
                :model-value="row.value"
                :options="selectOptionsFor(row.field)"
                placeholder="Select value"
                size="sm"
                class="flex-1"
                @update:model-value="v => (filterRows[i].value = v)"
              />
            </template>

            <!-- Link fieldtype — autocomplete via frappe.desk.search.search_link -->
            <template v-else-if="isLinkField(row.field)">
              <Autocomplete
                :model-value="{ label: row.value, value: row.value }"
                :options="linkOptions[row.field] || []"
                placeholder="Search…"
                size="sm"
                class="flex-1"
                @update:query="q => fetchLinkOptions(row.field, q)"
                @update:model-value="v => (filterRows[i].value = v?.value ?? '')"
              />
            </template>

            <template v-else-if="isDateField(row.field)">
              <DatePicker
                :model-value="row.value"
                size="sm"
                class="flex-1"
                @update:model-value="v => (filterRows[i].value = v)"
              />
            </template>

            <template v-else>
              <TextInput
                :model-value="row.value"
                placeholder="Value"
                size="sm"
                class="flex-1"
                @update:model-value="v => (filterRows[i].value = v)"
              />
            </template>

            <button
              class="flex-shrink-0 size-5 flex items-center justify-center text-ink-gray-3 hover:text-ink-red-4 rounded"
              @click="filterRows.splice(i, 1)"
            >×</button>
          </div>

          <div v-if="filterRows.length === 0" class="px-3 py-2.5 text-xs text-ink-gray-4">
            No filters — click below to add one.
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-between border-t border-outline-gray-1 bg-surface-gray-1 px-3 py-2">
          <button
            class="flex items-center gap-1 text-xs text-ink-gray-5 hover:text-ink-gray-8 transition-colors"
            @click="addRow"
          >
            <span class="lucide-plus size-3.5" aria-hidden="true" />
            Add a filter
          </button>
          <div class="flex items-center gap-2">
            <Button v-if="appliedCount > 0" variant="ghost" size="sm" label="Clear filters" class="!text-xs" @click="clearFilters" />
            <Button variant="subtle" size="sm" label="Apply filters" class="!text-xs" :loading="countLoading" @click="applyFilters" />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { Select, TextInput, DatePicker, Button, Autocomplete } from "frappe-ui";

const props = defineProps({
  modelValue: { type: Object, default: null },
});
const emit = defineEmits(["update:modelValue", "update:count"]);

// ── Operator list — mirrors filter.js exactly ─────────────────────────────────
const ALL_OPS = [
  { value: "=",        label: "Equals" },
  { value: "!=",       label: "Not Equals" },
  { value: "like",     label: "Like" },
  { value: "not like", label: "Not Like" },
  { value: "in",       label: "In" },
  { value: "not in",   label: "Not In" },
  { value: "is",       label: "Is" },
  { value: ">",        label: "Greater Than" },
  { value: "<",        label: "Less Than" },
  { value: ">=",       label: "Greater Than or Equal To" },
  { value: "<=",       label: "Less Than or Equal To" },
  { value: "Between",  label: "Between" },
  { value: "Timespan", label: "Timespan" },
];

const INVALID_OPS = {
  Date:         ["like", "not like"],
  Datetime:     ["like", "not like", "in", "not in", "=", "!="],
  Time:         ["Between", "Timespan"],
  Data:         ["Between", "Timespan"],
  Currency:     ["Between", "Timespan"],
  Link:         ["Between", "Timespan", ">", "<", ">=", "<="],
  Color:        ["Between", "Timespan", ">", "<", ">=", "<="],
  Select:       ["like", "not like", "Between", "Timespan", ">", "<", ">=", "<="],
  Check:        ["!=", "like", "not like", "in", "not in", "is", ">", "<", ">=", "<=", "Between", "Timespan"],
  Int:          ["like", "not like", "Between", "Timespan", "in", "not in"],
  Float:        ["like", "not like", "Between", "Timespan", "in", "not in"],
  Percent:      ["like", "not like", "Between", "Timespan", "in", "not in"],
  Rating:       ["like", "not like", "Between", "Timespan", "in", "not in"],
  "Small Text": ["Between", "Timespan", ">", "<", ">=", "<=", "in", "not in"],
  "Long Text":  ["Between", "Timespan", ">", "<", ">=", "<=", "in", "not in"],
  Text:         ["Between", "Timespan", ">", "<", ">=", "<=", "in", "not in"],
  Code:         ["Between", "Timespan", ">", "<", ">=", "<=", "in", "not in"],
};

const TIMESPAN_OPTIONS = [
  "last week", "last month", "last quarter", "last 6 months", "last year",
  "yesterday", "today", "tomorrow",
  "this week", "this month", "this quarter", "this year",
  "next week", "next month", "next quarter", "next year",
].map(v => ({ label: v.replace(/\b\w/g, c => c.toUpperCase()), value: v }));

// ── State ─────────────────────────────────────────────────────────────────────
const doctypes        = ref([]);
const selectedDoctype = ref("");
const emailFields     = ref([]);
const selectedField   = ref("");
const filterFields    = ref([]);
const recipientCount  = ref(null);
const countLoading    = ref(false);
const showFilters     = ref(false);
const filterRows      = ref([]);
const activeFilters   = ref({});
const linkOptions     = ref({});

const appliedCount       = computed(() => Object.keys(activeFilters.value).length);
const filterFieldOptions = computed(() =>
  filterFields.value.map(ff => ({ label: ff.label, value: ff.fieldname }))
);

// ── Field type helpers ────────────────────────────────────────────────────────
function fieldMeta(fieldname) {
  return filterFields.value.find(f => f.fieldname === fieldname) || null;
}
function isDateField(fn)   { const ft = fieldMeta(fn)?.fieldtype; return ft === "Date" || ft === "Datetime"; }
function isSelectField(fn) { return fieldMeta(fn)?.fieldtype === "Select"; }
function isLinkField(fn)   { return fieldMeta(fn)?.fieldtype === "Link"; }

function selectOptionsFor(fieldname) {
  return (fieldMeta(fieldname)?.options || []).map(o => ({ label: o, value: o }));
}

function operatorsFor(fieldname) {
  const ft = fieldMeta(fieldname)?.fieldtype || "Data";
  const invalid = INVALID_OPS[ft] || [];
  return ALL_OPS.filter(op => !invalid.includes(op.value));
}

// ── Link autocomplete via frappe.desk.search.search_link ─────────────────────
async function fetchLinkOptions(fieldname, query) {
  const ff = fieldMeta(fieldname);
  if (!ff?.options_doctype) return;
  try {
    const res = await frappe.call({
      method: "frappe.desk.search.search_link",
      args: {
        txt:              query || "",
        doctype:          ff.options_doctype,
        page_length:      20,
        reference_doctype: selectedDoctype.value,
        ignore_user_permissions: 0,
      },
    });
    linkOptions.value = {
      ...linkOptions.value,
      [fieldname]: (res.message || []).map(r => ({
        label: r.description ? `${r.value} — ${r.description}` : r.value,
        value: r.value,
      })),
    };
  } catch { /* ignore */ }
}

// ── Filter row management ─────────────────────────────────────────────────────
function toggleFilters() {
  showFilters.value = !showFilters.value;
  // Auto-add one empty row when opening with no rows
  if (showFilters.value && filterRows.value.length === 0) addRow();
}

function addRow() {
  const first = filterFields.value[0];
  if (!first) return;
  const ops = operatorsFor(first.fieldname);
  filterRows.value.push({ field: first.fieldname, op: ops[0].value, value: "" });
  prefetchLinkOptions(first.fieldname);
}

function setRowField(i, field) {
  const ops = operatorsFor(field);
  filterRows.value[i] = { field, op: ops[0].value, value: "" };
  prefetchLinkOptions(field);
}

// Pre-fetch link options immediately when a Link field is shown so the
// autocomplete is populated without requiring the user to type first.
function prefetchLinkOptions(fieldname) {
  if (isLinkField(fieldname) && !linkOptions.value[fieldname]?.length) {
    fetchLinkOptions(fieldname, "");
  }
}

function onOpChange(i, op) {
  filterRows.value[i] = { ...filterRows.value[i], op, value: op === "Between" ? ["", ""] : "" };
}

function setBetween(i, idx, v) {
  const val = Array.isArray(filterRows.value[i].value) ? [...filterRows.value[i].value] : ["", ""];
  val[idx] = v;
  filterRows.value[i] = { ...filterRows.value[i], value: val };
}

function applyFilters() {
  const dict = {};
  for (const row of filterRows.value) {
    if (!row.field) continue;
    if (row.op === "is" && row.value) {
      dict[row.field] = [row.op, row.value];
    } else if (row.op === "Between") {
      const [a, b] = Array.isArray(row.value) ? row.value : ["", ""];
      if (a || b) dict[row.field] = [row.op, [a, b]];
    } else if (row.value !== "" && row.value !== null && row.value !== undefined) {
      dict[row.field] = [row.op, row.value];
    }
  }
  activeFilters.value = dict;
  previewCount();
  emitConfig();
}

function clearFilters() {
  filterRows.value     = [];
  activeFilters.value  = {};
  recipientCount.value = null;
  emitConfig();
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
    recipientCount.value = null; emit("update:count", null);
  } finally {
    countLoading.value = false;
    emit("update:count", recipientCount.value);
  }
}

// ── DocType / field loading ───────────────────────────────────────────────────
async function loadDoctypes() {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_doctypes_with_email_fields" });
    doctypes.value = (res.message || []).map(d => ({ label: d, value: d }));
  } catch { /* ignore */ }
}

async function onDoctypeChange() {
  selectedField.value  = "";
  filterFields.value   = [];
  filterRows.value     = [];
  activeFilters.value  = {};
  recipientCount.value = null;
  emailFields.value    = [];
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
  emitConfig();
}

async function onFieldChange() {
  filterRows.value     = [];
  activeFilters.value  = {};
  recipientCount.value = null;
  await loadFilterFields();
  emitConfig();
}

async function loadFilterFields() {
  if (!selectedDoctype.value) return;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_doctype_filter_fields",
      args: { doctype: selectedDoctype.value },
    });
    filterFields.value = res.message || [];
  } catch {
    filterFields.value = [];
  }
}

function emitConfig() {
  if (selectedDoctype.value && selectedField.value) {
    emit("update:modelValue", {
      type:        "doctype",
      doctype:     selectedDoctype.value,
      email_field: selectedField.value,
      filters:     activeFilters.value,
    });
  } else {
    emit("update:modelValue", null);
  }
}

// ── Hydrate from saved config ─────────────────────────────────────────────────
watch(() => props.modelValue, async (cfg) => {
  if (cfg?.type !== "doctype") return;
  selectedDoctype.value = cfg.doctype || "";
  selectedField.value   = cfg.email_field || "";
  await loadFilterFields();
  if (cfg.filters && Object.keys(cfg.filters).length) {
    activeFilters.value = cfg.filters;
    filterRows.value = Object.entries(cfg.filters).map(([field, val]) => ({
      field,
      op:    Array.isArray(val) ? val[0] : "=",
      value: Array.isArray(val) ? val[1] : val,
    }));
  } else {
    activeFilters.value = {};
    filterRows.value    = [];
  }
}, { immediate: true });

onMounted(loadDoctypes);
</script>
