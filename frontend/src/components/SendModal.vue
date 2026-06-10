<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      @click.self="$emit('close')"
    >
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-sm mx-4 flex flex-col">

        <!-- Header -->
        <div class="px-6 py-4 border-b border-gray-100 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 class="text-base font-semibold text-gray-900">Send Campaign</h2>
            <p class="text-xs text-gray-400 mt-0.5">{{ campaignName }}</p>
          </div>
          <button
            class="w-7 h-7 flex items-center justify-center rounded-md text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            @click="$emit('close')"
          ><FeatherIcon name="x" class="w-4 h-4" /></button>
        </div>

        <!-- Body -->
        <div class="px-6 py-5 space-y-4">

          <!-- Recipients summary -->
          <div v-if="recipientConfig" class="rounded-lg bg-gray-50 border border-gray-200 px-4 py-3 flex items-start gap-3">
            <FeatherIcon name="users" class="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
            <div class="min-w-0">
              <p class="text-xs font-semibold text-gray-700">{{ recipientSummary }}</p>
              <button
                type="button"
                class="text-xs text-blue-600 hover:underline mt-0.5"
                @click="$emit('open-recipients')"
              >Change recipients</button>
            </div>
          </div>

          <!-- No recipients configured -->
          <div v-else class="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 flex items-start gap-3">
            <FeatherIcon name="alert-circle" class="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <p class="text-xs font-medium text-amber-700">No recipients configured.</p>
              <button
                type="button"
                class="text-xs text-blue-600 hover:underline mt-0.5"
                @click="$emit('open-recipients')"
              >Select recipients first</button>
            </div>
          </div>

          <!-- Error -->
          <div v-if="sendError" class="bg-red-50 rounded-lg px-4 py-3 text-xs text-red-600">{{ sendError }}</div>

          <!-- Success -->
          <div v-if="sentCount" class="bg-green-50 rounded-lg px-4 py-3 text-xs text-green-700 font-medium flex items-center gap-2">
            <FeatherIcon name="check" class="w-3.5 h-3.5 flex-shrink-0" />
            Queued for {{ sentCount }} recipient{{ sentCount === 1 ? "" : "s" }}. Campaign marked as Ready.
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-100 flex items-center justify-end gap-3 flex-shrink-0">
          <Button variant="ghost" size="sm" @click="$emit('close')">Cancel</Button>
          <Button
            variant="solid"
            size="sm"
            :disabled="!recipientConfig || sending || !!sentCount"
            @click="send"
          >{{ sending ? "Sending…" : sendLabel }}</Button>
        </div>

      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from "vue";
import { Button, FeatherIcon } from "frappe-ui";

const props = defineProps({
  campaignName:    String,
  campaignDoc:     Object,
  recipientConfig: Object,  // { type, email_group | recipients | (doctype + email_field + filters) }
});
const emit = defineEmits(["close", "sent", "open-recipients"]);

const sending   = ref(false);
const sendError = ref("");
const sentCount = ref(0);

const recipientSummary = computed(() => {
  const cfg = props.recipientConfig;
  if (!cfg) return "";
  if (cfg.type === "group") return `Email Group: "${cfg.email_group}"`;
  if (cfg.type === "paste") return `${cfg.recipients?.length ?? 0} pasted email${cfg.recipients?.length === 1 ? "" : "s"}`;
  if (cfg.type === "doctype") {
    const filterCount = Object.keys(cfg.filters || {}).length;
    return `${cfg.doctype} › ${cfg.email_field}${filterCount ? ` (${filterCount} filter${filterCount === 1 ? "" : "s"})` : " (all)"}`;
  }
  return "Unknown";
});

const sendLabel = computed(() => {
  const cfg = props.recipientConfig;
  if (!cfg) return "Send";
  if (cfg.type === "paste") return `Send to ${cfg.recipients?.length ?? 0}`;
  return "Send";
});

async function send() {
  if (!props.recipientConfig || sending.value) return;
  sending.value = true;
  sendError.value = "";
  try {
    const cfg  = props.recipientConfig;
    const args = { name: props.campaignDoc?.name };
    if (cfg.type === "group") {
      args.email_group = cfg.email_group;
    } else if (cfg.type === "paste") {
      args.recipients = JSON.stringify(cfg.recipients);
    } else if (cfg.type === "doctype") {
      args.doctype_config = JSON.stringify({
        doctype:     cfg.doctype,
        email_field: cfg.email_field,
        filters:     cfg.filters || {},
      });
    }
    const res = await frappe.call({ method: "letters.letters.api.send_campaign", args });
    sentCount.value = res.message.count;
    emit("sent", res.message);
  } catch (e) {
    const raw = e?._server_messages;
    let msg = e?.message || "Send failed. Check your outgoing mail settings.";
    if (raw) {
      try { msg = JSON.parse(JSON.parse(raw)[0]).message || msg; } catch { /* keep */ }
    }
    sendError.value = msg;
  } finally {
    sending.value = false;
  }
}
</script>
