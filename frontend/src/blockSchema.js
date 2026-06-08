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
          {
            key: "line_height",
            label: "Line height",
            type: "select",
            options: [
              { label: "Tight (1.3)", value: "1.3" },
              { label: "Snug (1.4)", value: "1.4" },
              { label: "Normal (1.6)", value: "1.6" },
              { label: "Relaxed (1.75)", value: "1.75" },
              { label: "Loose (2.0)", value: "2.0" },
            ],
          },
          {
            key: "letter_spacing",
            label: "Letter spacing",
            type: "select",
            options: [
              { label: "Normal", value: "normal" },
              { label: "Tight (−0.5px)", value: "-0.5px" },
              { label: "Wide (0.3px)", value: "0.3px" },
              { label: "Wider (0.99px)", value: "0.99px" },
            ],
          },
        ],
      },
    ],
  },

  image: {
    label: "Image",
    icon: "🖼",
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "image_url", label: "Image URL", type: "text", placeholder: "https://…" },
          { key: "caption", label: "Caption", type: "text", placeholder: "Optional caption…" },
          { key: "alt", label: "Alt text", type: "text", placeholder: "Describe the image…" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          {
            key: "border",
            label: "Border",
            type: "select",
            options: [
              { label: "None", value: "none" },
              { label: "Subtle (0.5px)", value: "0.5px solid #383838" },
              { label: "Light (1px gray)", value: "1px solid #e5e7eb" },
              { label: "Medium (2px)", value: "2px solid #383838" },
            ],
          },
          {
            key: "border_radius",
            label: "Corners",
            type: "select",
            options: [
              { label: "None", value: "0" },
              { label: "Small (4px)", value: "4px" },
              { label: "Rounded (8px)", value: "8px" },
              { label: "Large (12px)", value: "12px" },
            ],
          },
          { key: "caption_color", label: "Caption color", type: "color" },
        ],
      },
    ],
  },

  section_label: {
    label: "Section Label",
    icon: "§",
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "text_color", label: "Text color", type: "color" },
          {
            key: "font_size",
            label: "Font size",
            type: "select",
            options: [
              { label: "XS (10px)", value: "10px" },
              { label: "Small (11px)", value: "11px" },
              { label: "Normal (13px)", value: "13px" },
              { label: "Medium (15px)", value: "15px" },
              { label: "Large (18px)", value: "18px" },
            ],
          },
          {
            key: "font_weight",
            label: "Weight",
            type: "select",
            options: [
              { label: "Normal", value: "400" },
              { label: "Semibold", value: "600" },
              { label: "Bold", value: "700" },
            ],
          },
          { key: "line_color", label: "Line color", type: "color" },
          {
            key: "line_position",
            label: "Line",
            type: "select",
            options: [
              { label: "Below label", value: "below" },
              { label: "Above label", value: "above" },
              { label: "None", value: "none" },
            ],
          },
          {
            key: "align",
            label: "Alignment",
            type: "align",
          },
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

  columns: {
    label: "Columns",
    icon: "⊞",
    sections: [
      {
        id: "layout",
        title: "Layout",
        fields: [
          {
            key: "column_count",
            label: "Columns",
            type: "select",
            options: [
              { label: "2 Columns", value: "2" },
              { label: "3 Columns", value: "3" },
            ],
          },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          { key: "heading_color", label: "Heading color", type: "color" },
          { key: "text_color", label: "Text color", type: "color" },
          { key: "button_color", label: "Button color", type: "color" },
        ],
      },
    ],
  },

  container: {
    label: "Container",
    icon: "▢",
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "heading", label: "Heading", type: "text", placeholder: "Optional heading…" },
          { key: "text",    label: "Body text", type: "text", placeholder: "Optional text…" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          { key: "border_color",     label: "Border color", type: "color" },
          {
            key: "border_radius",
            label: "Corners",
            type: "select",
            options: [
              { label: "Sharp",       value: "0" },
              { label: "Small (4px)", value: "4px" },
              { label: "Rounded (8px)", value: "8px" },
              { label: "Large (12px)", value: "12px" },
              { label: "XL (16px)",   value: "16px" },
            ],
          },
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
