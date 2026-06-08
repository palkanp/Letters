<template>
  <!-- Backdrop -->
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
          <button
            class="text-gray-400 hover:text-gray-600 text-xl leading-none"
            @click="$emit('close')"
          >✕</button>
        </div>

        <!-- Body -->
        <div class="flex-1 overflow-y-auto px-6 py-5 space-y-6">

          <!-- Section 1: Paste emails -->
          <div>
            <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
              Type or paste emails
            </label>
            <textarea
              v-model="pastedEmails"
              rows="4"
              placeholder="one@example.com&#10;two@example.com&#10;three@example.com"
              class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none font-mono"
            />
            <p class="text-xs text-gray-400 mt-1">One email per line, or comma-separated.</p>
          </div>

          <!-- Divider -->
          <div class="flex items-center gap-3">
            <div class="flex-1 h-px bg-gray-100" />
            <span class="text-xs text-gray-400 font-medium">or pick from your data</span>
            <div class="flex-1 h-px bg-gray-100" />
          </div>

          <!-- Section 2: DocType picker -->
          <div class="space-y-3">
            <!-- Step 1: DocType -->
            <div>
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                1. Choose a DocType
              </label>
              <select
                v-model="selectedDoctype"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                @change="onDoctypeChange"
              >
                <option value="">— Select DocType —</option>
                <option v-for="dt in doctypes" :key="dt" :value="dt">{{ dt }}</option>
              </select>
            </div>

            <!-- Step 2: Email field (only if doctype chosen and has multiple email fields) -->
            <div v-if="emailFields.length > 1">
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                2. Choose email field
              </label>
              <select
                v-model="selectedField"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                @change="loadRecords"
              >
                <option value="">— Select field —</option>
                <option v-for="f in emailFields" :key="f.fieldname" :value="f.fieldname">
                  {{ f.label }} ({{ f.fieldname }})
                </option>
              </select>
            </div>

            <!-- Step 3: Search + record list -->
            <div v-if="selectedDoctype && selectedField">
              <label class="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">
                {{ emailFields.length > 1 ? "3." : "2." }} Pick recipients
              </label>
              <input
                v-model="search"
                type="text"
                placeholder="Search by email…"
                class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2"
                @input="onSearch"
              />

              <div v-if="loadingRecords" class="text-xs text-gray-400 py-2">Loading…</div>
              <div v-else-if="records.length === 0" class="text-xs text-gray-400 py-2">No records found.</div>
              <div v-else class="border border-gray-100 rounded-lg overflow-hidden">
                <!-- Select all -->
                <label class="flex items-center gap-3 px-3 py-2 bg-gray-50 border-b border-gray-100 cursor-pointer hover:bg-gray-100">
                  <input
                    type="checkbox"
                    :checked="allSelected"
                    :indeterminate="someSelected && !allSelected"
                    class="rounded"
                    @change="toggleAll"
                  />
                  <span class="text-xs font-medium text-gray-600">Select all ({{ records.length }})</span>
                </label>
                <!-- Records -->
                <label
                  v-for="rec in records"
                  :key="rec.email"
                  class="flex items-center gap-3 px-3 py-2 border-b border-gray-50 last:border-0 cursor-pointer hover:bg-blue-50"
                >
                  <input
                    type="checkbox"
                    :value="rec.email"
                    v-model="pickedEmails"
                    class="rounded"
                  />
                  <div class="min-w-0">
                    <p class="text-sm text-gray-800 truncate">{{ rec.label }}</p>
                    <p class="text-xs text-gray-400 truncate">{{ rec.email }}</p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          <!-- Combined recipient preview -->
          <div v-if="allRecipients.length > 0" class="bg-blue-50 rounded-lg px-4 py-3">
            <p class="text-xs font-semibold text-blue-700 mb-1">
              Ready to send to {{ allRecipients.length }} recipient{{ allRecipients.length === 1 ? "" : "s" }}
            </p>
            <p class="text-xs text-blue-500 truncate">{{ allRecipients.slice(0, 5).join(", ") }}{{ allRecipients.length > 5 ? ` +${allRecipients.length - 5} more` : "" }}</p>
          </div>

          <!-- Error -->
          <div v-if="sendError" class="bg-red-50 rounded-lg px-4 py-3 text-xs text-red-600">
            {{ sendError }}
          </div>

          <!-- Success -->
          <div v-if="sentCount" class="bg-green-50 rounded-lg px-4 py-3 text-xs text-green-700 font-medium">
            Sent to {{ sentCount }} recipient{{ sentCount === 1 ? "" : "s" }}. Campaign marked as Ready.
          </div>

        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-between flex-shrink-0 gap-3">
          <p class="text-xs text-gray-400">
            Emails are sent via your Frappe outgoing mail settings.
          </p>
          <button
            class="flex-shrink-0 px-5 py-2 rounded-lg text-sm font-semibold transition-colors"
            :class="canSend
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
            :disabled="!canSend || sending"
            @click="send"
          >
            {{ sending ? "Sending…" : `Send to ${allRecipients.length}` }}
          </button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";

const props = defineProps({
  campaignName: String,
  campaignDoc: Object,
});
const emit = defineEmits(["close", "sent"]);

// Paste section
const pastedEmails = ref("");

// Picker section
const doctypes = ref([]);
const selectedDoctype = ref("");
const emailFields = ref([]);
const selectedField = ref("");
const search = ref("");
const records = ref([]);
const pickedEmails = ref([]);
const loadingRecords = ref(false);

// Send state
const sending = ref(false);
const sendError = ref("");
const sentCount = ref(0);

// Parse pasted emails (comma or newline separated)
const parsedPasted = computed(() => {
  return pastedEmails.value
    .split(/[\n,]/)
    .map((e) => e.trim().toLowerCase())
    .filter((e) => e.includes("@"));
});

// All unique recipients from both sources
const allRecipients = computed(() => {
  const set = new Set([...parsedPasted.value, ...pickedEmails.value]);
  return [...set];
});

const canSend = computed(() => allRecipients.value.length > 0 && !sentCount.value);

const allSelected = computed(
  () => records.value.length > 0 && records.value.every((r) => pickedEmails.value.includes(r.email))
);
const someSelected = computed(() => pickedEmails.value.length > 0);

onMounted(loadDoctypes);

async function loadDoctypes() {
  try {
    const res = await frappe.call({ method: "letters.letters.api.get_doctypes_with_email_fields" });
    doctypes.value = res.message || [];
  } catch {
    // picker unavailable — user can still paste
  }
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
    // Auto-select if only one email field
    if (emailFields.value.length === 1) {
      selectedField.value = emailFields.value[0].fieldname;
      await loadRecords();
    }
  } catch {
    emailFields.value = [];
  }
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
      args: {
        doctype: selectedDoctype.value,
        email_field: selectedField.value,
        search: search.value,
      },
    });
    records.value = res.message || [];
  } catch {
    records.value = [];
  } finally {
    loadingRecords.value = false;
  }
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

async function send() {
  if (!canSend.value) return;
  sending.value = true;
  sendError.value = "";
  try {
    const res = await frappe.call({
      method: "letters.letters.api.send_campaign",
      args: {
        name: props.campaignDoc?.name,
        recipients: JSON.stringify(allRecipients.value),
      },
    });
    sentCount.value = res.message.count;
    emit("sent", res.message);
  } catch (e) {
    const msg =
      e?._server_messages?.length
        ? JSON.parse(e._server_messages)[0]
        : e?.message || "Send failed. Check your outgoing mail settings.";
    sendError.value = msg;
  } finally {
    sending.value = false;
  }
}
</script>
