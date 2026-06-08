import { defineStore } from "pinia";
import { ref, computed } from "vue";

let _idCounter = 0;

export const useEditorStore = defineStore("editor", () => {
  const blocks = ref([]);
  const renderedHtml = ref("");
  const campaignName = ref("");
  const campaignDoc = ref(null); // { name, title, subject, preview_text }
  const selectedBlockId = ref(null);

  const selectedBlock = computed(
    () => blocks.value.find((b) => b.id === selectedBlockId.value) || null
  );

  function addBlock(type) {
    const id = ++_idCounter;
    blocks.value.push({ id, type, props: defaultProps(type) });
    selectedBlockId.value = id; // select the block we just added
  }

  function removeBlock(id) {
    blocks.value = blocks.value.filter((b) => b.id !== id);
    if (selectedBlockId.value === id) selectedBlockId.value = null;
  }

  function moveBlock(fromIndex, toIndex) {
    const item = blocks.value.splice(fromIndex, 1)[0];
    blocks.value.splice(toIndex, 0, item);
  }

  function selectBlock(id) {
    selectedBlockId.value = id;
  }

  function updateBlockProps(id, props) {
    const block = blocks.value.find((b) => b.id === id);
    if (block) Object.assign(block.props, props);
  }

  function setRenderedHtml(html) {
    renderedHtml.value = html;
  }

  function loadFromDoc(doc) {
    campaignDoc.value = doc;
    campaignName.value = doc.title;
    _idCounter = 0;
    selectedBlockId.value = null;
    blocks.value = (doc.blocks || []).map((b) => ({ ...b, id: ++_idCounter }));
  }

  return {
    blocks,
    renderedHtml,
    campaignName,
    campaignDoc,
    selectedBlockId,
    selectedBlock,
    addBlock,
    removeBlock,
    moveBlock,
    selectBlock,
    updateBlockProps,
    setRenderedHtml,
    loadFromDoc,
  };
});

function defaultProps(type) {
  const defaults = {
    hero: {
      heading: "Your heading",
      subheading: "Your subheading",
      background_color: "#ffffff",
      text_align: "center",
      heading_color: "#111827",
      heading_size: "30px",
      subheading_color: "#6b7280",
      padding: "normal",
    },
    text: {
      content: "Start typing your message...",
      align: "left",
      font_size: "15px",
      font_weight: "400",
      text_color: "#374151",
    },
    image_text: {
      image_url: "",
      text: "Describe the image here. Keep it short and compelling.",
      image_position: "left",
      background_color: "#ffffff",
    },
    button: {
      label: "Click here",
      url: "#",
      color: "#6366f1",
      text_color: "#ffffff",
      align: "center",
      border_radius: "8px",
    },
    image: {
      image_url: "",
      caption: "",
      alt: "",
      background_color: "#ffffff",
      border: "0.5px solid #383838",
      border_radius: "0",
    },
    section_label: {
      label: "SECTION TITLE",
      text_color: "#383838",
      line_color: "#ededed",
      line_position: "below",
      align: "left",
    },
    columns: {
      column_count: "2",
      background_color: "#ffffff",
      heading_color: "#111827",
      text_color: "#6b7280",
      button_color: "#111827",
      columns: [
        { heading: "Column One", text: "Add your description here.", button_label: "", button_url: "" },
        { heading: "Column Two", text: "Add your description here.", button_label: "", button_url: "" },
      ],
    },
    divider: { border_color: "#e5e7eb", thickness: 1, style: "solid" },
    footer: {
      text: "You received this email because you signed up.",
      background_color: "#f9fafb",
      text_color: "#6b7280",
    },
  };
  return defaults[type] ?? {};
}
