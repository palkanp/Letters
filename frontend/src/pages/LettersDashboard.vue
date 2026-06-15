<template>
  <div class="flex h-screen bg-surface-gray-1 font-sans overflow-hidden">

    <!-- Sidebar -->
    <aside class="w-52 flex-shrink-0 bg-surface-base border-r border-outline-gray-1 flex flex-col py-4 px-3 gap-1">
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

      <div v-if="folders.length" class="mt-2">
        <p class="px-2 mb-1 text-[10px] font-semibold text-ink-gray-3 uppercase tracking-wide">Folders</p>
        <button
          v-for="f in folders"
          :key="f"
          class="flex items-center gap-2 px-2 py-1.5 rounded-md text-sm transition-colors w-full text-left"
          :class="activeFolder === f ? 'bg-surface-gray-3 text-ink-gray-9 font-medium' : 'text-ink-gray-6 hover:bg-surface-gray-2'"
          @click="activeFolder = f"
        >
          <FeatherIcon name="folder" class="w-3.5 h-3.5 flex-shrink-0" />
          <span class="truncate">{{ f }}</span>
        </button>
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
          <TextInput
            v-model="search"
            placeholder="Search…"
            class="w-44"
          />
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
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { FeatherIcon, Button, TextInput } from "frappe-ui";
import LetterCard from "../components/LetterCard.vue";

const emit = defineEmits(["open-letter"]);

const letters = ref([]);
const loading = ref(false);
const creating = ref(false);
const search = ref("");
const activeFolder = ref(null);

const folders = computed(() => {
  const set = new Set();
  letters.value.forEach((l) => { if (l.folder) set.add(l.folder); });
  return [...set].sort();
});

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

async function load() {
  loading.value = true;
  try {
    const res = await frappe.call({
      method: "letters.letters.api.get_letters",
    });
    letters.value = res.message || [];
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
      args: {},
    });
    if (res.message?.name) {
      openLetter(res.message.name);
    }
  } finally {
    creating.value = false;
  }
}

function openLetter(name) {
  emit("open-letter", name);
}

onMounted(load);
</script>
