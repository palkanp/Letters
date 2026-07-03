// Compound block presets — each becomes a real container with editable child blocks.
// insertBuiltBlock in editor.js applies BLOCK_SCHEMA defaults first, then overlays these props.
//
// Rule: wherever a preset has distinct column sections (image area, text area, etc.),
// each section gets its own inner container so it can be styled and expanded independently.

export const BLOCK_PRESET_TYPES = new Set([
  "header", "hero", "image_text", "product_card", "quote", "link_list", "footer",
  "two_col", "three_col", "text_cols", "video_thumb",
]);

// Shared zero-padding helper (inner containers that let children handle their own spacing)
const noPad = { padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 };

export const BLOCK_PRESET_DEFS = {

  // ── Logo / Header ──────────────────────────────────────────────────────────
  // Outer column container → inner containers for logo area and tagline area
  header: {
    type: "container", label: "Logo",
    props: { layout: "column", background_color: "#ffffff", align: "center", gap: 0,
             padding_top: 20, padding_right: 0, padding_bottom: 20, padding_left: 0 },
    children: [
      { type: "image", label: "Logo",
        props: { alt: "Logo", background_color: "transparent", height_class: "h-10", compact: true,
                 padding_top: 0, padding_right: 200, padding_bottom: 0, padding_left: 200 } },
    ],
  },

  // ── Hero ───────────────────────────────────────────────────────────────────
  // Outer column container → inner containers for heading area and body area
  hero: {
    type: "container", label: "Hero",
    props: { layout: "column", background_color: "#ffffff", align: "center", gap: 0,
             padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "container", label: "Heading area",
        props: { layout: "column", background_color: "transparent", align: "center", gap: 0,
                 padding_top: 48, padding_right: 32, padding_bottom: 12, padding_left: 32 },
        children: [
          { type: "text", label: "Heading",
            props: { html_content: "<p>Your Headline Here</p>", align: "center",
                     font_size: "32px", font_weight: "700", text_color: "#111827", line_height: "1.3",
                     background_color: "transparent", ...noPad } },
        ],
      },
      {
        type: "container", label: "Body area",
        props: { layout: "column", background_color: "transparent", align: "center", gap: 0,
                 padding_top: 0, padding_right: 32, padding_bottom: 48, padding_left: 32 },
        children: [
          { type: "text", label: "Subheading",
            props: { html_content: "<p>Supporting text that explains your offer in one or two sentences.</p>",
                     align: "center", font_size: "16px", text_color: "#6b7280", line_height: "1.6",
                     background_color: "transparent", ...noPad } },
        ],
      },
    ],
  },

  // ── Image + Text ───────────────────────────────────────────────────────────
  // Outer row container → left container (image) + right container (text)
  image_text: {
    type: "container", label: "Image + Text",
    props: { layout: "row", background_color: "#ffffff", vertical_align: "center", gap: 0,
             padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "container", label: "Image column",
        props: { layout: "column", background_color: "transparent", vertical_align: "flex-start", gap: 0,
                 padding_top: 24, padding_right: 12, padding_bottom: 24, padding_left: 24 },
        children: [
          { type: "image", label: "Image",
            props: { background_color: "transparent", border_radius: "8px", ...noPad } },
        ],
      },
      {
        type: "container", label: "Text column",
        props: { layout: "column", background_color: "transparent", vertical_align: "flex-start", gap: 8,
                 padding_top: 24, padding_right: 24, padding_bottom: 24, padding_left: 12 },
        children: [
          { type: "text", label: "Heading",
            props: { html_content: "<p><strong>Section heading</strong></p>",
                     font_size: "18px", font_weight: "700", text_color: "#111827", line_height: "1.4",
                     background_color: "transparent", ...noPad } },
          { type: "text", label: "Body",
            props: { html_content: "<p>Describe the image here. Keep it short and compelling.</p>",
                     font_size: "15px", text_color: "#374151", line_height: "1.6",
                     background_color: "transparent", ...noPad } },
        ],
      },
    ],
  },

  // ── Product Card ───────────────────────────────────────────────────────────
  // Image (full-width, no padding) → content: name, description, price + CTA row
  product_card: {
    type: "container", label: "Product Card",
    props: { layout: "column", background_color: "#ffffff", gap: 0,
             padding_top: 24, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "container", label: "Image section",
        props: { layout: "column", background_color: "transparent", gap: 0, ...noPad },
        children: [
          { type: "image", label: "Product Image",
            props: { alt: "Product image", background_color: "transparent",
                     border_radius: "0", padding_top: 0, padding_right: 24, padding_bottom: 0, padding_left: 24 } },
        ],
      },
      {
        type: "container", label: "Content section",
        props: { layout: "column", background_color: "transparent", gap: 12,
                 padding_top: 16, padding_right: 24, padding_bottom: 20, padding_left: 24 },
        children: [
          { type: "text", label: "Product Name",
            props: { html_content: "<p><strong>Product Name</strong></p>", align: "left",
                     font_size: "18px", font_weight: "700", text_color: "#111827", line_height: "1.3",
                     background_color: "transparent", ...noPad } },
          { type: "text", label: "Description",
            props: { html_content: "<p>Short description that highlights the key benefits.</p>",
                     align: "left", font_size: "14px", text_color: "#6b7280", line_height: "1.6",
                     background_color: "transparent", ...noPad } },
          {
            type: "container", label: "Price + CTA",
            props: { layout: "row", background_color: "transparent", vertical_align: "center",
                     gap: 0, mobile_stack: false, ...noPad },
            children: [
              { type: "text", label: "Price",
                props: { html_content: "<p><strong>$450</strong></p>", align: "left",
                         font_size: "18px", font_weight: "700", text_color: "#111827", line_height: "1.3",
                         background_color: "transparent", ...noPad } },
              { type: "button", label: "CTA Button",
                props: { label: "Click here", url: "#", align: "right",
                         color: "#111827", text_color: "#ffffff",
                         border_radius: "8px", padding_right: 0 } },
            ],
          },
        ],
      },
    ],
  },

  // ── Quote ──────────────────────────────────────────────────────────────────
  // Outer container → quote section + author section
  quote: {
    type: "container", label: "Quote",
    props: { layout: "column", background_color: "#f9fafb", gap: 0,
             padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "container", label: "Quote section",
        props: { layout: "column", background_color: "transparent", gap: 0,
                 padding_top: 28, padding_right: 32, padding_bottom: 12, padding_left: 32 },
        children: [
          { type: "text", label: "Quote text",
            props: { html_content: '<p><em>"This is a wonderful product that changed how we work."</em></p>',
                     font_family: "Georgia", font_size: "17px", text_color: "#111827", line_height: "1.7",
                     background_color: "transparent", ...noPad } },
        ],
      },
      {
        type: "container", label: "Author section",
        props: { layout: "column", background_color: "transparent", gap: 0,
                 padding_top: 0, padding_right: 32, padding_bottom: 28, padding_left: 32 },
        children: [
          { type: "text", label: "Author",
            props: { html_content: "<p>— Jane Doe, CEO at Acme Inc.</p>",
                     font_size: "13px", text_color: "#6b7280", line_height: "1.5",
                     background_color: "transparent", ...noPad } },
        ],
      },
    ],
  },

  // ── Text Columns ───────────────────────────────────────────────────────────
  // Row container with 3 equal text blocks separated by thin vertical dividers.
  // gap:0 + compact divider padding keeps the layout tight without manual fiddling.
  text_cols: {
    type: "container", label: "Text Columns",
    props: { layout: "row", background_color: "#ffffff", vertical_align: "center", gap: 0,
             padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "text", label: "Column 1",
        props: { html_content: "<p>Column content</p>", align: "left",
                 font_size: "15px", text_color: "#374151", line_height: "1.6",
                 background_color: "transparent",
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
      },
      {
        type: "divider", label: "Divider",
        props: { orientation: "vertical", border_color: "#e5e7eb", thickness: 1, style: "solid",
                 height: 40,
                 padding_top: 0, padding_right: 8, padding_bottom: 0, padding_left: 8 },
      },
      {
        type: "text", label: "Column 2",
        props: { html_content: "<p>Column content</p>", align: "left",
                 font_size: "15px", text_color: "#374151", line_height: "1.6",
                 background_color: "transparent",
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
      },
      {
        type: "divider", label: "Divider",
        props: { orientation: "vertical", border_color: "#e5e7eb", thickness: 1, style: "solid",
                 height: 40,
                 padding_top: 0, padding_right: 8, padding_bottom: 0, padding_left: 8 },
      },
      {
        type: "text", label: "Column 3",
        props: { html_content: "<p>Column content</p>", align: "left",
                 font_size: "15px", text_color: "#374151", line_height: "1.6",
                 background_color: "transparent",
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
      },
    ],
  },

  // ── Link List ──────────────────────────────────────────────────────────────
  // Outer container → heading section + links section
  link_list: {
    type: "container", label: "Link List",
    props: { layout: "column", background_color: "#ffffff", gap: 0,
             padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "container", label: "Heading section",
        props: { layout: "column", background_color: "transparent", gap: 0,
                 padding_top: 20, padding_right: 24, padding_bottom: 12, padding_left: 24 },
        children: [
          { type: "text", label: "Heading",
            props: { html_content: "<p><strong>Must Read</strong></p>", font_size: "11px", font_weight: "700",
                     text_color: "#9ca3af", line_height: "1.5", letter_spacing: "0.08em",
                     background_color: "transparent", ...noPad } },
        ],
      },
      {
        type: "container", label: "Links section",
        props: { layout: "column", background_color: "transparent", gap: 4,
                 padding_top: 0, padding_right: 24, padding_bottom: 20, padding_left: 24 },
        children: [
          { type: "text", label: "Link 1",
            props: { html_content: '<p><a href="#" style="color:#2563eb;text-decoration:none">→ Article title or announcement</a></p>',
                     font_size: "15px", text_color: "#111827", line_height: "1.5",
                     background_color: "transparent", ...noPad } },
          { type: "text", label: "Link 2",
            props: { html_content: '<p><a href="#" style="color:#2563eb;text-decoration:none">→ Another article or resource</a></p>',
                     font_size: "15px", text_color: "#111827", line_height: "1.5",
                     background_color: "transparent", ...noPad } },
          { type: "text", label: "Link 3",
            props: { html_content: '<p><a href="#" style="color:#2563eb;text-decoration:none">→ One more link for the reader</a></p>',
                     font_size: "15px", text_color: "#111827", line_height: "1.5",
                     background_color: "transparent", ...noPad } },
        ],
      },
    ],
  },

  // ── 2 Columns ──────────────────────────────────────────────────────────────
  // Row container with two equal inner containers
  two_col: {
    type: "container", label: "2 Columns",
    props: { layout: "row", background_color: "#ffffff", vertical_align: "flex-start", gap: 16,
             ...noPad },
    children: [
      {
        type: "container", label: "Column 1",
        props: { layout: "column", background_color: "transparent", gap: 8,
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
        children: [],
      },
      {
        type: "container", label: "Column 2",
        props: { layout: "column", background_color: "transparent", gap: 8,
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
        children: [],
      },
    ],
  },

  // ── 3 Columns ──────────────────────────────────────────────────────────────
  three_col: {
    type: "container", label: "3 Columns",
    props: { layout: "row", background_color: "#ffffff", vertical_align: "flex-start", gap: 16,
             ...noPad },
    children: [
      {
        type: "container", label: "Column 1",
        props: { layout: "column", background_color: "transparent", gap: 8,
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
        children: [],
      },
      {
        type: "container", label: "Column 2",
        props: { layout: "column", background_color: "transparent", gap: 8,
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
        children: [],
      },
      {
        type: "container", label: "Column 3",
        props: { layout: "column", background_color: "transparent", gap: 8,
                 padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
        children: [],
      },
    ],
  },

  // ── Video Thumbnail ────────────────────────────────────────────────────────
  // Container → image block (thumbnail, links to video) + text block (caption)
  video_thumb: {
    type: "container", label: "Video",
    props: { layout: "column", background_color: "#ffffff", gap: 0,
             padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16 },
    children: [
      { type: "video_thumb", label: "Thumbnail",
        props: { thumbnail_url: "", video_url: "#", caption: "",
                 border_radius: "8px", background_color: "transparent",
                 ...noPad } },
      { type: "text", label: "Caption",
        props: { html_content: "<p>Watch the video</p>",
                 align: "center", font_size: "13px", text_color: "#374151",
                 background_color: "transparent",
                 padding_top: 8, padding_right: 0, padding_bottom: 0, padding_left: 0 } },
    ],
  },

  // ── Section Label ──────────────────────────────────────────────────────────
  // Outer container → text block (uppercase label) + divider block
  section_label: {
    type: "container", label: "Section Label",
    props: { layout: "column", background_color: "transparent", gap: 0,
             padding_top: 12, padding_right: 16, padding_bottom: 12, padding_left: 16 },
    children: [
      { type: "text", label: "Label text",
        props: { html_content: "<p>SECTION TITLE</p>",
                 font_size: "11px", font_weight: "600", text_color: "#383838",
                 letter_spacing: "0.15em", line_height: "1.2",
                 background_color: "transparent", ...noPad } },
      { type: "divider", label: "Divider line",
        props: { border_color: "#ededed", thickness: 0.5, style: "solid", width: "100%",
                 padding_top: 8, padding_right: 0, padding_bottom: 0, padding_left: 0 } },
    ],
  },

  // ── Footer ─────────────────────────────────────────────────────────────────
  // Simple: outer container → text section
  footer: {
    type: "container", label: "Footer",
    props: { layout: "column", background_color: "#f9fafb", align: "center", gap: 0,
             padding_top: 0, padding_right: 0, padding_bottom: 0, padding_left: 0 },
    children: [
      {
        type: "container", label: "Footer text section",
        props: { layout: "column", background_color: "transparent", align: "center", gap: 0,
                 padding_top: 20, padding_right: 24, padding_bottom: 20, padding_left: 24 },
        children: [
          { type: "text", label: "Footer text",
            props: { html_content: "<p>You received this email because you signed up.</p>",
                     align: "center", font_size: "12px", text_color: "#6b7280", line_height: "1.6",
                     background_color: "transparent", ...noPad } },
        ],
      },
    ],
  },

};
