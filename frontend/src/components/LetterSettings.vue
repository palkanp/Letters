<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[100] flex items-center justify-center px-4 py-4 bg-black-overlay-200 dark:bg-black-overlay-700"
        @keydown.esc="isOpen = false"
      >
        <Transition
          enter-active-class="transition duration-100 ease-out"
          enter-from-class="opacity-50 scale-[0.98]"
          enter-to-class="opacity-100 scale-100"
          leave-active-class="transition duration-150 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-50 scale-[0.98]"
        >
          <div
            v-if="isOpen"
            class="relative w-full max-w-3xl rounded-xl bg-surface-base shadow-xl overflow-hidden"
          >
            <!-- Header -->
            <div class="flex items-center justify-between px-8 pt-4 pb-0">
              <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">Settings</h3>
              <Button variant="ghost" icon="lucide-x" aria-label="Close" @click="isOpen = false" />
            </div>

            <!-- Tab bar -->
            <div class="flex gap-5 px-8 mt-3 border-b border-outline-gray-2">
              <button
                v-for="s in sections"
                :key="s.id"
                class="relative py-2.5 text-base transition-colors duration-200"
                :class="activeTab === s.id ? 'text-ink-gray-9' : 'text-ink-gray-5 hover:text-ink-gray-9'"
                @click="activeTab = s.id"
              >
                {{ s.label }}
                <span
                  v-if="activeTab === s.id"
                  class="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-surface-gray-7 translate-y-px"
                />
              </button>
            </div>

            <!-- Tab content -->
            <div class="h-[55vh] overflow-y-auto px-8 pt-4 pb-5">

              <!-- ── Details ── -->
              <div v-if="activeTab === 'details'" class="space-y-4">
                <label class="block">
                  <span class="block text-xs font-semibold text-ink-gray-6  mb-1.5">Letter Name</span>
                  <TextInput
                    :model-value="letterName"
                    placeholder="e.g. June Newsletter"
                    @update:model-value="(v) => emit('update:letterName', v)"
                  />
                </label>
                <label class="block">
                  <span class="flex items-center justify-between mb-1.5">
                    <span class="text-xs font-semibold text-ink-gray-6 ">Subject Line <span class="text-red-400 ml-0.5">*</span></span>
                    <span class="text-xs tabular-nums" :class="subject.length > 78 ? 'text-red-500' : subject.length > 60 ? 'text-orange-500' : 'text-ink-gray-4'">{{ subject.length }}</span>
                  </span>
                  <TextInput
                    ref="subjectInputRef"
                    :model-value="subject"
                    placeholder="e.g. Your June update is here"
                    @update:model-value="(v) => emit('update:subject', v)"
                    @click="trackSubjectCursor"
                    @keyup="trackSubjectCursor"
                  />
                  <p v-if="subject.length > 78" class="mt-1 text-xs text-red-500">Most email clients truncate subjects over 78 characters.</p>
                  <p v-else-if="subject.length > 60" class="mt-1 text-xs text-orange-500">Over 60 characters may be clipped on mobile.</p>

                  <div v-if="isNotification" class="mt-1.5 flex items-center gap-2 flex-wrap">
                    <p class="text-xs text-ink-gray-4">
                      Supports Jinja tags, e.g. {{ jinjaTagExample }}.
                    </p>
                    <div class="relative">
                      <Button
                        variant="ghost"
                        size="sm"
                        icon-left="lucide-braces"
                        @click="toggleFieldPicker"
                      >
                        Insert field
                      </Button>
                      <div
                        v-if="showFieldPicker"
                        class="absolute z-10 mt-1 w-56 max-h-56 overflow-y-auto rounded-lg border border-outline-gray-2 bg-surface-base shadow-lg py-1"
                      >
                        <p v-if="loadingMergeFields" class="px-3 py-2 text-xs text-ink-gray-4">Loading fields…</p>
                        <p v-else-if="!mergeFields.length" class="px-3 py-2 text-xs text-ink-gray-4">
                          Set a Document Type on the Notification to see available fields.
                        </p>
                        <button
                          v-for="f in mergeFields"
                          :key="f.fieldname"
                          class="w-full text-left px-3 py-1.5 text-xs text-ink-gray-7 hover:bg-surface-gray-2"
                          @click="insertMergeField(f.fieldname)"
                        >
                          {{ f.label }}
                          <span class="text-ink-gray-4 font-mono ml-1">doc.{{ f.fieldname }}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </label>

                <label class="block">
                  <span class="block text-xs font-semibold text-ink-gray-6  mb-1.5">Preview Text</span>
                  <TextInput
                    :model-value="previewText"
                    placeholder="Brief teaser shown after subject line"
                    @update:model-value="(v) => emit('update:previewText', v)"
                  />
                </label>

                <div class="border-t border-outline-gray-1 pt-4 space-y-4">
                  <label class="block">
                    <span class="block text-xs font-semibold text-ink-gray-6 mb-1.5">Sender Name</span>
                    <TextInput
                      :model-value="localSenderName"
                      placeholder="e.g. Acme Team"
                      @update:model-value="localSenderName = $event"
                      @focusout="commitSenderName"
                      @keydown.enter.prevent="commitSenderName"
                    />
                  </label>
                  <label class="block">
                    <span class="block text-xs font-semibold text-ink-gray-6 mb-1.5">Sender Email</span>
                    <TextInput
                      :model-value="localSenderEmail"
                      placeholder="Leave blank to use system default"
                      @update:model-value="localSenderEmail = $event"
                      @focusout="commitSenderEmail"
                      @keydown.enter.prevent="commitSenderEmail"
                    />
                    <p class="mt-1.5 text-xs text-ink-gray-4">Must match a configured outgoing Email Account in Frappe. The sender name is used as the display name for that account.</p>
                  </label>
                </div>

                <div v-if="!isNotification" class="border-t border-outline-gray-1 pt-4">
                  <label class="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      class="mt-0.5 accent-ink-gray-9"
                      :checked="includeUnsubscribe"
                      @change="emit('update:includeUnsubscribe', $event.target.checked)"
                    />
                    <div>
                      <p class="text-sm font-medium text-ink-gray-8">Include unsubscribe link</p>
                      <p class="text-xs text-ink-gray-4 mt-0.5">For email group sends, Frappe handles opt-outs per group. For DocType / pasted-address sends, recipients unsubscribe from specific Letter Categories or all emails.</p>
                    </div>
                  </label>
                </div>
              </div>

              <!-- ── Recipients ── -->
              <div v-else-if="activeTab === 'recipients'" class="space-y-4">
                <!-- After sending: expandable source rows -->
                <div v-if="isSent">
                  <div v-if="loadingRecipients" class="text-xs text-ink-gray-5 py-6 text-center">Loading…</div>
                  <div v-else class="rounded-lg border border-outline-gray-1 divide-y divide-outline-gray-1">

                    <div v-for="(src, i) in audienceSources" :key="i">

                      <button
                        class="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-surface-gray-1 transition-colors text-left"
                        @click="toggleSource(i)"
                      >
                        <div class="flex-1 min-w-0">
                          <p class="text-xs font-medium text-ink-gray-7">
                            <a
                              v-if="src.externalLink"
                              :href="src.externalLink"
                              target="_blank"
                              class="text-ink-blue-4 hover:underline"
                              @click.stop
                            >{{ src.title }}</a>
                            <template v-else>{{ src.title }}</template>
                            <span class="font-normal text-ink-gray-4 ml-1">({{ src.subset.length }})</span>
                          </p>
                          <p v-if="src.detail" class="text-2xs text-ink-gray-4 mt-0.5">{{ src.detail }}</p>
                        </div>
                        <span
                          class="lucide-chevron-right size-3.5 text-ink-gray-3 transition-transform flex-shrink-0"
                          :class="expandedSources.has(i) ? 'rotate-90' : ''"
                          aria-hidden="true"
                        />
                      </button>

                      <div v-if="expandedSources.has(i)" class="border-t border-outline-gray-1 bg-surface-gray-1">
                        <div class="max-h-52 overflow-y-auto divide-y divide-outline-gray-1">
                          <div
                            v-for="r in src.subset"
                            :key="r.email"
                            class="flex items-center justify-between px-4 py-2 text-xs"
                          >
                            <span class="text-ink-gray-7 truncate mr-3">{{ r.email }}</span>
                            <div class="flex items-center gap-2 flex-shrink-0">
                              <span v-if="r.opened" class="flex items-center gap-0.5 text-ink-green-6">
                                <span class="lucide-eye size-3" aria-hidden="true" /> Opened
                              </span>
                              <a
                                v-if="r.status === 'Failed' && r.email_queue"
                                :href="`/app/error-log?reference_doctype=Email%20Queue&reference_name=${encodeURIComponent(r.email_queue)}`"
                                target="_blank"
                                class="text-ink-red-5 hover:underline"
                              >Failed</a>
                              <span v-else :class="{
                                'text-ink-gray-4':  r.status === 'Sent',
                                'text-ink-red-5':   r.status === 'Failed',
                                'text-ink-amber-6': r.status === 'Excluded',
                              }">{{ r.status }}</span>
                            </div>
                          </div>
                          <div v-if="!src.subset.length" class="px-4 py-4 text-xs text-ink-gray-4 text-center">No recipients found.</div>
                        </div>
                      </div>

                    </div>

                    <!-- Fallback when no source config stored -->
                    <div v-if="!audienceSources.length" class="divide-y divide-outline-gray-1">
                      <div
                        v-for="r in recipients"
                        :key="r.email"
                        class="flex items-center justify-between px-4 py-2 text-xs"
                      >
                        <span class="text-ink-gray-7 truncate mr-3">{{ r.email }}</span>
                        <a
                          v-if="r.status === 'Failed' && r.email_queue"
                          :href="`/app/error-log?reference_doctype=Email%20Queue&reference_name=${encodeURIComponent(r.email_queue)}`"
                          target="_blank"
                          class="text-ink-red-5 hover:underline"
                        >Failed</a>
                        <span v-else :class="r.status === 'Sent' ? 'text-ink-gray-4' : 'text-ink-red-5'">{{ r.status }}</span>
                      </div>
                    </div>

                  </div>
                </div>
                <!-- Before sending: picker -->
                <RecipientsPicker
                  v-else
                  :model-value="recipientConfig"
                  @update:model-value="(v) => emit('update:recipientConfig', v)"
                />
              </div>

              <!-- ── Notifications ── -->
              <div v-else-if="activeTab === 'notifications'">
                <NotificationsTab :letter-doc="letterDoc" :subject="subject" :flush-save="flushSave" />
              </div>

              <!-- ── Analytics ── -->
              <div v-else-if="activeTab === 'analytics'" class="space-y-4">
                <div v-if="loadingAnalytics" class="text-xs text-ink-gray-5 py-6 text-center">Loading analytics…</div>

                <div v-else-if="!analytics || !analytics.sent_status" class="rounded border border-dashed border-outline-gray-2 px-4 py-10 text-center">
                  <span class="lucide-chart-bar size-6 text-ink-gray-4 mx-auto mb-2 block" aria-hidden="true" />
                  <p class="text-sm text-ink-gray-6 font-medium">No sends yet</p>
                  <p class="text-xs text-ink-gray-5 mt-1">Analytics appear here once this letter has been sent.</p>
                </div>

                <div v-else class="space-y-4">
                  <!-- Sending-in-progress notice -->
                  <div v-if="analytics.sent_status === 'Sending'" class="flex items-start gap-2 rounded border border-outline-blue-2 bg-surface-blue-1 px-3 py-2.5 text-xs text-ink-gray-7">
                    <span class="lucide-loader size-3.5 mt-0.5 flex-shrink-0 animate-spin text-blue-500" aria-hidden="true" />
                    <span>Send in progress. Stats update once the batch completes.</span>
                  </div>

                  <!-- Open rate stats (only shown for completed sends) -->
                  <div v-if="analytics.sent_status !== 'Sending'" class="grid grid-cols-2 gap-3">
                    <div class="rounded border border-outline-gray-1 bg-surface-gray-1 px-4 py-3">
                      <p class="text-2xl font-semibold text-ink-gray-9 tabular-nums">{{ analytics.sent }}</p>
                      <p class="text-xs text-ink-gray-5 mt-0.5">Delivered</p>
                    </div>
                    <div class="rounded border border-outline-gray-1 bg-surface-gray-1 px-4 py-3">
                      <p class="text-2xl font-semibold text-ink-gray-9 tabular-nums">{{ analytics.open_rate }}%</p>
                      <p class="text-xs text-ink-gray-5 mt-0.5">Open rate</p>
                    </div>
                    <div class="rounded border border-outline-gray-1 bg-surface-gray-1 px-4 py-3">
                      <p class="text-2xl font-semibold text-ink-gray-9 tabular-nums">{{ analytics.opened }}</p>
                      <p class="text-xs text-ink-gray-5 mt-0.5">Opened</p>
                    </div>
                    <div class="rounded border border-outline-gray-1 bg-surface-gray-1 px-4 py-3">
                      <p class="text-2xl font-semibold text-ink-gray-9 tabular-nums">{{ analytics.unsubscribed ?? 0 }}</p>
                      <p class="text-xs text-ink-gray-5 mt-0.5">Unsubscribed</p>
                    </div>
                  </div>

                  <div class="text-xs text-ink-gray-5 space-y-0.5">
                    <p v-if="analytics.last_sent">Sent on {{ formatDate(analytics.last_sent) }}</p>
                    <p v-if="analytics.last_opened">Last opened {{ formatDate(analytics.last_opened) }}</p>
                  </div>

                  <p class="text-xs text-ink-gray-4 border-t border-outline-gray-1 pt-3">
                    Open tracking uses a pixel — undercounts with image blocking, overcounts with inbox proxies, and won't register on localhost.
                  </p>
                </div>
              </div>

              <!-- ── HTML ── -->
              <div v-else-if="activeTab === 'html'">
                <div v-if="loadingHtml" class="text-xs text-ink-gray-5 py-6 text-center">Compiling…</div>
                <div v-else-if="compiledHtml">
                  <div class="flex items-center justify-between mb-2">
                    <span class="text-xs text-ink-gray-5">Compiled email HTML</span>
                    <Button variant="ghost" size="sm" icon-left="lucide-copy" @click="copyHtml">Copy</Button>
                  </div>
                  <pre class="text-2xs font-mono leading-relaxed text-ink-gray-7 bg-surface-gray-1 border border-outline-gray-2 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap break-all">{{ compiledHtml }}</pre>
                </div>
                <div v-else class="text-xs text-ink-gray-5 py-6 text-center">Could not compile HTML.</div>
              </div>

            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { TextInput, Button, toast } from "frappe-ui";
import RecipientsPicker from "./RecipientsPicker.vue";
import NotificationsTab from "./NotificationsTab.vue";

const props = defineProps({
  modelValue:      { type: Boolean, default: false },
  letterName:    { type: String, default: "" },
  subject:         { type: String, default: "" },
  previewText:     { type: String, default: "" },
  senderName:      { type: String, default: "" },
  senderEmail:     { type: String, default: "" },
  recipientConfig:    { type: Object, default: null },
  includeUnsubscribe: { type: Boolean, default: false },
  letterDoc:        { type: Object, default: null },
  initialTab:       { type: String, default: null },
  flushSave:        { type: Function, default: null },
});
const emit = defineEmits([
  "update:modelValue", "update:letterName", "update:subject",
  "update:previewText", "update:senderName", "update:senderEmail",
  "update:recipientConfig", "update:includeUnsubscribe",
]);

const isNotification = computed(() => !!props.letterDoc?.has_notification);
// Written as a computed string, not inline in the template — Vue's mustache
// parser can't have a literal "{{ doc.name }}" inside another interpolation.
const jinjaTagExample = computed(() => "{{ doc.name }}");
const sections = computed(() => {
  const all = [
    { id: "details",       label: "Details" },
    { id: "recipients",    label: "Recipients" },
    { id: "notifications", label: "Notifications" },
    { id: "analytics",     label: "Analytics" },
    { id: "html",          label: "HTML" },
  ];
  return all.filter(s => {
    if (s.id === "notifications") return !isSent.value;
    if (s.id === "recipients" || s.id === "analytics") return !isNotification.value;
    return true;
  });
});
const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit("update:modelValue", v),
});

const activeTab = ref("details");
const isSent = computed(() => ["Sent", "Partial", "Failed", "Sending", "Scheduled"].includes(props.letterDoc?.status));

const localSenderName  = ref(props.senderName);
const localSenderEmail = ref(props.senderEmail);
watch(() => props.senderName,  (v) => { localSenderName.value  = v; });
watch(() => props.senderEmail, (v) => { localSenderEmail.value = v; });
function commitSenderName()  { emit("update:senderName",  localSenderName.value); }
function commitSenderEmail() { emit("update:senderEmail", localSenderEmail.value); }

const OP_LABEL = { "=": "=", "!=": "≠", "like": "contains", "not like": "doesn't contain", ">": ">", "<": "<", ">=": "≥", "<=": "≤", "is": "is", "in": "in", "not in": "not in", "Between": "between", "Timespan": "timespan" };

function describeFilters(filters) {
  if (!filters || !Object.keys(filters).length) return null;
  const parts = Object.entries(filters).map(([field, val]) => {
    const op    = Array.isArray(val) ? (OP_LABEL[val[0]] || val[0]) : "=";
    const value = Array.isArray(val) ? (Array.isArray(val[1]) ? val[1].join(" – ") : val[1]) : val;
    return `${field} ${op} ${value}`;
  });
  return `Filters: ${parts.join(" | ")}`;
}

const audienceSources = computed(() => {
  const cfg = props.recipientConfig;
  if (!cfg) return [];
  const list = Array.isArray(cfg) ? cfg : [cfg];

  const recipientMap = Object.fromEntries(
    recipients.value.map(r => [r.email.toLowerCase(), r])
  );

  function resolvedSubset(src) {
    // If the backend snapshotted resolved_emails at send time, use them directly.
    if (src.resolved_emails?.length) {
      return src.resolved_emails
        .map(e => recipientMap[e.toLowerCase()])
        .filter(Boolean);
    }
    return null;
  }

  return list.map(src => {
    if (src.type === "group") {
      const members = groupMembers.value[src.email_group] || new Set();
      const subset = resolvedSubset(src) ?? [...members]
        .map(e => recipientMap[e.toLowerCase()])
        .filter(Boolean);
      return {
        title: src.email_group || "—",
        detail: null,
        externalLink: `/app/email-group/${encodeURIComponent(src.email_group)}`,
        subset,
      };
    }

    if (src.type === "paste") {
      const subset = resolvedSubset(src) ?? (src.recipients || [])
        .map(e => recipientMap[e.toLowerCase()])
        .filter(Boolean);
      return { title: "Pasted addresses", detail: null, externalLink: null, subset };
    }

    if (src.type === "doctype") {
      const filterDesc = describeFilters(src.filters);
      const subset = resolvedSubset(src) ?? recipients.value;
      return {
        title: src.doctype || "DocType",
        detail: filterDesc || null,
        externalLink: null,
        subset,
      };
    }

    return null;
  }).filter(Boolean);
});

const analytics         = ref(null);
const loadingAnalytics  = ref(false);
const compiledHtml      = ref(null);
const loadingHtml       = ref(false);

// ── Merge fields (Jinja "Insert field") ────────────────────────────────────
const subjectInputRef      = ref(null);
const showFieldPicker      = ref(false);
const mergeFields          = ref([]);
const loadingMergeFields   = ref(false);
const subjectCursorPos     = ref(null);

function trackSubjectCursor() {
  const el = subjectInputRef.value?.el;
  if (el) subjectCursorPos.value = el.selectionStart;
}

async function loadMergeFields() {
  if (!props.letterDoc?.name) return;
  loadingMergeFields.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.notifications.get_merge_fields",
      args: { letter: props.letterDoc.name },
    });
    mergeFields.value = res.message?.fields || [];
  } catch {
    mergeFields.value = [];
  } finally {
    loadingMergeFields.value = false;
  }
}

async function toggleFieldPicker() {
  showFieldPicker.value = !showFieldPicker.value;
  if (showFieldPicker.value && !mergeFields.value.length) await loadMergeFields();
}

function insertMergeField(fieldname) {
  const tag = `{{ doc.${fieldname} }}`;
  const pos = subjectCursorPos.value ?? props.subject.length;
  const next = props.subject.slice(0, pos) + tag + props.subject.slice(pos);
  emit("update:subject", next);
  subjectCursorPos.value = pos + tag.length;
  showFieldPicker.value = false;
}

const recipients        = ref([]);
const loadingRecipients = ref(false);
const expandedSources   = ref(new Set());
const groupMembers      = ref({}); // { groupName: Set<email> }

function toggleSource(i) {
  const s = new Set(expandedSources.value);
  s.has(i) ? s.delete(i) : s.add(i);
  expandedSources.value = s;
}

async function loadAnalytics() {
  if (!props.letterDoc?.name) {
    analytics.value = null;
    return;
  }
  loadingAnalytics.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_letter_analytics",
      args: { name: props.letterDoc.name },
    });
    analytics.value = res.message || null;
  } catch {
    analytics.value = null;
  } finally {
    loadingAnalytics.value = false;
  }
}

async function loadRecipients() {
  if (!props.letterDoc?.name) return;
  loadingRecipients.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_letter_recipients",
      args: { name: props.letterDoc.name },
    });
    recipients.value = res.message || [];
    await loadGroupMembers();
  } catch {
    recipients.value = [];
  } finally {
    loadingRecipients.value = false;
  }
}

async function loadGroupMembers() {
  const cfg = props.recipientConfig;
  if (!cfg) return;
  const list = Array.isArray(cfg) ? cfg : [cfg];
  const groups = list.filter(s => s.type === "group").map(s => s.email_group).filter(Boolean);
  const result = {};
  await Promise.all(groups.map(async (g) => {
    try {
      const res = await frappe.call({
        method: "frappe.client.get_list",
        args: { doctype: "Email Group Member", filters: { email_group: g }, fields: ["email"], limit: 10000 },
      });
      result[g] = new Set((res.message || []).map(r => r.email.toLowerCase()));
    } catch {
      result[g] = new Set();
    }
  }));
  groupMembers.value = result;
}

watch(() => props.modelValue, (open) => {
  if (open && props.initialTab && sections.some(s => s.id === props.initialTab)) {
    activeTab.value = props.initialTab;
  }
});

watch(
  () => [props.modelValue, activeTab.value, props.letterDoc?.status],
  ([open, tab, status], [, , prevStatus]) => {
    if (!open) return;
    // Auto-switch to analytics when letter transitions to a sent state
    if (status !== prevStatus && ["Sent", "Partial", "Failed"].includes(status)) {
      activeTab.value = "analytics";
    }
    if (tab === "analytics") loadAnalytics();
    if (tab === "recipients" && isSent.value) loadRecipients();
    if (tab === "html") loadHtml();
    if (tab === "details" && isNotification.value && !mergeFields.value.length) loadMergeFields();
  }
);

async function loadHtml() {
  if (!props.letterDoc?.name) return;
  loadingHtml.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.render_preview",
      args: { name: props.letterDoc.name },
    });
    compiledHtml.value = res.message?.html || null;
  } catch {
    compiledHtml.value = null;
  } finally {
    loadingHtml.value = false;
  }
}

function copyHtml() {
  if (!compiledHtml.value) return;
  navigator.clipboard.writeText(compiledHtml.value);
  toast.success("HTML copied to clipboard.");
}

function formatDate(s) {
  try {
    return new Date(s.replace(" ", "T")).toLocaleString();
  } catch {
    return s;
  }
}
</script>
