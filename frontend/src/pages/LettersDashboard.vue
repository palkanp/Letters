<template>
  <div class="flex h-screen bg-surface-base font-sans overflow-hidden" @click="closeAll">

    <!-- Sidebar -->
    <aside
      class="w-52 flex-shrink-0 border-r border-outline-gray-1 flex flex-col"
      :class="props.isDark ? '' : 'bg-surface-gray-1'"
      :style="props.isDark ? { background: '#111111' } : {}"
    >
      <!-- App header -->
      <div class="flex items-center gap-2.5 px-4 py-3.5 border-b border-outline-gray-1 h-[53px]">
        <div
          class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold"
          :class="props.isDark ? '' : 'bg-surface-gray-3 text-ink-gray-6'"
          :style="props.isDark ? 'background:rgba(255,255,255,0.12);color:rgba(255,255,255,0.55)' : ''"
        >
          L
        </div>
        <span
          class="text-sm font-semibold flex-1"
          :class="props.isDark ? '' : 'text-ink-gray-7'"
          :style="props.isDark ? 'color:rgba(255,255,255,0.65)' : ''"
        >Letters</span>
        <Button
          variant="ghost"
          :icon="props.isDark ? 'lucide-sun' : 'lucide-moon'"
          size="sm"
          :title="props.isDark ? 'Switch to light' : 'Switch to dark'"
          aria-label="Toggle theme"
          @click.stop="props.toggleDark()"
        />
      </div>

      <!-- Nav -->
      <div class="px-3 py-3 flex flex-col gap-0.5">
        <Button
          variant="ghost"
          class="w-full !justify-start px-2 py-1.5 text-sm"
          :class="activeFolder === null
            ? (props.isDark ? '!bg-white/10 !text-white/70 font-medium' : '!bg-surface-base !text-ink-gray-8 font-medium')
            : (props.isDark ? '!text-white/55' : 'text-ink-gray-6')"
          @click="activeFolder = null"
        >
          <template #prefix>
            <span class="lucide-inbox size-3.5 flex-shrink-0" aria-hidden="true" />
          </template>
          All Letters
          <template #suffix>
            <span class="ml-auto text-xs tabular-nums" :class="props.isDark ? 'text-ink-gray-3' : 'text-ink-gray-4'">{{ letters.length }}</span>
          </template>
        </Button>
      </div>

      <!-- Folders -->
      <div class="px-3 flex-1 overflow-y-auto">
        <div class="flex items-center justify-between px-2 mb-1">
          <p
            class="text-[10px] font-semibold uppercase tracking-wide"
            :class="props.isDark ? '' : 'text-ink-gray-4'"
            :style="props.isDark ? 'color:rgba(255,255,255,0.38)' : ''"
          >Category</p>
          <Button
            variant="ghost"
            icon="lucide-plus"
            size="sm"
            title="New category"
            aria-label="New category"
            class="!w-5 !h-5"
            @click.stop="startNewFolder"
          />
        </div>

        <div v-if="creatingFolder" class="flex items-center gap-1.5 px-2 py-1 mb-0.5">
          <span class="lucide-folder size-3.5 text-ink-gray-4 flex-shrink-0" aria-hidden="true" />
          <TextInput
            ref="folderInput"
            v-model="newFolderName"
            size="sm"
            class="flex-1 min-w-0"
            placeholder="Category name"
            @keydown.enter="saveNewFolder"
            @keydown.escape="cancelNewFolder"
            @blur="saveNewFolder"
          />
        </div>

        <Button
          v-for="f in allFolders"
          :key="f.name"
          variant="ghost"
          class="w-full !justify-start px-2 py-1.5 text-sm"
          :class="activeFolder === f.name
            ? (props.isDark ? '!bg-white/10 !text-white/70 font-medium' : '!bg-surface-base !text-ink-gray-8 font-medium')
            : (props.isDark ? '!text-white/55' : 'text-ink-gray-6')"
          @click="activeFolder = f.name"
        >
          <template #prefix>
            <span class="lucide-folder size-3.5 flex-shrink-0" aria-hidden="true" />
          </template>
          {{ f.name }}
          <template #suffix>
            <span class="ml-auto text-[10px] tabular-nums" :class="props.isDark ? 'text-ink-gray-3' : 'text-ink-gray-4'">{{ folderCount(f.name) }}</span>
          </template>
        </Button>

        <p v-if="!allFolders.length && !creatingFolder" class="px-2 text-xs mt-1" :class="props.isDark ? 'text-ink-gray-3' : 'text-ink-gray-4'">No categories yet</p>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Header -->
      <header
        class="flex items-center justify-between px-6 border-b border-outline-gray-1 flex-shrink-0 gap-3 h-[53px]"
        :class="props.isDark ? 'bg-black' : 'bg-surface-base'"
      >
        <h1 class="text-base font-semibold flex-shrink-0" :class="props.isDark ? 'text-ink-gray-7' : 'text-ink-gray-8'">{{ activeFolder || "All Letters" }}</h1>

        <div class="flex items-center gap-2 flex-1 justify-end">
          <TextInput
            v-model="search"
            placeholder="Filter by title…"
            size="sm"
            class="w-48"
          >
            <template #prefix>
              <span class="lucide-search size-3.5 text-ink-gray-4" aria-hidden="true" />
            </template>
          </TextInput>

          <Dropdown :options="statusOptions">
            <Button
              size="sm"
              :variant="activeStatus ? 'outline' : 'ghost'"
              class="gap-1.5"
              :class="props.isDark ? '!text-ink-gray-6' : '!text-ink-gray-7'"
            >
              {{ activeStatus || "Status" }}
              <template #suffix>
                <span
                  v-if="activeStatus"
                  class="lucide-x size-3 opacity-60"
                  aria-hidden="true"
                  @click.stop="activeStatus = null"
                />
                <span v-else class="lucide-chevron-down size-3" aria-hidden="true" />
              </template>
            </Button>
          </Dropdown>

          <Dropdown :options="sortOptions">
            <Button variant="ghost" size="sm" class="gap-1.5" :class="props.isDark ? '!text-ink-gray-6' : '!text-ink-gray-7'">
              {{ sortOptions.find(s => s.value === sortBy)?.label || 'Last Modified' }}
              <template #suffix>
                <span class="lucide-chevron-down size-3" aria-hidden="true" />
              </template>
            </Button>
          </Dropdown>

          <div class="flex border border-outline-gray-1 rounded-md overflow-hidden" :class="props.isDark ? '' : 'bg-surface-gray-2'">
            <Button
              variant="ghost"
              icon="lucide-layout-grid"
              size="sm"
              class="!rounded-none"
              :class="viewMode === 'grid'
                ? (props.isDark ? '!bg-white/25 !text-white/70' : '!bg-surface-base !text-ink-gray-8')
                : (props.isDark ? '!text-white/40' : 'text-ink-gray-4')"
              aria-label="Grid view"
              data-testid="view-grid"
              @click="viewMode = 'grid'"
            />
            <Button
              variant="ghost"
              icon="lucide-list"
              size="sm"
              class="!rounded-none border-l border-outline-gray-1"
              :class="viewMode === 'list'
                ? (props.isDark ? '!bg-white/25 !text-white/70' : '!bg-surface-base !text-ink-gray-8')
                : (props.isDark ? '!text-white/40' : 'text-ink-gray-4')"
              aria-label="List view"
              data-testid="view-list"
              @click="viewMode = 'list'"
            />
          </div>

          <Button variant="solid" icon-left="lucide-plus" @click="createNew">
            New Letter
          </Button>
        </div>
      </header>

      <!-- Content -->
      <div class="flex-1 overflow-y-auto pt-12 pb-6" :class="props.isDark ? 'bg-black' : 'bg-surface-base'">
        <div class="max-w-[1000px] mx-auto px-6">
        <div v-if="loading" class="flex items-center justify-center h-48 text-ink-gray-4 text-sm gap-2">
          <span class="lucide-loader size-4 animate-spin" aria-hidden="true" /> Loading…
        </div>

        <div v-else-if="!visibleLetters.length" class="flex flex-col items-center justify-center h-48 gap-3">
          <span class="lucide-mail size-10 text-ink-gray-3" aria-hidden="true" />
          <p class="text-sm text-ink-gray-5">{{ search || activeStatus ? "No letters match your filters." : "No letters yet." }}</p>
          <Button v-if="!search && !activeStatus" variant="subtle" icon-left="lucide-plus" @click="createNew">
            Create your first letter
          </Button>
        </div>

        <!-- Grid view -->
        <div v-else-if="viewMode === 'grid'" class="grid grid-cols-4 gap-x-4 gap-y-2">
          <LetterCard
            v-for="l in visibleLetters"
            :key="l.name"
            :letter="l"
            :is-dark="props.isDark"
            @open="openLetter"
            @menu="(e) => openContextMenu(e, l)"
            @contextmenu.prevent="openContextMenu($event, l)"
          />
        </div>

        <!-- List view -->
        <div v-else class="flex flex-col">
          <template v-for="(l, idx) in visibleLetters" :key="l.name">
          <div v-if="idx > 0" class="mx-4 border-t border-outline-gray-1" />
          <div
            class="flex items-center gap-4 px-4 py-3 rounded-xl cursor-pointer transition-colors"
            :class="props.isDark ? 'hover:bg-white/10' : 'hover:bg-surface-gray-2'"
            @click="openLetter(l.name)"
            @contextmenu.prevent="openContextMenu($event, l)"
          >
            <div class="w-36 h-24 rounded-md flex-shrink-0 overflow-hidden" :class="props.isDark ? '' : 'border border-outline-gray-2 shadow-sm'">
              <LetterThumbnail :name="l.name" icon-class="w-5 h-5" />
            </div>
            <div class="flex-1 min-w-0 flex flex-col self-stretch justify-between py-0.5">
              <div class="min-w-0">
                <p class="text-sm font-medium truncate" :class="props.isDark ? 'text-ink-gray-7' : 'text-ink-gray-8'">{{ l.title }}</p>
                <p class="text-xs truncate mt-0.5" :class="props.isDark ? 'text-ink-gray-5' : 'text-ink-gray-5'">{{ l.subject || "No subject" }}</p>
              </div>
              <p class="text-xs" :class="props.isDark ? 'text-ink-gray-4' : 'text-ink-gray-4'">{{ relativeTime(l.modified) }}</p>
            </div>
            <div class="flex-shrink-0 w-20 flex justify-center">
              <Badge :theme="badgeTheme(l.status)" :label="l.status" size="sm" variant="subtle" class="!px-2.5 !py-1" />
            </div>
            <Button
              variant="ghost"
              icon="lucide-ellipsis"
              size="sm"
              class="flex-shrink-0"
              aria-label="More options"
              @click.stop="openContextMenu($event, l)"
            />
          </div>
          </template>
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
        <Button
          variant="ghost"
          class="w-full !justify-start px-3 py-1.5 text-ink-gray-7"
          iconLeft="lucide-copy"
          @click="duplicateLetter(contextMenu.letter); closeAll()"
        >
          Duplicate
        </Button>
        <Button
          variant="ghost"
          class="w-full !justify-start px-3 py-1.5 text-ink-gray-7"
          iconLeft="lucide-external-link"
          @click="viewInDesk(contextMenu.letter)"
        >
          View in Desk
        </Button>

        <!-- Move to category — inline toggle -->
        <Button
          variant="ghost"
          class="w-full !justify-start px-3 py-1.5 text-ink-gray-7"
          iconLeft="lucide-folder"
          @click.stop="folderMenuOpen = !folderMenuOpen"
        >
          Move to category
          <template #suffix>
            <span :class="`lucide-${folderMenuOpen ? 'chevron-up' : 'chevron-down'} size-3 ml-auto text-ink-gray-4`" aria-hidden="true" />
          </template>
        </Button>

        <!-- Inline folder list -->
        <div v-if="folderMenuOpen" class="border-t border-outline-gray-1 mx-1 mt-0.5">
          <div class="px-2 py-1.5">
            <TextInput
              v-model="folderSearch"
              placeholder="Search…"
              size="sm"
              @click.stop
            />
          </div>
          <div class="max-h-40 overflow-y-auto pb-1">
            <Button
              v-if="contextMenu.letter?.folder"
              variant="ghost"
              class="w-full !justify-start px-3 py-1.5 text-ink-gray-6 text-xs"
              iconLeft="lucide-x"
              @click="moveToFolder(contextMenu.letter, null)"
            >
              Remove from folder
            </Button>
            <Button
              v-for="f in filteredFolders"
              :key="f.name"
              variant="ghost"
              class="w-full !justify-start px-3 py-1.5 text-xs"
              :class="contextMenu.letter?.folder === f.name ? 'text-ink-gray-4 cursor-default' : 'text-ink-gray-7'"
              :disabled="contextMenu.letter?.folder === f.name"
              @click="contextMenu.letter?.folder !== f.name && moveToFolder(contextMenu.letter, f.name)"
            >
              <template #prefix>
                <span class="lucide-folder size-3 flex-shrink-0" aria-hidden="true" />
              </template>
              {{ f.name }}
              <template #suffix>
                <span v-if="contextMenu.letter?.folder === f.name" class="lucide-check size-3 ml-auto flex-shrink-0" aria-hidden="true" />
              </template>
            </Button>
            <p v-if="!filteredFolders.length" class="px-3 py-1.5 text-xs text-ink-gray-4">
              {{ folderSearch ? "No matches" : "No folders yet" }}
            </p>
          </div>
        </div>

        <div class="border-t border-outline-gray-1 mx-1 my-1" />
        <Button
          variant="ghost"
          theme="red"
          class="w-full !justify-start px-3 py-1.5"
          iconLeft="lucide-trash-2"
          @click="promptDelete(contextMenu.letter)"
        >
          Delete
        </Button>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { Button, Dropdown, TextInput, Badge, dialog } from "frappe-ui";
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

function badgeTheme(status) {
  const map = {
    Draft:     "gray",
    Scheduled: "orange",
    Sending:   "blue",
    Sent:      "green",
    Partial:   "orange",
    Failed:    "red",
  };
  return map[status] || "gray";
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
    const [lettersRes, foldersRes] = await Promise.allSettled([
      frappe.call({ method: "letters.letters.api.get_letters" }),
      frappe.call({ method: "frappe.client.get_list", args: { doctype: "Letter Category", fields: ["name"], order_by: "name asc", limit: 200 } }),
    ]);
    letters.value = lettersRes.status === "fulfilled" ? (lettersRes.value?.message || []) : [];
    allFolders.value = foldersRes.status === "fulfilled" ? (foldersRes.value?.message || []) : [];
  } finally {
    loading.value = false;
  }
}

function createNew() {
  emit("new-letter");
}

async function duplicateLetter(letter) {
  try {
    const res = await frappe.call({
      method: "letters.letters.api.duplicate_letter",
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
  dialog.confirm({
    title: "Delete letter?",
    message: `"${letter.title}" will be permanently deleted. This cannot be undone.`,
    theme: "red",
    onConfirm: async ({ close }) => {
      try {
        await frappe.call({
          method: "frappe.client.delete",
          args: { doctype: "Letter", name: letter.name },
        });
        letters.value = letters.value.filter((l) => l.name !== letter.name);
        close();
      } catch (e) {
        frappe.msgprint(e.message || "Could not delete.");
      }
    },
  });
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
      args: { doc: { doctype: "Letter Category", folder_name: name } },
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
