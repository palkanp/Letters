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

        <!-- Panel: left nav + right content, mirroring Frappe Builder's settings -->
        <div class="bg-surface-base relative flex w-full max-w-3xl h-[560px] max-h-[90vh] rounded-xl shadow-2xl overflow-hidden">

          <!-- Left nav -->
          <aside class="bg-surface-gray-2 border-outline-gray-2 w-52 flex-shrink-0 border-r p-3 flex flex-col">
            <p class="text-ink-gray-9 px-2.5 py-2 text-base font-semibold">Settings</p>
            <p class="text-ink-gray-5 px-2.5 pt-2 pb-1 text-xs font-medium uppercase tracking-wide">Campaign</p>
            <nav class="space-y-0.5">
              <Button
                v-for="s in sections"
                :key="s.id"
                variant="ghost"
                :icon="s.icon"
                :label="s.label"
                class="w-full !justify-start !text-sm"
                :class="activeTab === s.id
                  ? '!bg-surface-base !text-ink-gray-9 shadow-sm !font-medium'
                  : '!text-ink-gray-5'"
                @click="activeTab = s.id"
              />
            </nav>
          </aside>

          <!-- Right content -->
          <div class="bg-surface-base flex-1 flex flex-col min-w-0">
            <div class="border-outline-gray-2 flex items-center justify-between px-6 py-4 border-b flex-shrink-0">
              <h2 class="text-ink-gray-9 text-base font-semibold">{{ activeSection.label }}</h2>
              <Button variant="ghost" icon="x" size="sm" aria-label="Close settings" @click="close" />
            </div>

            <div class="flex-1 overflow-y-auto px-6 py-5">

              <!-- ── Details ── -->
              <div v-if="activeTab === 'details'" class="space-y-4">
                <label class="block">
                  <span class="block text-xs font-semibold text-ink-gray-6 uppercase tracking-wide mb-1.5">Campaign Name</span>
                  <TextInput
                    :model-value="campaignName"
                    placeholder="e.g. June Newsletter"
                    @update:model-value="(v) => emit('update:campaignName', v)"
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
              </div>

              <!-- ── Recipients ── -->
              <div v-else-if="activeTab === 'recipients'">
                <!-- After sending: show who it was sent to -->
                <div v-if="isSent">
                  <div v-if="loadingRecipients" class="text-xs text-ink-gray-5 py-6 text-center">Loading…</div>
                  <div v-else>
                    <div class="max-h-80 overflow-y-auto rounded border border-outline-gray-1 divide-y divide-outline-gray-1">
                      <div
                        v-for="r in recipients"
                        :key="r.email"
                        class="flex items-center justify-between px-3 py-2 text-xs"
                      >
                        <span class="text-ink-gray-7 truncate mr-3">{{ r.email }}</span>
                        <div class="flex items-center gap-2 flex-shrink-0">
                          <span v-if="r.opened" class="flex items-center gap-0.5 text-green-600">
                            <FeatherIcon name="eye" class="w-3 h-3" /> Opened
                          </span>
                          <span :class="r.status === 'Sent' ? 'text-ink-gray-4' : r.status === 'Failed' ? 'text-red-500' : 'text-yellow-600'">
                            {{ r.status }}
                          </span>
                        </div>
                      </div>
                      <div v-if="!recipients.length" class="px-3 py-6 text-xs text-ink-gray-4 text-center">No recipients found.</div>
                    </div>
                    <p v-if="analytics && analytics.total > recipients.length" class="text-xs text-ink-gray-4 mt-1.5">
                      Showing first {{ recipients.length }} of {{ analytics.total }}
                    </p>
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
                  <FeatherIcon name="bar-chart-2" class="w-6 h-6 text-ink-gray-4 mx-auto mb-2" />
                  <p class="text-sm text-ink-gray-6 font-medium">No sends yet</p>
                  <p class="text-xs text-ink-gray-5 mt-1">Analytics appear here once this campaign has been sent.</p>
                </div>

                <div v-else class="space-y-4">
                  <!-- Sending-in-progress notice -->
                  <div v-if="analytics.sent_status === 'Sending'" class="flex items-start gap-2 rounded border border-outline-blue-2 bg-surface-blue-1 px-3 py-2.5 text-xs text-ink-gray-7">
                    <FeatherIcon name="loader" class="w-3.5 h-3.5 mt-0.5 flex-shrink-0 animate-spin text-blue-500" />
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

                  <!-- Delivery breakdown -->
                  <div v-if="analytics.sent_status !== 'Sending' && analytics.status_counts && Object.keys(analytics.status_counts).length" class="space-y-1.5">
                    <p class="text-xs font-medium text-ink-gray-7">Delivery breakdown</p>
                    <div
                      v-for="(count, status) in analytics.status_counts"
                      :key="status"
                      class="flex items-center justify-between text-xs py-1 border-b border-outline-gray-1 last:border-0"
                    >
                      <span class="flex items-center gap-1.5">
                        <span
                          class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                          :class="status === 'Sent' ? 'bg-surface-green-3' : status === 'Failed' ? 'bg-surface-red-4' : status === 'Pending' ? 'bg-surface-gray-4' : 'bg-surface-amber-2'"
                        />
                        <span class="text-ink-gray-6">{{ status }}</span>
                      </span>
                      <span class="tabular-nums font-medium text-ink-gray-7">{{ count }}</span>
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
import { TextInput, FeatherIcon, Button } from "frappe-ui";
import RecipientsPicker from "./RecipientsPicker.vue";

const props = defineProps({
  modelValue:      { type: Boolean, default: false },
  campaignName:    { type: String, default: "" },
  subject:         { type: String, default: "" },
  previewText:     { type: String, default: "" },
  recipientConfig: { type: Object, default: null },
  campaignDoc:     { type: Object, default: null },
});
const emit = defineEmits([
  "update:modelValue", "update:campaignName", "update:subject",
  "update:previewText", "update:recipientConfig",
]);

const sections = [
  { id: "details",    label: "Details",    icon: "settings" },
  { id: "recipients", label: "Recipients", icon: "users" },
  { id: "analytics",  label: "Analytics",  icon: "bar-chart-2" },
];
const activeTab = ref("details");
const activeSection = computed(() => sections.find(s => s.id === activeTab.value) || sections[0]);
const isSent = computed(() => ["Sent", "Partial", "Failed", "Sending"].includes(props.campaignDoc?.status));

function close() {
  emit("update:modelValue", false);
}

// ── Analytics (lazy: load when the tab is opened) ─────────────────────────────
const analytics        = ref(null);
const loadingAnalytics = ref(false);
const recipients       = ref([]);
const loadingRecipients = ref(false);

async function loadAnalytics() {
  if (!props.campaignDoc?.name) {
    analytics.value = null;
    return;
  }
  loadingAnalytics.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_campaign_analytics",
      args: { name: props.campaignDoc.name },
    });
    analytics.value = res.message || null;
  } catch {
    analytics.value = null;
  } finally {
    loadingAnalytics.value = false;
  }
}

async function loadRecipients() {
  if (!props.campaignDoc?.name) return;
  loadingRecipients.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_campaign_recipients",
      args: { name: props.campaignDoc.name },
    });
    recipients.value = res.message || [];
  } catch {
    recipients.value = [];
  } finally {
    loadingRecipients.value = false;
  }
}

watch(
  () => [props.modelValue, activeTab.value],
  ([open, tab]) => {
    if (!open) return;
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
