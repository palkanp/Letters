<template>
  <div class="flex h-screen bg-surface-gray-1 font-sans overflow-hidden" @click="closeAll">

    <!-- Sidebar -->
    <aside class="w-52 flex-shrink-0 bg-surface-base border-r border-outline-gray-1 flex flex-col">
      <!-- App header -->
      <div class="flex items-center gap-2.5 px-4 py-3.5 border-b border-outline-gray-1">
        <div class="w-7 h-7 rounded-lg bg-surface-gray-4 flex items-center justify-center flex-shrink-0 text-sm font-bold text-ink-gray-7">
          L
        </div>
        <span class="text-sm font-semibold text-ink-gray-9 flex-1">Letters</span>
        <button
          class="w-6 h-6 flex items-center justify-center rounded-md text-ink-gray-4 hover:text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          :title="props.isDark ? 'Switch to light' : 'Switch to dark'"
          @click.stop="props.toggleDark()"
        >
          <FeatherIcon :name="props.isDark ? 'sun' : 'moon'" class="w-3.5 h-3.5" />
        </button>
      </div>

      <!-- Nav -->
      <div class="px-3 py-3 flex flex-col gap-0.5">
        <button
          class="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors w-full text-left"
          :class="activeFolder === null ? 'bg-surface-gray-3 text-ink-gray-9 font-medium' : 'text-ink-gray-6 hover:bg-surface-gray-2'"
          @click="activeFolder = null"
        >
          <FeatherIcon name="inbox" class="w-3.5 h-3.5 flex-shrink-0" />
          All Letters
          <span class="ml-auto text-xs text-ink-gray-4 tabular-nums">{{ letters.length }}</span>
        </button>
      </div>

      <!-- Folders -->
      <div class="px-3 flex-1 overflow-y-auto">
        <div class="flex items-center justify-between px-2 mb-1">
          <p class="text-[10px] font-semibold text-ink-gray-3 uppercase tracking-wide">Folders</p>
          <button class="text-ink-gray-3 hover:text-ink-gray-6 transition-colors" title="New folder" @click.stop="startNewFolder">
            <FeatherIcon name="plus" class="w-3 h-3" />
          </button>
        </div>

        <div v-if="creatingFolder" class="flex items-center gap-1.5 px-2 py-1 mb-0.5">
          <FeatherIcon name="folder" class="w-3.5 h-3.5 text-ink-gray-4 flex-shrink-0" />
          <input
            ref="folderInput"
            v-model="newFolderName"
            class="flex-1 min-w-0 text-sm bg-transparent border-b border-outline-gray-3 outline-none text-ink-gray-9 py-0.5"
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
          <div class="relative">
            <FeatherIcon name="search" class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-ink-gray-4 pointer-events-none" />
            <input
              v-model="search"
              placeholder="Filter by title…"
              class="pl-8 pr-3 py-1.5 text-sm bg-surface-gray-2 border border-outline-gray-1 rounded-md outline-none focus:border-outline-gray-4 text-ink-gray-8 placeholder:text-ink-gray-3 w-48 transition-colors"
            />
          </div>

          <Dropdown :options="statusOptions">
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

          <Dropdown :options="sortOptions">
            <template #default>
              <button class="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-outline-gray-1 bg-surface-base text-ink-gray-6 hover:bg-surface-gray-2 rounded-md transition-colors">
                {{ sortOptions.find(s => s.value === sortBy)?.label || 'Last Modified' }}
                <FeatherIcon name="chevron-down" class="w-3 h-3" />
              </button>
            </template>
          </Dropdown>

          <div class="flex border border-outline-gray-1 rounded-md overflow-hidden">
            <button
              class="px-2 py-1.5 transition-colors"
              :class="viewMode === 'grid' ? 'bg-surface-gray-3 text-ink-gray-9' : 'bg-surface-base text-ink-gray-4 hover:bg-surface-gray-2'"
              @click="viewMode = 'grid'"
            ><FeatherIcon name="grid" class="w-3.5 h-3.5" /></button>
            <button
              class="px-2 py-1.5 border-l border-outline-gray-1 transition-colors"
              :class="viewMode === 'list' ? 'bg-surface-gray-3 text-ink-gray-9' : 'bg-surface-base text-ink-gray-4 hover:bg-surface-gray-2'"
              @click="viewMode = 'list'"
            ><FeatherIcon name="list" class="w-3.5 h-3.5" /></button>
          </div>

          <Button variant="solid" :loading="creating" @click="createNew">
            <template #prefix><FeatherIcon name="plus" class="w-4 h-4" /></template>
            New Letter
          </Button>
        </div>
      </header>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto px-6 py-5">
        <div v-if="loading" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm gap-2">
          <FeatherIcon name="loader" class="w-4 h-4 animate-spin" /> Loading…
        </div>

        <div v-else-if="!visibleLetters.length" class="flex flex-col items-center justify-center h-48 gap-3">
          <FeatherIcon name="mail" class="w-10 h-10 text-ink-gray-3" />
          <p class="text-sm text-ink-gray-5">{{ search || activeStatus ? "No letters match your filters." : "No letters yet." }}</p>
          <Button v-if="!search && !activeStatus" variant="subtle" :loading="creating" @click="createNew">
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
            @menu="(e) => openContextMenu(e, l)"
            @contextmenu.prevent="openContextMenu($event, l)"
          />
        </div>

        <!-- List view -->
        <div v-else class="divide-y divide-outline-gray-1">
          <div
            v-for="l in visibleLetters"
            :key="l.name"
            class="flex items-center gap-4 px-4 py-3 hover:bg-surface-gray-1 cursor-pointer transition-colors"
            @click="openLetter(l.name)"
            @contextmenu.prevent="openContextMenu($event, l)"
          >
            <div class="w-28 h-20 rounded-md flex-shrink-0 overflow-hidden">
              <LetterThumbnail :name="l.name" icon-class="w-5 h-5" />
            </div>
            <div class="flex-1 min-w-0 flex flex-col self-stretch justify-between py-0.5">
              <div class="min-w-0">
                <p class="text-sm font-medium text-ink-gray-9 truncate">{{ l.title }}</p>
                <p class="text-xs text-ink-gray-4 truncate mt-0.5">{{ l.subject || "No subject" }}</p>
              </div>
              <p class="text-xs text-ink-gray-3">{{ relativeTime(l.modified) }}</p>
            </div>
            <span
              class="text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 w-20 text-center"
              :class="statusClass(l.status)"
            >{{ l.status }}</span>
            <button
              class="p-1 rounded text-ink-gray-4 hover:text-ink-gray-7 hover:bg-surface-gray-3 transition-colors flex-shrink-0"
              @click.stop="openContextMenu($event, l)"
            >
              <FeatherIcon name="more-horizontal" class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Context menu + folder picker -->
    <Teleport to="body">
      <div
        v-if="contextMenu.visible"
        class="fixed z-50 bg-surface-base border border-outline-gray-2 rounded-lg shadow-xl py-1 w-52 text-sm"
        :style="contextMenuStyle"
        @click.stop
      >
        <button
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          @click="duplicateLetter(contextMenu.letter); closeAll()"
        >
          <FeatherIcon name="copy" class="w-3.5 h-3.5" /> Duplicate
        </button>
        <button
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          @click="viewInDesk(contextMenu.letter)"
        >
          <FeatherIcon name="external-link" class="w-3.5 h-3.5" /> View in Desk
        </button>

        <!-- Move to folder — inline toggle -->
        <button
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-7 hover:bg-surface-gray-2 transition-colors"
          @click.stop="folderMenuOpen = !folderMenuOpen"
        >
          <FeatherIcon name="folder" class="w-3.5 h-3.5" /> Move to folder
          <FeatherIcon :name="folderMenuOpen ? 'chevron-up' : 'chevron-down'" class="w-3 h-3 ml-auto text-ink-gray-4" />
        </button>

        <!-- Inline folder list -->
        <div v-if="folderMenuOpen" class="border-t border-outline-gray-1 mx-1 mt-0.5">
          <div class="px-2 py-1.5">
            <input
              v-model="folderSearch"
              placeholder="Search…"
              class="w-full px-2 py-1 text-xs bg-surface-gray-1 border border-outline-gray-2 rounded-md outline-none text-ink-gray-8 placeholder:text-ink-gray-3"
              @click.stop
            />
          </div>
          <div class="max-h-40 overflow-y-auto pb-1">
            <button
              v-if="contextMenu.letter?.folder"
              class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-ink-gray-6 hover:bg-surface-gray-2 transition-colors text-xs"
              @click="moveToFolder(contextMenu.letter, null)"
            >
              <FeatherIcon name="x" class="w-3 h-3" /> Remove from folder
            </button>
            <button
              v-for="f in filteredFolders"
              :key="f.name"
              class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-xs transition-colors"
              :class="contextMenu.letter?.folder === f.name ? 'text-ink-gray-4 cursor-default' : 'text-ink-gray-7 hover:bg-surface-gray-2'"
              :disabled="contextMenu.letter?.folder === f.name"
              @click="contextMenu.letter?.folder !== f.name && moveToFolder(contextMenu.letter, f.name)"
            >
              <FeatherIcon name="folder" class="w-3 h-3 flex-shrink-0" />
              <span class="truncate flex-1">{{ f.name }}</span>
              <FeatherIcon v-if="contextMenu.letter?.folder === f.name" name="check" class="w-3 h-3 ml-auto flex-shrink-0" />
            </button>
            <p v-if="!filteredFolders.length" class="px-3 py-1.5 text-xs text-ink-gray-4">
              {{ folderSearch ? "No matches" : "No folders yet" }}
            </p>
          </div>
        </div>

        <div class="border-t border-outline-gray-1 mx-1 my-1" />
        <button
          class="flex items-center gap-2 px-3 py-1.5 w-full text-left text-red-500 hover:bg-surface-red-1 transition-colors"
          @click="promptDelete(contextMenu.letter)"
        >
          <FeatherIcon name="trash-2" class="w-3.5 h-3.5" /> Delete
        </button>
      </div>
    </Teleport>

    <!-- Delete confirmation dialog -->
    <Teleport to="body">
      <div
        v-if="deleteDialog.show"
        class="fixed inset-0 z-[100] flex items-center justify-center"
        @click.self="deleteDialog.show = false"
      >
        <div class="absolute inset-0 bg-black/40" />
        <div class="relative bg-surface-base rounded-xl shadow-2xl w-96 p-6 border border-outline-gray-2" @click.stop>
          <div class="flex items-start gap-3 mb-5">
            <div class="w-9 h-9 rounded-full bg-surface-red-1 flex items-center justify-center flex-shrink-0 mt-0.5">
              <FeatherIcon name="trash-2" class="w-4 h-4 text-red-500" />
            </div>
            <div>
              <h3 class="text-sm font-semibold text-ink-gray-9 mb-1">Delete letter?</h3>
              <p class="text-sm text-ink-gray-5">
                "<span class="font-medium text-ink-gray-7">{{ deleteDialog.letter?.title }}</span>" will be permanently deleted. This cannot be undone.
              </p>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <Button variant="subtle" @click="deleteDialog.show = false">Cancel</Button>
            <Button variant="solid" theme="red" :loading="deleteDialog.deleting" @click="confirmDelete">Delete</Button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { FeatherIcon, Button, Dropdown } from "frappe-ui";
import LetterCard from "../components/LetterCard.vue";
import LetterThumbnail from "../components/LetterThumbnail.vue";

const props = defineProps({
  isDark: { type: Boolean, default: false },
  toggleDark: { type: Function, default: () => {} },
});
const emit = defineEmits(["open-letter", "new-letter"]);

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
const folderMenuOpen = ref(false);
const folderSearch = ref("");
const deleteDialog = ref({ show: false, letter: null, deleting: false });

const CONTEXT_MENU_W = 208;
const CONTEXT_MENU_H = 220;

const contextMenuStyle = computed(() => {
  const x = contextMenu.value.x + CONTEXT_MENU_W > window.innerWidth
    ? contextMenu.value.x - CONTEXT_MENU_W
    : contextMenu.value.x;
  const y = contextMenu.value.y + CONTEXT_MENU_H > window.innerHeight
    ? contextMenu.value.y - CONTEXT_MENU_H
    : contextMenu.value.y;
  return { top: `${y}px`, left: `${x}px` };
});

const filteredFolders = computed(() => {
  const q = folderSearch.value.toLowerCase();
  return q ? allFolders.value.filter((f) => f.name.toLowerCase().includes(q)) : allFolders.value;
});

const statusOptions = computed(() => [
  { label: "All",       value: null,        onClick: () => { activeStatus.value = null; } },
  { label: "Draft",     value: "Draft",     onClick: () => { activeStatus.value = "Draft"; } },
  { label: "Scheduled", value: "Scheduled", onClick: () => { activeStatus.value = "Scheduled"; } },
  { label: "Sending",   value: "Sending",   onClick: () => { activeStatus.value = "Sending"; } },
  { label: "Sent",      value: "Sent",      onClick: () => { activeStatus.value = "Sent"; } },
  { label: "Partial",   value: "Partial",   onClick: () => { activeStatus.value = "Partial"; } },
  { label: "Failed",    value: "Failed",    onClick: () => { activeStatus.value = "Failed"; } },
]);

const sortOptions = computed(() => [
  { label: "Last Modified",        value: "modified_desc", onClick: () => { sortBy.value = "modified_desc"; } },
  { label: "Last Created",         value: "creation_desc", onClick: () => { sortBy.value = "creation_desc"; } },
  { label: "Alphabetically (A–Z)", value: "title_asc",     onClick: () => { sortBy.value = "title_asc"; } },
  { label: "Alphabetically (Z–A)", value: "title_desc",    onClick: () => { sortBy.value = "title_desc"; } },
]);

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
    if (diff < 60)           return "Edited just now";
    if (diff < 3600)         return `Edited ${Math.floor(diff / 60)} mins ago`;
    if (diff < 86400)        return `Edited ${Math.floor(diff / 3600)} hours ago`;
    if (diff < 86400 * 14)   return `Edited ${Math.floor(diff / 86400)} days ago`;
    if (diff < 86400 * 60)   return `Edited ${Math.floor(diff / (86400 * 7))} weeks ago`;
    if (diff < 86400 * 365)  return `Edited ${Math.floor(diff / (86400 * 30))} months ago`;
    return `Edited ${Math.floor(diff / (86400 * 365))} years ago`;
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
    if (res.message?.name) { await load(); openLetter(res.message.name); }
  } catch (e) {
    frappe.msgprint(e.message || "Could not duplicate.");
  }
}

function viewInDesk(letter) {
  closeAll();
  frappe.set_route("Form", "Letter", letter.name);
}

function promptDelete(letter) {
  closeAll();
  deleteDialog.value = { show: true, letter, deleting: false };
}

async function confirmDelete() {
  deleteDialog.value.deleting = true;
  try {
    await frappe.call({
      method: "frappe.client.delete",
      args: { doctype: "Letter", name: deleteDialog.value.letter.name },
    });
    letters.value = letters.value.filter((l) => l.name !== deleteDialog.value.letter.name);
    deleteDialog.value.show = false;
  } catch (e) {
    frappe.msgprint(e.message || "Could not delete.");
    deleteDialog.value.deleting = false;
  }
}

function openLetter(name) { emit("open-letter", name); }

function closeAll() {
  contextMenu.value.visible = false;
  folderMenuOpen.value = false;
  folderSearch.value = "";
}

function openContextMenu(event, letter) {
  folderMenuOpen.value = false;
  folderSearch.value = "";
  contextMenu.value = { visible: true, x: event.clientX, y: event.clientY, letter };
}

async function moveToFolder(letter, folderName) {
  closeAll();
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

onMounted(load);
</script>
