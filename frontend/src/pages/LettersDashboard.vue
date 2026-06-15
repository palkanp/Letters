<template>
  <div class="flex h-screen bg-surface-gray-1 font-sans overflow-hidden" @click="closeContextMenu">

    <!-- Sidebar -->
    <aside class="w-52 flex-shrink-0 bg-surface-base border-r border-outline-gray-1 flex flex-col py-4 px-3">
      <p class="px-2 mb-2 text-xs font-semibold text-ink-gray-4 uppercase tracking-wide">Letters</p>

      <button
        class="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors w-full text-left"
        :class="activeFolder === null ? 'bg-surface-gray-3 text-ink-gray-9 font-medium' : 'text-ink-gray-6 hover:bg-surface-gray-2'"
        @click="activeFolder = null"
      >
        <FeatherIcon name="inbox" class="w-3.5 h-3.5 flex-shrink-0" />
        All Letters
        <span class="ml-auto text-xs text-ink-gray-4 tabular-nums">{{ letters.length }}</span>
      </button>

      <div class="mt-3">
        <div class="flex items-center justify-between px-2 mb-1">
          <p class="text-[10px] font-semibold text-ink-gray-3 uppercase tracking-wide">Folders</p>
          <button
            class="text-ink-gray-3 hover:text-ink-gray-6 transition-colors"
            title="New folder"
            @click.stop="startNewFolder"
          >
            <FeatherIcon name="plus" class="w-3 h-3" />
          </button>
        </div>

        <!-- New folder input -->
        <div v-if="creatingFolder" class="flex items-center gap-1 px-2 py-1 mb-0.5">
          <FeatherIcon name="folder" class="w-3.5 h-3.5 text-ink-gray-4 flex-shrink-0" />
          <input
            ref="folderInput"
            v-model="newFolderName"
            class="flex-1 text-sm bg-transparent border-b border-outline-gray-3 outline-none text-ink-gray-9 py-0.5"
            placeholder="Folder name"
            @keydown.enter="saveNewFolder"
            @keydown.escape="cancelNewFolder"
            @blur="saveNewFolder"
          />
        </div>

        <button
          v-for="f in allFolders"
          :key="f.name"
          class="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors w-full text-left group"
          :class="activeFolder === f.name ? 'bg-surface-gray-3 text-ink-gray-9 font-medium' : 'text-ink-gray-6 hover:bg-surface-gray-2'"
          @click="activeFolder = f.name"
        >
          <FeatherIcon name="folder" class="w-3.5 h-3.5 flex-shrink-0" />
          <span class="truncate flex-1">{{ f.name }}</span>
          <span class="text-[10px] text-ink-gray-3 tabular-nums">{{ folderCount(f.name) }}</span>
        </button>

        <p v-if="!allFolders.length && !creatingFolder" class="px-2 text-xs text-ink-gray-3 mt-1">No folders yet</p>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Header -->
      <header class="flex items-center justify-between px-6 py-4 border-b border-outline-gray-1 bg-surface-base flex-shrink-0">
        <div>
          <h1 class="text-base font-semibold text-ink-gray-9">{{ activeFolder || "All Letters" }}</h1>
          <p class="text-xs text-ink-gray-5 mt-0.5">{{ visibleLetters.length }} letter{{ visibleLetters.length !== 1 ? "s" : "" }}</p>
        </div>
        <div class="flex items-center gap-2">
          <TextInput v-model="search" placeholder="Search…" class="w-44" />
          <Button variant="solid" @click="createNew" :loading="creating">
            <template #prefix><FeatherIcon name="plus" class="w-4 h-4" /></template>
            New Letter
          </Button>
        </div>
      </header>

      <!-- Grid -->
      <div class="flex-1 overflow-y-auto px-6 py-5">
        <div v-if="loading" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm gap-2">
          <FeatherIcon name="loader" class="w-4 h-4 animate-spin" />
          Loading…
        </div>

        <div v-else-if="!visibleLetters.length" class="flex flex-col items-center justify-center h-48 gap-3">
          <FeatherIcon name="mail" class="w-10 h-10 text-ink-gray-3" />
          <p class="text-sm text-ink-gray-5">{{ search ? "No letters match your search." : "No letters yet." }}</p>
          <Button v-if="!search" variant="subtle" @click="createNew" :loading="creating">
            <template #prefix><FeatherIcon name="plus" class="w-4 h-4" /></template>
            Create your first letter
          </Button>
        </div>

        <div v-else class="grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))">
          <LetterCard
            v-for="l in visibleLetters"
            :key="l.name"
            :letter="l"
            @open="openLetter"
            @contextmenu.prevent="openContextMenu($event, l)"
          />
        </div>
      </div>
    </div>

    <!-- Context menu -->
    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="fixed z-50 bg-surface-base border border-outline-gray-2 rounded-lg shadow-xl py-1 w-48 text-sm"
        :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
        @click.stop
      >
        <button
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          @click="openLetter(contextMenu.letter.name); closeContextMenu()"
        >
          <FeatherIcon name="edit-2" class="w-3.5 h-3.5" /> Open
        </button>

        <div class="border-t border-outline-gray-1 my-1" />

        <p class="px-3 py-1 text-[10px] font-semibold text-ink-gray-4 uppercase tracking-wide">Move to folder</p>
        <button
          v-if="contextMenu.letter?.folder"
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          @click="moveToFolder(contextMenu.letter, null)"
        >
          <FeatherIcon name="x" class="w-3.5 h-3.5" /> Remove from folder
        </button>
        <button
          v-for="f in allFolders"
          :key="f.name"
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left transition-colors"
          :class="contextMenu.letter?.folder === f.name ? 'text-ink-gray-4 cursor-default' : 'text-ink-gray-7 hover:bg-surface-gray-2'"
          :disabled="contextMenu.letter?.folder === f.name"
          @click="contextMenu.letter?.folder !== f.name && moveToFolder(contextMenu.letter, f.name)"
        >
          <FeatherIcon name="folder" class="w-3.5 h-3.5" />
          <span class="truncate">{{ f.name }}</span>
          <FeatherIcon v-if="contextMenu.letter?.folder === f.name" name="check" class="w-3 h-3 ml-auto" />
        </button>
        <p v-if="!allFolders.length" class="px-3 py-1.5 text-xs text-ink-gray-4">No folders — create one in the sidebar</p>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { FeatherIcon, Button, TextInput } from "frappe-ui";
import LetterCard from "../components/LetterCard.vue";

const emit = defineEmits(["open-letter"]);

const letters = ref([]);
const allFolders = ref([]);
const loading = ref(false);
const creating = ref(false);
const search = ref("");
const activeFolder = ref(null);

// Folder creation
const creatingFolder = ref(false);
const newFolderName = ref("");
const folderInput = ref(null);

// Context menu
const contextMenu = ref({ visible: false, x: 0, y: 0, letter: null });

const visibleLetters = computed(() => {
  let list = activeFolder.value
    ? letters.value.filter((l) => l.folder === activeFolder.value)
    : letters.value;
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    list = list.filter(
      (l) =>
        (l.title || "").toLowerCase().includes(q) ||
        (l.subject || "").toLowerCase().includes(q),
    );
  }
  return list;
});

function folderCount(name) {
  return letters.value.filter((l) => l.folder === name).length;
}

async function load() {
  loading.value = true;
  try {
    const [lettersRes, foldersRes] = await Promise.all([
      frappe.call({ method: "letters.letters.api.get_letters" }),
      frappe.call({ method: "frappe.client.get_list", args: { doctype: "Letter Folder", fields: ["name"], order_by: "name asc", limit: 200 } }),
    ]);
    letters.value = lettersRes.message || [];
    allFolders.value = foldersRes.message || [];
  } catch {
    letters.value = [];
  } finally {
    loading.value = false;
  }
}

async function createNew() {
  creating.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.save_campaign",
      args: activeFolder.value ? { folder: activeFolder.value } : {},
    });
    if (res.message?.name) openLetter(res.message.name);
  } finally {
    creating.value = false;
  }
}

function openLetter(name) {
  emit("open-letter", name);
}

// ── Folder creation ──────────────────────────────────────────────────────────
async function startNewFolder() {
  creatingFolder.value = true;
  newFolderName.value = "";
  await nextTick();
  folderInput.value?.focus();
}

async function saveNewFolder() {
  const name = newFolderName.value.trim();
  creatingFolder.value = false;
  if (!name) return;
  try {
    await frappe.call({
      method: "frappe.client.insert",
      args: { doc: { doctype: "Letter Folder", folder_name: name } },
    });
    await load();
    activeFolder.value = name;
  } catch (e) {
    frappe.msgprint(e.message || "Could not create folder.");
  }
}

function cancelNewFolder() {
  creatingFolder.value = false;
  newFolderName.value = "";
}

// ── Context menu ─────────────────────────────────────────────────────────────
function openContextMenu(event, letter) {
  contextMenu.value = { visible: true, x: event.clientX, y: event.clientY, letter };
}

function closeContextMenu() {
  contextMenu.value.visible = false;
}

async function moveToFolder(letter, folderName) {
  closeContextMenu();
  try {
    await frappe.call({
      method: "frappe.client.set_value",
      args: { doctype: "Letter", name: letter.name, fieldname: "folder", value: folderName || "" },
    });
    letter.folder = folderName || null;
  } catch (e) {
    frappe.msgprint(e.message || "Could not move letter.");
  }
}

onMounted(load);
</script>
