<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="$emit('close')"
    >
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-xl mx-4 flex flex-col max-h-[90vh]">

        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 class="text-base font-semibold text-gray-900">Send Campaign</h2>
            <p class="text-xs text-gray-400 mt-0.5">{{ campaignName }}</p>
          </div>
          <button class="text-gray-400 hover:text-gray-600 text-xl leading-none" @click="$emit('close')">✕</button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">

          <!-- Mode tabs -->
          <div class="flex gap-1 bg-gray-100 rounded-lg p-1">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              class="flex-1 text-xs font-medium py-1.5 rounded-md transition-colors"
              :class="mode === tab.id
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'"
              @click="mode = tab.id"
            >{{ tab.label }}</button>
          </div>

          <!-- ── Tab: Email Group ── -->
          <div v-if="mode === 'group'" class="space-y-4">
            <div v-if="loadingGroups" class="text-xs text-gray-400 py-2">Loading groups…</div>
            <div v-else-if="emailGroups.length === 0" class="rounded-lg border border-dashed border-gray-200 px-4 py-6 text-center">
              <p class="text-sm text-gray-500 font-medium">No Email Groups found</p>
              <p class="text-xs text-gray-400 mt-1">
                Create one in <strong>Frappe → Email Group</strong> to manage subscriber lists with unsubscribe support.
              </p>
            </div>
            <div v-else class="space-y-2">
              <label
                v-for="g in emailGroups"
                :key="g.name"
                class="flex items-center gap-3 px-4 py-3 rounded-lg border cursor-pointer transition-colors"
                :class="selectedGroup === g.name
                  ? 'border-gray-900 bg-gray-50'
                  : 'border-gray-200 hover:border-gray-300'"
              >
                <input type="radio" v-model="selectedGroup" :value="g.name" class="accent-gray-900" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-800">{{ g.title || g.name }}</p>
                  <p class="text-xs text-gray-400">{{ g.count }} active subscriber{{ g.count === 1 ? "" : "s" }}</p>
                </div>
                <span v-if="selectedGroup === g.name" class="text-xs text-gray-500 font-medium">Selected</span>
              </label>
            </div>
            <p class="text-xs text-gray-400">
              Unsubscribe links are added automatically for Email Group sends.
            </p>
          </div>

          <!-- ── Tab: Paste emails ── -->
          <div v-if="mode === 'paste'" class="space-y-3">
            <textarea
              v-model="pastedEmails"
              rows="6"
              placeholder="one@example.com&#10;two@example.com&#10;three@example.com"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-1 focus:ring-gray-400 resize-none font-mono"
            />
            <p class="text-xs text-gray-400">One email per line, or comma-separated.</p>
            <div v-if="parsedPasted.length > 0" class="text-xs text-gray-500 font-medium">
              {{ parsedPasted.length }} valid email{{ parsedPasted.length === 1 ? "" : "s" }} detected
            </div>
          </div>

          <!-- ── Tab: Pick from DocType ── -->
          <div v-if="mode === 'doctype'" class="space-y-3">
            <!-- DocType select -->
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">DocType</label>
              <select
                v-model="selectedDoctype"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-400 bg-white"
                @change="onDoctypeChange"
              >
                <option value="">— Select DocType —</option>
                <option v-for="dt in doctypes" :key="dt" :value="dt">{{ dt }}</option>
              </select>
            </div>

            <!-- Email field (only if multiple) -->
            <div v-if="emailFields.length > 1">
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">Email field</label>
              <select
                v-model="selectedField"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-400 bg-white"
                @change="loadRecords"
              >
                <option value="">— Select field —</option>
                <option v-for="f in emailFields" :key="f.fieldname" :value="f.fieldname">
                  {{ f.label }} ({{ f.fieldname }})
                </option>
              </select>
            </div>

            <!-- Search + records -->
            <div v-if="selectedDoctype && selectedField">
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">Pick recipients</label>
              <input
                v-model="search"
                type="text"
                placeholder="Search by email…"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-400 mb-2"
                @input="onSearch"
              />
              <div v-if="loadingRecords" class="text-xs text-gray-400 py-2">Loading…</div>
              <div v-else-if="records.length === 0" class="text-xs text-gray-400 py-2">No records found.</div>
              <div v-else class="border border-gray-100 rounded-lg overflow-hidden">
                <label class="flex items-center gap-3 px-3 py-2 bg-gray-50 border-b border-gray-100 cursor-pointer hover:bg-gray-100">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    :indeterminate.prop="someSelected && !allSelected"
                    class="rounded"
                    @change="toggleAll"
                  />
                  <span class="text-xs font-medium text-gray-600">Select all ({{ records.length }})</span>
                </label>
                <label
                  v-for="rec in records"
                  :key="rec.email"
                  class="flex items-center gap-3 px-3 py-2 border-b border-gray-50 last:border-0 cursor-pointer hover:bg-gray-50"
                >
                  <input type="checkbox" :value="rec.email" v-model="pickedEmails" class="rounded" />
                  <div class="min-w-0">
                    <p class="text-sm text-gray-800 truncate">{{ rec.label }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ rec.email }}</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <!-- Recipient summary -->
          <div v-if="recipientSummary" class="rounded-lg bg-gray-50 border border-gray-200 px-4 py-3">
            <p class="text-xs font-semibold text-gray-700">
              {{ recipientSummary }}
            </p>
          </div>

          <!-- Error -->
          <div v-if="sendError" class="bg-red-50 rounded-lg px-4 py-3 text-xs text-red-600">{{ sendError }}</div>

          <!-- Success -->
          <div v-if="sentCount" class="bg-green-50 rounded-lg px-4 py-3 text-xs text-green-700 font-medium">
            ✓ Queued for {{ sentCount }} recipient{{ sentCount === 1 ? "" : "s" }}. Campaign marked as Ready.
          </div>

        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between flex-shrink-0 gap-3">
          <p class="text-xs text-gray-400">Sent via your Frappe outgoing mail settings.</p>
          <Button
            variant="solid"
            :disabled="!canSend || sending"
            @click="send"
          >
            {{ sending ? "Sending…" : sendLabel }}
          </Button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { Button } from "frappe-ui";

const props = defineProps({
  campaignName: String,
  campaignDoc: Object,
});
const emit = defineEmits(["close", "sent"]);

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
    .split(/[\n,]/)
    .map((e) => e.trim().toLowerCase())
    .filter((e) => e.includes("@"))
);

// ── DocType picker ────────────────────────────────────────────────────────────
const doctypes        = ref([]);
const selectedDoctype = ref("");
const emailFields     = ref([]);
const selectedField   = ref("");
const search          = ref("");
const records         = ref([]);
const pickedEmails    = ref([]);
const loadingRecords  = ref(false);

const allSelected = computed(
  () => records.value.length > 0 && records.value.every((r) => pickedEmails.value.includes(r.email))
);
const someSelected = computed(() => pickedEmails.value.length > 0);

async function loadDoctypes() {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_doctypes_with_email_fields" });
    doctypes.value = res.message || [];
  } catch { /* paste still works */ }
}

async function onDoctypeChange() {
  selectedField.value = "";
  records.value = [];
  pickedEmails.value = [];
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
      await loadRecords();
    }
  } catch { emailFields.value = []; }
}

let searchTimer = null;
function onSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadRecords, 300);
}

async function loadRecords() {
  if (!selectedDoctype.value || !selectedField.value) return;
  loadingRecords.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_emails_from_doctype",
      args: { doctype: selectedDoctype.value, email_field: selectedField.value, search: search.value },
    });
    records.value = res.message || [];
  } catch { records.value = []; }
  finally { loadingRecords.value = false; }
}

function toggleAll() {
  if (allSelected.value) {
    const toRemove = new Set(records.value.map((r) => r.email));
    pickedEmails.value = pickedEmails.value.filter((e) => !toRemove.has(e));
  } else {
    const existing = new Set(pickedEmails.value);
    records.value.forEach((r) => existing.add(r.email));
    pickedEmails.value = [...existing];
  }
}

// ── Send state ────────────────────────────────────────────────────────────────
const sending   = ref(false);
const sendError = ref("");
const sentCount = ref(0);

const canSend = computed(() => {
  if (sentCount.value) return false;
  if (mode.value === "group")   return !!selectedGroup.value;
  if (mode.value === "paste")   return parsedPasted.value.length > 0;
  if (mode.value === "doctype") return pickedEmails.value.length > 0;
  return false;
});

const recipientSummary = computed(() => {
  if (mode.value === "group" && selectedGroup.value) {
    const g = emailGroups.value.find((x) => x.name === selectedGroup.value);
    return g ? `Sending to ${g.count} subscriber${g.count === 1 ? "" : "s"} in "${g.title || g.name}"` : null;
  }
  if (mode.value === "paste" && parsedPasted.value.length > 0) {
    return `${parsedPasted.value.length} recipient${parsedPasted.value.length === 1 ? "" : "s"} ready`;
  }
  if (mode.value === "doctype" && pickedEmails.value.length > 0) {
    return `${pickedEmails.value.length} recipient${pickedEmails.value.length === 1 ? "" : "s"} selected`;
  }
  return null;
});

const sendLabel = computed(() => {
  if (mode.value === "group" && selectedGroup.value) {
    const g = emailGroups.value.find((x) => x.name === selectedGroup.value);
    return g ? `Send to ${g.count}` : "Send";
  }
  if (mode.value === "paste")   return parsedPasted.value.length ? `Send to ${parsedPasted.value.length}` : "Send";
  if (mode.value === "doctype") return pickedEmails.value.length ? `Send to ${pickedEmails.value.length}` : "Send";
  return "Send";
});

async function send() {
  if (!canSend.value) return;
  sending.value = true;
  sendError.value = "";
  try {
    const args = { name: props.campaignDoc?.name };
    if (mode.value === "group") {
      args.email_group = selectedGroup.value;
    } else {
      const list = mode.value === "paste" ? parsedPasted.value : pickedEmails.value;
      args.recipients = JSON.stringify(list);
    }
    const res = await frappe.call({ method: "letters.letters.api.send_campaign", args });
    sentCount.value = res.message.count;
    emit("sent", res.message);
  } catch (e) {
    const raw = e?._server_messages;
    let msg = e?.message || "Send failed. Check your outgoing mail settings.";
    if (raw) {
      try { msg = JSON.parse(JSON.parse(raw)[0]).message || msg; } catch { /* keep msg */ }
    }
    sendError.value = msg;
  } finally {
    sending.value = false;
  }
}

onMounted(() => {
  loadEmailGroups();
  loadDoctypes();
});
</script>
