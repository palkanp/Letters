<template>
  <Teleport to="body">
    <transition
      enter-active-class="transition-opacity duration-150"
      leave-active-class="transition-opacity duration-150"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 flex items-center justify-center p-4 font-sans"
      >
        <!-- Overlay -->
        <div class="absolute inset-0 bg-black/60" @click="close" />

        <!-- Panel: left nav + right content -->
        <div class="bg-surface-base relative flex w-full max-w-3xl h-[560px] max-h-[90vh] rounded-xl shadow-2xl overflow-hidden border border-outline-gray-2">

          <!-- Left nav -->
          <aside class="bg-surface-gray-2 border-outline-gray-2 w-52 flex-shrink-0 border-r flex flex-col">
            <div class="flex items-center h-[60px] px-4 flex-shrink-0">
              <span class="text-ink-gray-9 text-base font-semibold">Settings</span>
            </div>
            <nav class="space-y-0.5 p-3">
              <Button
                v-for="s in sections"
                :key="s.id"
                variant="ghost"
                class="w-full !justify-start px-2.5 py-1.5 text-sm"
                :class="activeTab === s.id
                  ? 'bg-surface-base text-ink-gray-9 shadow-sm font-medium'
                  : 'text-ink-gray-5 hover:bg-surface-gray-3'"
                :iconLeft="`lucide-${s.icon}`"
                @click="activeTab = s.id"
              >
                {{ s.label }}
              </Button>
            </nav>
          </aside>

          <!-- Right content -->
          <div class="bg-surface-base flex-1 flex flex-col min-w-0">
            <div class="border-outline-gray-2 flex items-center justify-between px-6 py-4 border-b flex-shrink-0">
              <h2 class="text-ink-gray-9 text-base font-semibold">{{ activeSection.label }}</h2>
              <Button variant="ghost" icon="lucide-x" size="sm" aria-label="Close settings" @click="close" />
            </div>

            <div class="flex-1 overflow-y-auto px-6 py-5">

              <!-- ── Details ── -->
              <div v-if="activeTab === 'details'" class="space-y-4">
                <label class="block">
                  <span class="block text-xs font-semibold text-ink-gray-6 uppercase tracking-wide mb-1.5">Letter Name</span>
                  <TextInput
                    :model-value="letterName"
                    placeholder="e.g. June Newsletter"
                    @update:model-value="(v) => emit('update:letterName', v)"
                  />
                </label>
                <label class="block">
                  <span class="flex items-center justify-between mb-1.5">
                    <span class="text-xs font-semibold text-ink-gray-6 uppercase tracking-wide">Subject Line <span class="text-red-400 ml-0.5">*</span></span>
                    <span class="text-xs tabular-nums" :class="subject.length > 78 ? 'text-red-500' : subject.length > 60 ? 'text-orange-500' : 'text-ink-gray-4'">{{ subject.length }}</span>
                  </span>
                  <TextInput
                    :model-value="subject"
                    placeholder="e.g. Your June update is here"
                    @update:model-value="(v) => emit('update:subject', v)"
                  />
                  <p v-if="subject.length > 78" class="mt-1 text-xs text-red-500">Most email clients truncate subjects over 78 characters.</p>
                  <p v-else-if="subject.length > 60" class="mt-1 text-xs text-orange-500">Over 60 characters may be clipped on mobile.</p>
                </label>
                <label class="block">
                  <span class="block text-xs font-semibold text-ink-gray-6 uppercase tracking-wide mb-1.5">Preview Text</span>
                  <TextInput
                    :model-value="previewText"
                    placeholder="Brief teaser shown after subject line"
                    @update:model-value="(v) => emit('update:previewText', v)"
                  />
                </label>

                <div class="border-t border-outline-gray-1 pt-4">
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

                      <!-- Email group: link only, no expand -->
                      <div v-if="src.link" class="flex items-center gap-3 px-3 py-2.5">
                        <span :class="`lucide-${src.icon} size-3.5 flex-shrink-0 text-ink-gray-4`" aria-hidden="true" />
                        <div class="flex-1 min-w-0">
                          <p class="text-xs font-medium text-ink-gray-7">Email Group</p>
                          <a
                            :href="src.link"
                            target="_blank"
                            class="text-2xs text-ink-blue-4 hover:underline"
                          >{{ src.title }}</a>
                        </div>
                      </div>

                      <!-- Paste / DocType: expandable with count -->
                      <template v-else>
                        <button
                          class="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1 transition-colors text-left"
                          @click="toggleSource(i)"
                        >
                          <span :class="`lucide-${src.icon} size-3.5 flex-shrink-0 text-ink-gray-4`" aria-hidden="true" />
                          <div class="flex-1 min-w-0">
                            <p class="text-xs font-medium text-ink-gray-7">
                              {{ src.title }}
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
                                <span :class="{
                                  'text-ink-gray-4':  r.status === 'Sent',
                                  'text-ink-red-5':   r.status === 'Failed',
                                  'text-ink-amber-6': r.status === 'Excluded',
                                }">{{ r.status }}</span>
                              </div>
                            </div>
                            <div v-if="!src.subset.length" class="px-4 py-4 text-xs text-ink-gray-4 text-center">No recipients found.</div>
                          </div>
                        </div>
                      </template>

                    </div>

                    <!-- Fallback when no source config stored -->
                    <div v-if="!audienceSources.length" class="divide-y divide-outline-gray-1">
                      <div
                        v-for="r in recipients"
                        :key="r.email"
                        class="flex items-center justify-between px-3 py-2 text-xs"
                      >
                        <span class="text-ink-gray-7 truncate mr-3">{{ r.email }}</span>
                        <span :class="r.status === 'Sent' ? 'text-ink-gray-4' : 'text-ink-red-5'">{{ r.status }}</span>
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

            </div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { TextInput, Button } from "frappe-ui";
import RecipientsPicker from "./RecipientsPicker.vue";

const props = defineProps({
  modelValue:      { type: Boolean, default: false },
  letterName:    { type: String, default: "" },
  subject:         { type: String, default: "" },
  previewText:     { type: String, default: "" },
  recipientConfig:    { type: Object, default: null },
  includeUnsubscribe: { type: Boolean, default: false },
  letterDoc:        { type: Object, default: null },
});
const emit = defineEmits([
  "update:modelValue", "update:letterName", "update:subject",
  "update:previewText", "update:recipientConfig", "update:includeUnsubscribe",
]);

const sections = [
  { id: "details",    label: "Details",    icon: "settings" },
  { id: "recipients", label: "Recipients", icon: "users" },
  { id: "analytics",  label: "Analytics",  icon: "chart-bar" },
];
const activeTab = ref("details");
const activeSection = computed(() => sections.find(s => s.id === activeTab.value) || sections[0]);
const isSent = computed(() => ["Sent", "Partial", "Failed", "Sending"].includes(props.letterDoc?.status));

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
      return {
        icon: "users",
        title: src.email_group || "—",
        detail: null,
        link: `/app/email-group/${encodeURIComponent(src.email_group)}`,
        subset: null,
      };
    }

    if (src.type === "paste") {
      const subset = resolvedSubset(src) ?? (src.recipients || [])
        .map(e => recipientMap[e.toLowerCase()])
        .filter(Boolean);
      return { icon: "clipboard-list", title: "Pasted addresses", detail: null, link: null, subset };
    }

    if (src.type === "doctype") {
      const filterDesc = describeFilters(src.filters);
      const subset = resolvedSubset(src) ?? recipients.value;
      return {
        icon: "database",
        title: src.doctype || "DocType",
        detail: filterDesc || null,
        link: null,
        subset,
      };
    }

    return null;
  }).filter(Boolean);
});

function close() {
  emit("update:modelValue", false);
}

const analytics         = ref(null);
const loadingAnalytics  = ref(false);
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
  }
);

function onKeydown(e) {
  if (e.key === "Escape" && props.modelValue) close();
}
onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => document.removeEventListener("keydown", onKeydown));

function formatDate(s) {
  try {
    return new Date(s.replace(" ", "T")).toLocaleString();
  } catch {
    return s;
  }
}
</script>
