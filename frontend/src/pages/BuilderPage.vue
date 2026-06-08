<template>
  <div class="flex h-screen w-screen bg-gray-100 font-sans overflow-hidden">

    <!-- Left: Block Palette -->
    <aside class="w-52 flex-shrink-0 bg-gray-900 flex flex-col overflow-y-auto">
      <div class="px-4 py-3 border-b border-gray-700">
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-widest">Blocks</span>
      </div>
      <div class="p-3 flex flex-col gap-1.5">
        <div
          v-for="block in availableBlocks"
          :key="block.type"
          class="flex items-center gap-2 px-3 py-2 rounded-md bg-gray-800 text-gray-200 text-sm cursor-grab select-none hover:bg-gray-700 active:cursor-grabbing transition-colors"
          draggable="true"
          @dragstart="onDragStart(block)"
        >
          <span class="text-gray-400 text-xs">{{ block.icon }}</span>
          {{ block.label }}
        </div>
      </div>
    </aside>

    <!-- Center: Canvas -->
    <main
      class="flex-1 overflow-y-auto p-8"
      @dragover.prevent
      @drop="onDrop"
    >
      <div class="max-w-2xl mx-auto">
        <!-- Campaign meta bar -->
        <div class="mb-3 flex flex-col gap-2">
          <div class="flex items-center gap-3">
            <TextInput
              v-model="editorStore.campaignName"
              placeholder="Campaign name…"
              class="flex-1"
              size="sm"
            />
            <Button variant="solid" theme="gray" size="sm" @click="saveCampaign" :loading="saving">
              Save
            </Button>
            <Button variant="subtle" size="sm" @click="refreshPreview" :loading="previewing">
              Preview
            </Button>
          </div>
          <div class="flex items-center gap-2">
            <TextInput
              v-model="subject"
              placeholder="Subject line…"
              class="flex-1"
              size="sm"
            />
            <TextInput
              v-model="previewText"
              placeholder="Preview text…"
              class="flex-1"
              size="sm"
            />
          </div>
        </div>

        <!-- Save feedback -->
        <div v-if="saveMsg" class="mb-3 px-3 py-2 rounded bg-green-50 text-green-700 text-xs">
          {{ saveMsg }}
        </div>

        <!-- Empty state -->
        <div
          v-if="!editorStore.blocks.length"
          class="border-2 border-dashed border-gray-300 rounded-lg p-16 text-center text-gray-400 text-sm"
        >
          Drag blocks here to start designing
        </div>

        <!-- Block list -->
        <component
          v-for="(block, index) in editorStore.blocks"
          :key="block.id"
          :is="blockComponent(block.type)"
          :block="block"
          :index="index"
        />
      </div>
    </main>

    <!-- Right: Preview -->
    <aside class="w-80 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col overflow-hidden">
      <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <span class="text-xs font-semibold text-gray-500 uppercase tracking-widest">Preview</span>
        <div class="flex gap-1">
          <Button
            variant="subtle"
            size="sm"
            :class="previewMode === 'desktop' ? 'bg-gray-100' : ''"
            @click="previewMode = 'desktop'"
          >Desktop</Button>
          <Button
            variant="subtle"
            size="sm"
            :class="previewMode === 'mobile' ? 'bg-gray-100' : ''"
            @click="previewMode = 'mobile'"
          >Mobile</Button>
        </div>
      </div>
      <div class="flex-1 overflow-y-auto p-3">
        <div
          class="border border-gray-200 rounded overflow-hidden bg-white transition-all mx-auto"
          :class="previewMode === 'mobile' ? 'max-w-[375px]' : 'w-full'"
          v-html="editorStore.renderedHtml || '<div class=\'p-8 text-gray-400 text-sm text-center\'>Save &amp; click Preview</div>'"
        />
      </div>
    </aside>

  </div>
</template>

<script setup>
import { ref, defineAsyncComponent, onMounted } from "vue";
import { Button, TextInput } from "frappe-ui";
import { useEditorStore } from "../stores/editor";

const editorStore = useEditorStore();
const previewMode = ref("desktop");
const saving = ref(false);
const previewing = ref(false);
const saveMsg = ref("");
const subject = ref("");
const previewText = ref("");

// Read campaign name from URL ?name=xxx
const urlParams = new URLSearchParams(window.location.search);
const initialName = urlParams.get("name");

onMounted(async () => {
  if (initialName) {
    await loadCampaign(initialName);
  }
});

async function loadCampaign(name) {
  try {
    const res = await frappe.call({
      method: "letters.api.get_campaign",
      args: { name },
    });
    const doc = res.message;
    editorStore.loadFromDoc(doc);
    subject.value = doc.subject;
    previewText.value = doc.preview_text;
  } catch (e) {
    console.error("Failed to load campaign", e);
  }
}

async function saveCampaign() {
  saving.value = true;
  saveMsg.value = "";
  try {
    const res = await frappe.call({
      method: "letters.api.save_campaign",
      args: {
        name: editorStore.campaignDoc?.name || null,
        title: editorStore.campaignName || "Untitled Campaign",
        subject: subject.value,
        preview_text: previewText.value,
        blocks: JSON.stringify(
          editorStore.blocks.map(({ id: _id, ...rest }) => rest)
        ),
      },
    });
    const saved = res.message;
    if (!editorStore.campaignDoc) {
      editorStore.campaignDoc = saved;
    } else {
      editorStore.campaignDoc.name = saved.name;
    }
    saveMsg.value = "Saved!";
    setTimeout(() => (saveMsg.value = ""), 2500);
  } catch (e) {
    console.error("Save failed", e);
  } finally {
    saving.value = false;
  }
}

async function refreshPreview() {
  previewing.value = true;
  try {
    const res = await frappe.call({
      method: "letters.api.render_preview",
      args: {
        blocks: JSON.stringify(
          editorStore.blocks.map(({ id: _id, ...rest }) => rest)
        ),
      },
    });
    editorStore.setRenderedHtml(res.message.html);
  } catch (e) {
    console.error("Preview failed", e);
  } finally {
    previewing.value = false;
  }
}

const availableBlocks = [
  { type: "hero",       label: "Hero",         icon: "◉" },
  { type: "text",       label: "Text",         icon: "¶" },
  { type: "image_text", label: "Image + Text", icon: "▣" },
  { type: "button",     label: "Button",       icon: "▷" },
  { type: "divider",    label: "Divider",      icon: "—" },
  { type: "footer",     label: "Footer",       icon: "≡" },
];

const blockComponentCache = {};

function blockComponent(type) {
  if (!blockComponentCache[type]) {
    blockComponentCache[type] = defineAsyncComponent(
      () => import(`../components/blocks/${type}.vue`)
    );
  }
  return blockComponentCache[type];
}

let dragging = null;

function onDragStart(block) {
  dragging = block;
}

function onDrop() {
  if (dragging) {
    editorStore.addBlock(dragging.type);
    dragging = null;
  }
}
</script>
