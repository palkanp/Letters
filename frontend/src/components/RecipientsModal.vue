<template>
  <Dialog
    :model-value="true"
    title="Select Recipients"
    :message="campaignName"
    size="xl"
    @update:model-value="(v) => { if (!v) $emit('close') }"
  >
    <template #default>
      <div class="space-y-5">

          <!-- Mode tabs -->
          <TabButtons
            :buttons="tabs.map(t => ({ label: t.label, value: t.id }))"
            v-model="mode"
          />

          <!-- ── Tab: Email Group ── -->
          <div v-if="mode === 'group'" class="space-y-4">
            <div v-if="loadingGroups" class="text-xs text-gray-400 py-2">Loading groups…</div>
            <div v-else-if="emailGroups.length === 0" class="rounded-lg border border-dashed border-gray-200 px-4 py-6 text-center">
              <p class="text-sm text-gray-500 font-medium">No Email Groups found</p>
              <p class="text-xs text-gray-400 mt-1">
                Create one via <strong>Email Group</strong> in Frappe to manage subscribers with unsubscribe support.
              </p>
            </div>
            <div v-else class="space-y-2">
              <label
                v-for="g in emailGroups"
                :key="g.name"
                class="flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-colors"
                :class="selectedGroup === g.name ? 'border-gray-900 bg-gray-50' : 'border-gray-200 hover:border-gray-300'"
              >
                <input type="radio" v-model="selectedGroup" :value="g.name" class="accent-gray-900" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-800">{{ g.title || g.name }}</p>
                  <p class="text-xs text-gray-400">{{ g.count }} active subscriber{{ g.count === 1 ? "" : "s" }}</p>
                </div>
                <span v-if="selectedGroup === g.name" class="text-xs text-gray-500 font-medium">Selected</span>
              </label>
            </div>
            <p class="text-xs text-gray-400">Unsubscribe links are added automatically for Email Group sends.</p>
          </div>

          <!-- ── Tab: Paste emails ── -->
          <div v-if="mode === 'paste'" class="space-y-3">
            <Textarea
              v-model="pastedEmails"
              :rows="6"
              placeholder="one@example.com&#10;two@example.com&#10;three@example.com"
              size="sm"
            />
            <p class="text-xs text-gray-400">One email per line, or comma- or semicolon-separated.</p>
            <div v-if="parsedPasted.length > 0" class="text-xs text-gray-500 font-medium">
              {{ parsedPasted.length }} valid email{{ parsedPasted.length === 1 ? "" : "s" }} detected
            </div>
          </div>

          <!-- ── Tab: From DocType ── -->
          <div v-if="mode === 'doctype'" class="space-y-4">
            <!-- DocType select -->
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">DocType</label>
              <Select
                v-model="selectedDoctype"
                :options="doctypes"
                placeholder="Select DocType"
                size="sm"
                @update:modelValue="onDoctypeChange"
              />
            </div>

            <!-- Email field (shown when doctype is selected) -->
            <div v-if="emailFields.length > 1">
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">Email Field</label>
              <Select
                v-model="selectedField"
                :options="emailFields.map(f => ({ label: `${f.label} (${f.fieldname})`, value: f.fieldname }))"
                placeholder="Select field"
                size="sm"
                @update:modelValue="onFieldChange"
              />
            </div>

            <!-- Filters (shown once doctype + field selected) -->
            <div v-if="selectedDoctype && selectedField && filterFields.length" class="space-y-3">
              <p class="text-xs font-semibold text-gray-600 uppercase tracking-wide">Filters <span class="font-normal normal-case text-gray-400">(optional — leave blank to include all)</span></p>

              <div v-for="ff in filterFields" :key="ff.fieldname" class="flex items-center gap-3">
                <label class="w-32 flex-shrink-0 text-xs text-gray-600 font-medium truncate" :title="ff.label">{{ ff.label }}</label>

                <!-- Select field -->
                <Select
                  v-if="ff.fieldtype === 'Select'"
                  class="flex-1"
                  size="sm"
                  :model-value="activeFilters[ff.fieldname] || ''"
                  :options="[{ label: '— Any —', value: '' }, ...ff.options.map(o => ({ label: o, value: o }))]"
                  @update:model-value="setFilter(ff.fieldname, $event)"
                />

                <!-- Date/Datetime -->
                <DatePicker
                  v-else-if="ff.fieldtype === 'Date' || ff.fieldtype === 'Datetime'"
                  class="flex-1"
                  size="sm"
                  placeholder="On or after…"
                  :model-value="activeFilters[ff.fieldname] ? activeFilters[ff.fieldname][1] : ''"
                  @update:model-value="setDateFilter(ff.fieldname, $event)"
                />

                <!-- Link field — free text for now -->
                <TextInput
                  v-else
                  class="flex-1"
                  size="sm"
                  type="text"
                  :placeholder="`Filter by ${ff.label}…`"
                  :model-value="activeFilters[ff.fieldname] || ''"
                  @update:model-value="setFilter(ff.fieldname, $event)"
                />

                <!-- Clear filter -->
                <button
                  v-if="activeFilters[ff.fieldname] !== undefined && activeFilters[ff.fieldname] !== ''"
                  type="button"
                  class="text-gray-300 hover:text-red-400"
                  @click="clearFilter(ff.fieldname)"
                ><FeatherIcon name="x" class="w-3.5 h-3.5" /></button>
              </div>

              <!-- Preview count -->
              <div class="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  class="text-xs text-blue-600 hover:underline"
                  :disabled="countLoading"
                  @click="previewCount"
                >{{ countLoading ? "Counting…" : "Preview recipient count" }}</button>
                <span v-if="recipientCount !== null" class="text-xs text-gray-600 font-medium">
                  → {{ recipientCount }} recipient{{ recipientCount === 1 ? "" : "s" }}
                </span>
              </div>
            </div>

            <p v-if="selectedDoctype && selectedField && !filterFields.length && !loadingFilters" class="text-xs text-gray-400">
              No filterable fields found for this DocType.
            </p>
          </div>

      </div>
    </template>

    <template #actions>
      <div class="flex items-center justify-between gap-3 w-full">
        <p class="text-xs text-ink-gray-5">
          <template v-if="summaryText">{{ summaryText }}</template>
          <template v-else>Configure who will receive this campaign.</template>
        </p>
        <Button
          variant="solid"
          :disabled="!canConfirm"
          @click="confirm"
        >Save recipients</Button>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { Dialog, Button, TabButtons, Textarea, Select, DatePicker, TextInput, FeatherIcon } from "frappe-ui";

const props = defineProps({ campaignName: String, campaignDoc: Object });
const emit  = defineEmits(["close", "saved"]);

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

// ── Summary / canConfirm ──────────────────────────────────────────────────────
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

const canConfirm = computed(() => {
  if (mode.value === "group")   return !!selectedGroup.value;
  if (mode.value === "paste")   return parsedPasted.value.length > 0;
  if (mode.value === "doctype") return !!(selectedDoctype.value && selectedField.value);
  return false;
});

// ── Confirm (emit recipient config back to BuilderPage) ───────────────────────
function confirm() {
  if (!canConfirm.value) return;
  let config;
  if (mode.value === "group") {
    config = { type: "group", email_group: selectedGroup.value };
  } else if (mode.value === "paste") {
    config = { type: "paste", recipients: parsedPasted.value };
  } else {
    config = {
      type: "doctype",
      doctype: selectedDoctype.value,
      email_field: selectedField.value,
      filters: activeFilters.value,
    };
  }
  emit("saved", config);
}

onMounted(() => {
  loadEmailGroups();
  loadDoctypes();
});
</script>
