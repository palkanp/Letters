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
          <button class="text-ink-gray-3 hover:text-ink-gray-6 transition-colors" title="New folder" @click.stop="startNewFolder">
            <FeatherIcon name="plus" class="w-3 h-3" />
          </button>
        </div>

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
          class="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors w-full text-left"
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
      <header class="flex items-center justify-between px-6 py-3.5 border-b border-outline-gray-1 bg-surface-base flex-shrink-0 gap-3">
        <h1 class="text-base font-semibold text-ink-gray-9 flex-shrink-0">{{ activeFolder || "All Letters" }}</h1>

        <div class="flex items-center gap-2 flex-1 justify-end">
          <!-- Search -->
          <div class="relative">
            <FeatherIcon name="search" class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-ink-gray-4 pointer-events-none" />
            <input
              v-model="search"
              placeholder="Filter by title…"
              class="pl-8 pr-3 py-1.5 text-sm bg-surface-gray-2 border border-outline-gray-1 rounded-md outline-none focus:border-outline-gray-4 text-ink-gray-8 placeholder:text-ink-gray-3 w-48 transition-colors"
            />
          </div>

          <!-- Status filter -->
          <Dropdown :options="statusOptions" @select="(o) => activeStatus = o.value">
            <template #default>
              <button
                class="flex items-center gap-1.5 px-3 py-1.5 text-sm border rounded-md transition-colors"
                :class="activeStatus ? 'border-outline-gray-4 bg-surface-gray-3 text-ink-gray-9 font-medium' : 'border-outline-gray-1 bg-surface-base text-ink-gray-6 hover:bg-surface-gray-2'"
              >
                {{ activeStatus || "Status" }}
                <FeatherIcon v-if="activeStatus" name="x" class="w-3 h-3 opacity-60" @click.stop="activeStatus = null" />
                <FeatherIcon v-else name="chevron-down" class="w-3 h-3" />
              </button>
            </template>
          </Dropdown>

          <!-- Sort -->
          <Dropdown :options="sortOptions" @select="(o) => sortBy = o.value">
            <template #default>
              <button class="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-outline-gray-1 bg-surface-base text-ink-gray-6 hover:bg-surface-gray-2 rounded-md transition-colors">
                {{ sortOptions.find(s => s.value === sortBy)?.label || 'Last Modified' }}
                <FeatherIcon name="chevron-down" class="w-3 h-3" />
              </button>
            </template>
          </Dropdown>

          <!-- View toggle -->
          <div class="flex border border-outline-gray-1 rounded-md overflow-hidden">
            <button
              class="px-2 py-1.5 transition-colors"
              :class="viewMode === 'grid' ? 'bg-surface-gray-3 text-ink-gray-9' : 'bg-surface-base text-ink-gray-4 hover:bg-surface-gray-2'"
              title="Grid view"
              @click="viewMode = 'grid'"
            >
              <FeatherIcon name="grid" class="w-3.5 h-3.5" />
            </button>
            <button
              class="px-2 py-1.5 border-l border-outline-gray-1 transition-colors"
              :class="viewMode === 'list' ? 'bg-surface-gray-3 text-ink-gray-9' : 'bg-surface-base text-ink-gray-4 hover:bg-surface-gray-2'"
              title="List view"
              @click="viewMode = 'list'"
            >
              <FeatherIcon name="list" class="w-3.5 h-3.5" />
            </button>
          </div>

          <Button variant="solid" @click="createNew" :loading="creating">
            <template #prefix><FeatherIcon name="plus" class="w-4 h-4" /></template>
            New Letter
          </Button>
        </div>
      </header>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-6 py-5">
        <div v-if="loading" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm gap-2">
          <FeatherIcon name="loader" class="w-4 h-4 animate-spin" />
          Loading…
        </div>

        <div v-else-if="!visibleLetters.length" class="flex flex-col items-center justify-center h-48 gap-3">
          <FeatherIcon name="mail" class="w-10 h-10 text-ink-gray-3" />
          <p class="text-sm text-ink-gray-5">{{ search || activeStatus ? "No letters match your filters." : "No letters yet." }}</p>
          <Button v-if="!search && !activeStatus" variant="subtle" @click="createNew" :loading="creating">
            <template #prefix><FeatherIcon name="plus" class="w-4 h-4" /></template>
            Create your first letter
          </Button>
        </div>

        <!-- Grid view -->
        <div v-else-if="viewMode === 'grid'" class="grid gap-4" style="grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))">
          <LetterCard
            v-for="l in visibleLetters"
            :key="l.name"
            :letter="l"
            @open="openLetter"
            @contextmenu.prevent="openContextMenu($event, l)"
          />
        </div>

        <!-- List view -->
        <div v-else class="bg-surface-base border border-outline-gray-1 rounded-xl overflow-hidden divide-y divide-outline-gray-1">
          <div
            v-for="l in visibleLetters"
            :key="l.name"
            class="flex items-center gap-4 px-4 py-3 hover:bg-surface-gray-1 cursor-pointer transition-colors group"
            @click="openLetter(l.name)"
            @contextmenu.prevent="openContextMenu($event, l)"
          >
            <!-- Thumbnail placeholder -->
            <div class="w-16 h-12 rounded-md bg-surface-gray-2 border border-outline-gray-1 flex-shrink-0 flex items-center justify-center">
              <FeatherIcon name="mail" class="w-5 h-5 text-ink-gray-3" />
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium text-ink-gray-9 truncate">{{ l.title }}</p>
              <p class="text-xs text-ink-gray-4 truncate mt-0.5">{{ l.subject || "No subject" }}</p>
            </div>

            <!-- Modified -->
            <p class="text-xs text-ink-gray-4 flex-shrink-0 hidden sm:block w-36 text-right">
              {{ relativeTime(l.modified) }}
            </p>

            <!-- Status badge -->
            <span
              class="text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 w-20 text-center"
              :class="statusClass(l.status)"
            >{{ l.status }}</span>

            <!-- Actions -->
            <button
              class="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded text-ink-gray-4 hover:text-ink-gray-7 hover:bg-surface-gray-3"
              @click.stop="openContextMenu($event, l)"
            >
              <FeatherIcon name="more-horizontal" class="w-4 h-4" />
            </button>
          </div>
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
        <button
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          @click="duplicateLetter(contextMenu.letter); closeContextMenu()"
        >
          <FeatherIcon name="copy" class="w-3.5 h-3.5" /> Duplicate
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
        <p v-if="!allFolders.length" class="px-3 py-1.5 text-xs text-ink-gray-4">No folders yet</p>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { FeatherIcon, Button, Dropdown } from "frappe-ui";
import LetterCard from "../components/LetterCard.vue";

const emit = defineEmits(["open-letter"]);

const letters = ref([]);
const allFolders = ref([]);
const loading = ref(false);
const creating = ref(false);
const search = ref("");
const activeFolder = ref(null);
const activeStatus = ref(null);
const sortBy = ref("modified_desc");
const viewMode = ref("grid");

const creatingFolder = ref(false);
const newFolderName = ref("");
const folderInput = ref(null);

const contextMenu = ref({ visible: false, x: 0, y: 0, letter: null });

const statusOptions = [
  { label: "All", value: null },
  { label: "Draft", value: "Draft" },
  { label: "Scheduled", value: "Scheduled" },
  { label: "Sending", value: "Sending" },
  { label: "Sent", value: "Sent" },
  { label: "Partial", value: "Partial" },
  { label: "Failed", value: "Failed" },
];

const sortOptions = [
  { label: "Last Modified", value: "modified_desc" },
  { label: "Last Created", value: "creation_desc" },
  { label: "Alphabetically (A–Z)", value: "title_asc" },
  { label: "Alphabetically (Z–A)", value: "title_desc" },
];

const visibleLetters = computed(() => {
  let list = activeFolder.value
    ? letters.value.filter((l) => l.folder === activeFolder.value)
    : letters.value;
  if (activeStatus.value) list = list.filter((l) => l.status === activeStatus.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    list = list.filter(
      (l) => (l.title || "").toLowerCase().includes(q) || (l.subject || "").toLowerCase().includes(q),
    );
  }
  return [...list].sort((a, b) => {
    switch (sortBy.value) {
      case "creation_desc": return (b.creation || "").localeCompare(a.creation || "");
      case "title_asc":     return (a.title || "").localeCompare(b.title || "");
      case "title_desc":    return (b.title || "").localeCompare(a.title || "");
      default:              return (b.modified || "").localeCompare(a.modified || "");
    }
  });
});

function folderCount(name) {
  return letters.value.filter((l) => l.folder === name).length;
}

function statusClass(status) {
  const map = {
    Draft:     "bg-surface-gray-3 text-ink-gray-6",
    Scheduled: "bg-surface-amber-1 text-amber-700",
    Sending:   "bg-surface-blue-1 text-blue-700",
    Sent:      "bg-surface-green-1 text-green-700",
    Partial:   "bg-surface-amber-1 text-amber-700",
    Failed:    "bg-surface-red-1 text-red-700",
  };
  return map[status] || map.Draft;
}

function relativeTime(ts) {
  if (!ts) return "";
  try {
    const d = new Date(ts.replace(" ", "T"));
    const diff = (Date.now() - d.getTime()) / 1000;
    if (diff < 60) return "Just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 86400 * 7) return `${Math.floor(diff / 86400)}d ago`;
    return d.toLocaleDateString();
  } catch { return ""; }
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

async function duplicateLetter(letter) {
  try {
    const res = await frappe.call({
      method: "letters.letters.api.duplicate_campaign",
      args: { name: letter.name },
    });
    if (res.message?.name) {
      await load();
      openLetter(res.message.name);
    }
  } catch (e) {
    frappe.msgprint(e.message || "Could not duplicate.");
  }
}

function openLetter(name) { emit("open-letter", name); }

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

function openContextMenu(event, letter) {
  contextMenu.value = { visible: true, x: event.clientX, y: event.clientY, letter };
}

function closeContextMenu() { contextMenu.value.visible = false; }

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
