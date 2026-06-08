import { defineStore } from "pinia";
import { ref } from "vue";

let _idCounter = 0;

export const useEditorStore = defineStore("editor", () => {
  const blocks = ref([]);
  const renderedHtml = ref("");
  const campaignName = ref("");
  const campaignDoc = ref(null); // { name, title, subject, preview_text }

  function addBlock(type) {
    blocks.value.push({ id: ++_idCounter, type, props: defaultProps(type) });
  }

  function removeBlock(id) {
    blocks.value = blocks.value.filter((b) => b.id !== id);
  }

  function moveBlock(fromIndex, toIndex) {
    const item = blocks.value.splice(fromIndex, 1)[0];
    blocks.value.splice(toIndex, 0, item);
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
    blocks.value = (doc.blocks || []).map((b) => ({ ...b, id: ++_idCounter }));
  }

  return {
    blocks,
    renderedHtml,
    campaignName,
    campaignDoc,
    addBlock,
    removeBlock,
    moveBlock,
    updateBlockProps,
    setRenderedHtml,
    loadFromDoc,
  };
});

function defaultProps(type) {
  const defaults = {
    hero: { heading: "Your heading", subheading: "Your subheading", background_color: "#ffffff" },
    text: { content: "Start typing your message...", align: "left", font_size: "16px" },
    image_text: { image_url: "", text: "Describe the image", image_position: "left" },
    button: { label: "Click here", url: "#", color: "#6366f1", text_color: "#ffffff", align: "center" },
    divider: { border_color: "#e0e0e0", thickness: 1, style: "solid" },
    footer: { text: "You received this email because you signed up.", background_color: "#f9fafb", text_color: "#6b7280" },
  };
  return defaults[type] ?? {};
}
