// Declarative property schema for the right-side Inspector panel.
// Sections map to collapsible groups in the Inspector.
// Supported control types: "color", "select", "text", "number", "align".

export const BLOCK_SCHEMA = {
  hero: {
    label: "Hero",
    icon: "◉",
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
        ],
      },
      {
        id: "typography",
        title: "Typography",
        fields: [
          { key: "text_align", label: "Alignment", type: "align" },
          {
            key: "heading_size",
            label: "Heading size",
            type: "select",
            options: [
              { label: "Medium (24px)", value: "24px" },
              { label: "Large (30px)", value: "30px" },
              { label: "X-Large (36px)", value: "36px" },
            ],
          },
          { key: "heading_color", label: "Heading color", type: "color" },
          { key: "subheading_color", label: "Subheading color", type: "color" },
        ],
      },
      {
        id: "layout",
        title: "Layout",
        fields: [
          {
            key: "padding",
            label: "Vertical padding",
            type: "select",
            options: [
              { label: "Compact", value: "compact" },
              { label: "Normal", value: "normal" },
              { label: "Spacious", value: "spacious" },
            ],
          },
        ],
      },
    ],
  },

  text: {
    label: "Text",
    icon: "¶",
    sections: [
      {
        id: "typography",
        title: "Typography",
        fields: [
          { key: "align", label: "Alignment", type: "align" },
          {
            key: "font_size",
            label: "Font size",
            type: "select",
            options: [
              { label: "Small (13px)", value: "13px" },
              { label: "Normal (15px)", value: "15px" },
              { label: "Large (18px)", value: "18px" },
              { label: "X-Large (22px)", value: "22px" },
            ],
          },
          {
            key: "font_weight",
            label: "Weight",
            type: "select",
            options: [
              { label: "Normal", value: "400" },
              { label: "Medium", value: "500" },
              { label: "Semibold", value: "600" },
              { label: "Bold", value: "700" },
            ],
          },
          { key: "text_color", label: "Text color", type: "color" },
        ],
      },
    ],
  },

  image_text: {
    label: "Image + Text",
    icon: "▣",
    sections: [
      {
        id: "image",
        title: "Image",
        fields: [
          { key: "image_url", label: "Image URL", type: "text", placeholder: "https://…" },
          {
            key: "image_position",
            label: "Image side",
            type: "select",
            options: [
              { label: "Left", value: "left" },
              { label: "Right", value: "right" },
            ],
          },
          {
            key: "image_width",
            label: "Image width",
            type: "select",
            options: [
              { label: "Small (25%)", value: "25%" },
              { label: "Medium (33%)", value: "33%" },
              { label: "Half (50%)", value: "50%" },
              { label: "Large (175px)", value: "175px" },
            ],
          },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
        ],
      },
    ],
  },

  button: {
    label: "Button",
    icon: "▷",
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "url", label: "Link URL", type: "text", placeholder: "https://…" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "color", label: "Button color", type: "color" },
          { key: "text_color", label: "Text color", type: "color" },
          {
            key: "border_radius",
            label: "Corners",
            type: "select",
            options: [
              { label: "Sharp", value: "4px" },
              { label: "Rounded", value: "8px" },
              { label: "Pill", value: "999px" },
            ],
          },
        ],
      },
      {
        id: "layout",
        title: "Layout",
        fields: [
          { key: "align", label: "Alignment", type: "align" },
        ],
      },
    ],
  },

  divider: {
    label: "Divider",
    icon: "—",
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "border_color", label: "Color", type: "color" },
          {
            key: "style",
            label: "Line style",
            type: "select",
            options: [
              { label: "Solid", value: "solid" },
              { label: "Dashed", value: "dashed" },
              { label: "Dotted", value: "dotted" },
            ],
          },
          { key: "thickness", label: "Thickness (px)", type: "number", min: 1, max: 10 },
        ],
      },
    ],
  },

  footer: {
    label: "Footer",
    icon: "≡",
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          { key: "text_color", label: "Text color", type: "color" },
        ],
      },
    ],
  },
};
