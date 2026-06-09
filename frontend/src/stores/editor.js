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

  function addBlock(type, afterIndex = null) {
    const id = ++_idCounter;
    const newBlock = { id, type, props: defaultProps(type) };
    if (afterIndex === null || afterIndex === undefined) {
      blocks.value.push(newBlock);
    } else if (afterIndex < 0) {
      blocks.value.unshift(newBlock);
    } else {
      blocks.value.splice(afterIndex + 1, 0, newBlock);
    }
    selectedBlockId.value = id;
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
      padding_top: 40, padding_right: 32, padding_bottom: 40, padding_left: 32,
    },
    text: {
      content: "Start typing your message...",
      align: "left",
      font_size: "15px",
      font_weight: "400",
      text_color: "#374151",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
    image_text: {
      image_url: "",
      text: "Describe the image here. Keep it short and compelling.",
      image_position: "left",
      image_width: "160px",
      layout_mode: "side",
      background_color: "#ffffff",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
    button: {
      label: "Click here",
      url: "#",
      color: "#111827",
      text_color: "#ffffff",
      align: "center",
      border_radius: "8px",
      font_size: "14px",
      button_padding: "normal",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
    image: {
      image_url: "",
      caption: "",
      alt: "",
      background_color: "#ffffff",
      border: "0.5px solid #383838",
      border_radius: "0",
      padding_top: 16, padding_right: 32, padding_bottom: 16, padding_left: 32,
    },
    section_label: {
      label: "SECTION TITLE",
      text_color: "#383838",
      line_color: "#ededed",
      line_position: "below",
      align: "left",
      padding_top: 12, padding_right: 32, padding_bottom: 12, padding_left: 32,
    },
    columns: {
      column_count: "2",
      background_color: "#ffffff",
      heading_color: "#111827",
      text_color: "#6b7280",
      button_color: "#111827",
      show_dividers: false,
      divider_color: "#e5e7eb",
      col_gap: 24,
      columns: [
        { heading: "", text: "Add your text here.", button_label: "", button_url: "" },
        { heading: "", text: "Add your text here.", button_label: "", button_url: "" },
      ],
      padding_top: 20, padding_right: 24, padding_bottom: 20, padding_left: 24,
    },
    container: {
      heading: "",
      text: "",
      background_color: "#f8fafc",
      border_color: "#e2e8f0",
      border_radius: "12px",
      padding_top: 24, padding_right: 24, padding_bottom: 24, padding_left: 24,
    },
    divider: {
      border_color: "#e5e7eb", thickness: 1, style: "solid",
      width: "100%", align: "center",
      padding_top: 16, padding_right: 32, padding_bottom: 16, padding_left: 32,
    },
    footer: {
      text: "You received this email because you signed up.",
      background_color: "#f9fafb",
      text_color: "#6b7280",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
  };
  return defaults[type] ?? {};
}
