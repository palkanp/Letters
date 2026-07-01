<template>
  <div class="space-y-4">
    <div v-if="loading" class="text-xs text-ink-gray-5 py-6 text-center">Loading…</div>

    <!-- ── Inline notification form ── -->
    <div v-else-if="notifDoc" class="space-y-3">

      <!-- Header: enabled toggle -->
      <div class="flex items-center justify-end gap-3">
        <label class="flex items-center gap-2 cursor-pointer flex-shrink-0">
          <span class="text-sm text-ink-gray-7">Enabled</span>
          <input
            type="checkbox"
            class="accent-ink-gray-9 cursor-pointer"
            :checked="!!notifDoc.enabled"
            @change="onEnabledChange"
          />
        </label>
      </div>
      <div v-if="enableErrors.length" class="rounded-md bg-surface-red-1 border border-outline-red-2 px-3 py-2 space-y-0.5">
        <p v-for="err in enableErrors" :key="err" class="text-xs text-ink-red-4">{{ err }}</p>
      </div>

      <!-- Send Alert On + Document Type (left) | Sender + Sender Email (right) -->
      <div class="grid grid-cols-2 gap-2">
        <div class="min-w-0 space-y-2">
          <div>
            <span class="field-label">Send Alert On</span>
            <Select
              style="width:100%"
              :model-value="notifDoc.event || ''"
              :options="EVENT_OPTIONS"
              placeholder="Select event…"
              @update:model-value="(v) => setField('event', v)"
            />
          </div>
          <div>
            <span class="field-label">Document Type</span>
            <Autocomplete
              :model-value="doctypeValue"
              :options="doctypeOptions"
              :loading="loadingDoctypes"
              placeholder="Search DocType…"
              @update:model-value="(v) => setField('document_type', v?.value || '')"
            />
          </div>
        </div>
        <div class="min-w-0 space-y-2">
          <div>
            <span class="field-label">Sender</span>
            <Autocomplete
              :model-value="senderValue"
              :options="senderOptions"
              :loading="loadingSenders"
              placeholder="Default outgoing account"
              @update:model-value="(v) => setSender(v?.value || '')"
            />
          </div>
          <div v-if="notifDoc.sender_email">
            <span class="field-label">Sender Email</span>
            <TextInput :model-value="notifDoc.sender_email" :disabled="true" />
          </div>
        </div>
      </div>

      <!-- Days Before / Days After -->
      <template v-if="notifDoc.event === 'Days Before' || notifDoc.event === 'Days After'">
        <label class="block">
          <span class="field-label">Date Field</span>
          <TextInput
            :model-value="notifDoc.date_changed"
            placeholder="e.g. due_date"
            @update:model-value="(v) => setField('date_changed', v)"
          />
        </label>
        <label class="block">
          <span class="field-label">Days</span>
          <TextInput
            type="number"
            :model-value="notifDoc.days_in_advance"
            placeholder="0"
            @update:model-value="(v) => setField('days_in_advance', Number(v))"
          />
        </label>
      </template>

      <!-- Value Change -->
      <label v-else-if="notifDoc.event === 'Value Change'" class="block">
        <span class="field-label">Field to Monitor</span>
        <TextInput
          :model-value="notifDoc.value_changed"
          placeholder="e.g. status"
          @update:model-value="(v) => setField('value_changed', v)"
        />
      </label>

      <!-- Method -->
      <label v-else-if="notifDoc.event === 'Method'" class="block">
        <span class="field-label">Method Name</span>
        <TextInput
          :model-value="notifDoc.method"
          placeholder="e.g. before_submit"
          @update:model-value="(v) => setField('method', v)"
        />
      </label>

      <!-- Condition Type -->
      <div class="w-1/2 pr-1">
        <span class="field-label">Condition Type</span>
        <Select
          style="width:100%"
          :model-value="notifDoc.condition_type || 'Python'"
          :options="CONDITION_TYPE_OPTIONS"
          @update:model-value="(v) => setField('condition_type', v)"
        />
      </div>

      <!-- Condition (Python expression) -->
      <label v-if="!notifDoc.condition_type || notifDoc.condition_type === 'Python'" class="block">
        <span class="field-label">
          Condition
          <span class="ml-1 text-ink-gray-4 font-normal normal-case tracking-normal">(optional)</span>
        </span>
        <Textarea
          :model-value="notifDoc.condition"
          placeholder='e.g. doc.status == "Submitted"'
          :rows="3"
          class="font-mono text-xs"
          @update:model-value="(v) => setField('condition', v)"
        />
      </label>

      <!-- Filters editor -->
      <div v-else>
        <p v-if="!notifDoc.document_type" class="text-xs text-ink-gray-4 italic">
          Set a Document Type first to configure filters.
        </p>
        <div v-else ref="filterGroupEl" class="filter-group-wrapper" />
      </div>


      <!-- ── Recipients ── -->
      <div>
        <span class="field-label block mb-2">Recipients</span>
        <div class="rounded border border-outline-gray-2 overflow-hidden">
          <!-- Column headers -->
          <div class="grid grid-cols-[1fr_1fr_1fr_3rem] bg-surface-gray-1 border-b border-outline-gray-2 px-3 py-1.5">
            <span class="text-xs text-ink-gray-5 font-medium">By Role</span>
            <span class="text-xs text-ink-gray-5 font-medium">By Document Field</span>
            <span class="text-xs text-ink-gray-5 font-medium">CC</span>
            <span />
          </div>

          <!-- Rows -->
          <template v-for="(row, idx) in notifDoc.recipients" :key="row.name || idx">
            <!-- Summary row -->
            <div
              class="grid grid-cols-[1fr_1fr_1fr_3rem] border-b border-outline-gray-2 px-3 py-2 items-center"
              :class="editingIdx === idx ? 'bg-surface-gray-1' : ''"
            >
              <span class="text-xs text-ink-gray-7 truncate">{{ row.receiver_by_role || '—' }}</span>
              <span class="text-xs text-ink-gray-7 truncate">{{ row.receiver_by_document_field || '—' }}</span>
              <span class="text-xs text-ink-gray-7 truncate">{{ row.cc || '—' }}</span>
              <div class="flex items-center justify-end gap-1">
                <button
                  class="text-ink-gray-4 hover:text-ink-gray-7 transition-colors p-0.5"
                  @click="editingIdx = editingIdx === idx ? null : idx"
                >
                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
                <button
                  class="text-ink-gray-4 hover:text-red-500 transition-colors p-0.5"
                  @click="removeRecipient(idx)"
                >
                  <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>
                </button>
              </div>
            </div>

            <!-- Inline edit form -->
            <div
              v-if="editingIdx === idx"
              class="border-b border-outline-gray-2 bg-surface-gray-1 px-3 py-3"
            >
              <div class="grid grid-cols-2 gap-x-2 gap-y-2">
                <div class="min-w-0">
                  <span class="field-label">By Role</span>
                  <Select
                    style="width:100%"
                    :model-value="row.receiver_by_role || ''"
                    :options="[{ label: '—', value: '' }, ...roleOptions.map(r => ({ label: r, value: r }))]"
                    @update:model-value="(v) => { row.receiver_by_role = v; scheduleAutoSave() }"
                  />
                </div>
                <div class="min-w-0">
                  <span class="field-label">By Document Field</span>
                  <Select
                    style="width:100%"
                    :model-value="row.receiver_by_document_field || ''"
                    :options="[{ label: '—', value: '' }, ...receiverFieldOptions]"
                    @update:model-value="(v) => { row.receiver_by_document_field = v; scheduleAutoSave() }"
                  />
                </div>
                <div class="min-w-0">
                  <span class="field-label">CC</span>
                  <TextInput
                    :model-value="row.cc"
                    placeholder="email"
                    @update:model-value="(v) => { row.cc = v; scheduleAutoSave() }"
                  />
                </div>
                <div class="min-w-0">
                  <span class="field-label">BCC</span>
                  <TextInput
                    :model-value="row.bcc"
                    placeholder="email"
                    @update:model-value="(v) => { row.bcc = v; scheduleAutoSave() }"
                  />
                </div>
                <div class="min-w-0">
                  <span class="field-label">
                    Condition
                    <span class="ml-1 text-ink-gray-4 font-normal normal-case tracking-normal">(optional)</span>
                  </span>
                  <Textarea
                    :model-value="row.condition"
                    :rows="1"
                    class="font-mono text-xs"
                    @update:model-value="(v) => { row.condition = v; scheduleAutoSave() }"
                  />
                </div>
              </div>
            </div>
          </template>

          <!-- Empty state -->
          <div v-if="!notifDoc.recipients?.length" class="px-3 py-3 text-center text-xs text-ink-gray-4">
            No recipients
          </div>
        </div>

        <Button
          variant="ghost"
          size="sm"
          icon-left="lucide-plus"
          class="mt-1"
          @click="addRecipientRow"
        >
          Add Row
        </Button>
      </div>

      <!-- Footer: save status + open in desk -->
      <div class="flex items-center justify-between pt-2 border-t border-outline-gray-1">
        <span
          class="text-xs"
          :class="saving ? 'text-ink-gray-4' : savedFlash ? 'text-green-600' : 'text-ink-gray-3'"
        >
          {{ saving ? 'Saving…' : savedFlash ? 'Saved' : 'Auto-saves on change' }}
        </span>
        <Button
          variant="ghost"
          size="sm"
          icon-left="lucide-external-link"
          @click="openInDesk"
        >
          Open in Desk
        </Button>
      </div>
    </div>

    <!-- ── Empty state ── -->
    <div v-else class="rounded border border-dashed border-outline-gray-2 px-4 py-10 text-center">
      <span class="lucide-bell size-6 text-ink-gray-4 mx-auto mb-2 block" aria-hidden="true" />
      <p class="text-sm text-ink-gray-6 font-medium">No notification linked</p>
      <p class="text-xs text-ink-gray-5 mt-1 mb-4 leading-relaxed">
        Create a Frappe Notification that uses this Letter as its email body.
      </p>
      <Button
        size="sm"
        label="Create Notification"
        :loading="creating"
        @click="createNotification"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, watch } from "vue";
import { Button, TextInput, Select, Textarea, Autocomplete, toast } from "frappe-ui";

const EVENT_OPTIONS = [
  { label: "New", value: "New" },
  { label: "Save", value: "Save" },
  { label: "Submit", value: "Submit" },
  { label: "Cancel", value: "Cancel" },
  { label: "Days Before", value: "Days Before" },
  { label: "Days After", value: "Days After" },
  { label: "Value Change", value: "Value Change" },
  { label: "Method", value: "Method" },
  { label: "Custom", value: "Custom" },
];

const CONDITION_TYPE_OPTIONS = [
  { label: "Python Expression", value: "Python" },
  { label: "Filters", value: "Filters" },
];

const props = defineProps({
  letterDoc: { type: Object, default: null },
});

const loading    = ref(false);
const creating   = ref(false);
const saving     = ref(false);
const savedFlash = ref(false);
let _savedFlashTimer = null;
let _autoSaveTimer   = null;

const notifDoc = ref(null);
const enableErrors = ref([]);

const doctypeOptions  = ref([]);
const loadingDoctypes = ref(false);
const doctypeValue    = computed(() => {
  const v = notifDoc.value?.document_type;
  return v ? { label: v, value: v } : null;
});

const senderOptions  = ref([]);
const loadingSenders = ref(false);
const senderValue    = computed(() => {
  const v = notifDoc.value?.sender;
  return v ? { label: v, value: v } : null;
});

const roleOptions          = ref([]);
const receiverFieldOptions = ref([]);
const editingIdx           = ref(null);

const filterGroupEl = ref(null);
let _filterGroup    = null;
let _filterGeneration = 0;

// ── Filter group ──────────────────────────────────────────────────────────────

function initFilterGroup() {
  if (!filterGroupEl.value || !notifDoc.value?.document_type) return;
  const $parent = $(filterGroupEl.value);
  $parent.empty();
  _filterGroup = null;
  const gen = ++_filterGeneration;
  const existing = notifDoc.value.filters && notifDoc.value.filters !== "[]"
    ? JSON.parse(notifDoc.value.filters)
    : [];
  frappe.model.with_doctype(notifDoc.value.document_type, () => {
    if (gen !== _filterGeneration) return;
    _filterGroup = new frappe.ui.FilterGroup({
      parent: $parent,
      doctype: notifDoc.value.document_type,
      on_change: () => {
        if (!notifDoc.value) return;
        notifDoc.value.filters = JSON.stringify(_filterGroup.get_filters());
        scheduleAutoSave();
      },
    });
    _filterGroup.add_filters_to_filter_group(existing);
  });
}

watch(() => notifDoc.value?.document_type, (dt) => loadReceiverFields(dt));

watch(
  () => [notifDoc.value?.condition_type, notifDoc.value?.document_type],
  ([condType, docType]) => {
    if (condType === "Filters" && docType) {
      nextTick(initFilterGroup);
    } else {
      _filterGroup = null;
    }
  },
);

// ── Data loaders ─────────────────────────────────────────────────────────────

async function loadRoles() {
  if (roleOptions.value.length) return;
  try {
    const res = await frappe.call({
      method: "frappe.client.get_list",
      args: { doctype: "Role", fields: ["name"], filters: { disabled: 0 }, limit_page_length: 200, order_by: "name asc" },
    });
    roleOptions.value = (res.message || []).map((r) => r.name);
  } catch { /* ignore */ }
}

function loadReceiverFields(doctype) {
  if (!doctype) { receiverFieldOptions.value = []; return; }
  frappe.model.with_doctype(doctype, () => {
    const fields = frappe.get_doc("DocType", doctype).fields || [];
    const TABLE_TYPES = ["Table", "Table MultiSelect"];
    const opts = [{ label: "owner", value: "owner" }];
    for (const df of fields) {
      if (TABLE_TYPES.includes(df.fieldtype)) {
        const child = frappe.get_doc("DocType", df.options);
        if (!child) continue;
        for (const cdf of child.fields || []) {
          if (isReceiverField(cdf)) {
            opts.push({ label: `${df.fieldname} > ${cdf.fieldname}`, value: `${cdf.fieldname},${df.fieldname}` });
          }
        }
      } else if (isReceiverField(df)) {
        opts.push({ label: df.fieldname, value: df.fieldname });
      }
    }
    receiverFieldOptions.value = opts;
  });
}

function isReceiverField(df) {
  return (df.fieldtype === "Link" && (df.options === "User" || df.options === "Customer")) ||
         df.options === "Email";
}

async function loadDoctypes() {
  if (doctypeOptions.value.length) return;
  loadingDoctypes.value = true;
  try {
    const res = await frappe.call({
      method: "frappe.client.get_list",
      args: { doctype: "DocType", fields: ["name"], limit_page_length: 500, order_by: "name asc" },
    });
    doctypeOptions.value = (res.message || []).map((d) => ({ label: d.name, value: d.name }));
  } catch {
    // ignore
  } finally {
    loadingDoctypes.value = false;
  }
}

async function loadSenders() {
  if (senderOptions.value.length) return;
  loadingSenders.value = true;
  try {
    const res = await frappe.call({
      method: "frappe.client.get_list",
      args: { doctype: "Email Account", filters: { enable_outgoing: 1 }, fields: ["name", "email_id"], limit_page_length: 100 },
    });
    senderOptions.value = (res.message || []).map((a) => ({ label: a.name, value: a.name, description: a.email_id }));
  } catch {
    // ignore
  } finally {
    loadingSenders.value = false;
  }
}

async function load() {
  if (!props.letterDoc?.name) return;
  loading.value = true;
  loadDoctypes();
  loadSenders();
  loadRoles();
  try {
    const res = await frappe.call({
      method: "letters.letters.api.notifications.get_notification_for_letter",
      args: { letter: props.letterDoc.name },
    });
    const info = res.message;
    if (!info?.name) { notifDoc.value = null; return; }

    const full = await frappe.call({
      method: "letters.letters.api.notifications.get_notification_detail",
      args: { notification: info.name },
    });
    const doc = full.message;
    if (Array.isArray(doc?.recipients)) {
      doc.recipients = doc.recipients.map((r) => ({
        name: r.name || "",
        receiver_by_role: r.receiver_by_role || "",
        receiver_by_document_field: r.receiver_by_document_field || "",
        cc: r.cc || "",
        bcc: r.bcc || "",
        condition: r.condition || "",
      }));
    }
    notifDoc.value = doc;
    if (notifDoc.value?.document_type) loadReceiverFields(notifDoc.value.document_type);
  } catch {
    notifDoc.value = null;
  } finally {
    loading.value = false;
  }
}

// ── Field updates ─────────────────────────────────────────────────────────────

function validateForEnable() {
  const errors = [];
  if (!notifDoc.value.event) errors.push("Send Alert On is required.");
  if (!notifDoc.value.document_type) errors.push("Document Type is required.");
  const hasRecipient = notifDoc.value.recipients?.some(r =>
    r.receiver_by_role?.trim() || r.receiver_by_document_field?.trim() || r.cc?.trim()
  );
  if (!hasRecipient) errors.push("At least one recipient is required.");
  enableErrors.value = errors;
  return errors.length === 0;
}

function onEnabledChange(e) {
  if (e.target.checked && !validateForEnable()) {
    e.target.checked = false;
    return;
  }
  enableErrors.value = [];
  setField("enabled", e.target.checked ? 1 : 0);
}

function setField(field, value) {
  if (!notifDoc.value) return;
  enableErrors.value = [];
  notifDoc.value[field] = value;
  if (field === "condition_type") {
    if (value === "Filters") {
      notifDoc.value.condition = "";
    } else {
      notifDoc.value.filters = "";
      _filterGroup = null;
    }
  }
  scheduleAutoSave();
}

async function setSender(name) {
  if (!notifDoc.value) return;
  notifDoc.value.sender = name;
  if (!name) {
    notifDoc.value.sender_email = "";
  } else {
    try {
      const res = await frappe.call({
        method: "frappe.client.get_value",
        args: { doctype: "Email Account", filters: name, fieldname: "email_id" },
      });
      notifDoc.value.sender_email = res.message?.email_id || "";
    } catch {
      notifDoc.value.sender_email = "";
    }
  }
  scheduleAutoSave();
}

function addRecipientRow() {
  if (!notifDoc.value) return;
  if (!notifDoc.value.recipients) notifDoc.value.recipients = [];
  notifDoc.value.recipients.push({ receiver_by_role: "", receiver_by_document_field: "", cc: "", bcc: "", condition: "" });
  editingIdx.value = notifDoc.value.recipients.length - 1;
  scheduleAutoSave();
}

function removeRecipient(idx) {
  notifDoc.value.recipients.splice(idx, 1);
  if (editingIdx.value === idx) editingIdx.value = null;
  else if (editingIdx.value > idx) editingIdx.value--;
  scheduleAutoSave();
}

// ── Save ──────────────────────────────────────────────────────────────────────

function scheduleAutoSave() {
  clearTimeout(_autoSaveTimer);
  _autoSaveTimer = setTimeout(saveNotification, 800);
}

async function saveNotification() {
  if (!notifDoc.value?.name) return;
  saving.value = true;
  try {
    await frappe.call({
      method: "letters.letters.api.notifications.save_notification_fields",
      args: {
        notification: notifDoc.value.name,
        fields: JSON.stringify({
          enabled:         notifDoc.value.enabled,
          document_type:   notifDoc.value.document_type,
          event:           notifDoc.value.event,
          condition_type:  notifDoc.value.condition_type,
          condition:       notifDoc.value.condition,
          filters:         notifDoc.value.filters,
          sender:          notifDoc.value.sender,
          sender_email:    notifDoc.value.sender_email,
          date_changed:    notifDoc.value.date_changed,
          days_in_advance: notifDoc.value.days_in_advance,
          value_changed:   notifDoc.value.value_changed,
          method:          notifDoc.value.method,
          recipients:      notifDoc.value.recipients || [],
        }),
      },
    });
    clearTimeout(_savedFlashTimer);
    savedFlash.value = true;
    _savedFlashTimer = setTimeout(() => { savedFlash.value = false; }, 2000);
  } catch (e) {
    toast.error(e.message || "Could not save notification.");
  } finally {
    saving.value = false;
  }
}

// ── Notification creation ─────────────────────────────────────────────────────

async function createNotification() {
  if (!props.letterDoc?.subject?.trim()) {
    toast.error("Set a subject line in the Details tab before creating a notification.");
    return;
  }
  creating.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.notifications.create_notification_for_letter",
      args: { letter: props.letterDoc.name },
    });
    const full = await frappe.call({
      method: "letters.letters.api.notifications.get_notification_detail",
      args: { notification: res.message.name },
    });
    notifDoc.value = full.message;
  } catch {
    toast.error("Couldn't create notification.");
  } finally {
    creating.value = false;
  }
}

function openInDesk() {
  if (notifDoc.value?.name) {
    window.open(`/app/notification/${encodeURIComponent(notifDoc.value.name)}`, "_blank");
  }
}

onMounted(load);
watch(() => props.letterDoc?.name, load);
watch(() => props.letterDoc?.subject, (newSubject) => {
  if (notifDoc.value && newSubject !== undefined) {
    notifDoc.value.subject = newSubject;
  }
});
</script>

<style scoped>
.field-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ink-gray-6);
  margin-bottom: 0.25rem;
}

.recipient-cell {
  width: 100%;
  background: transparent;
  font-size: 0.75rem;
  color: var(--ink-gray-8);
  outline: none;
  border: none;
  padding: 0 0.25rem;
}

.recipient-cell::placeholder {
  color: var(--ink-gray-3);
}

.recipient-cell:focus {
  background: var(--surface-gray-1);
  border-radius: 0.25rem;
}

.recipient-select {
  width: 100%;
}
</style>
