// Declarative property schema for the right-side Inspector panel.
// Each block entry has:
//   label    — display name
//   icon     — feather icon name
//   sections — Inspector sections (collapsible groups of fields)
//   defaults — initial prop values used when the block is first created
//
// Having defaults here (instead of a separate defaultProps() in editor.js) means
// there is a single source of truth per block: adding a new prop only requires
// touching one file.
//
// Supported control types: "color", "select", "text", "number", "align", "dimension".

export const BLOCK_SCHEMA = {
  hero: {
    label: "Hero",
    icon: "layout",
    defaults: {
      heading: "Your heading",
      subheading: "Your subheading",
      background_color: "#ffffff",
      text_align: "center",
      heading_color: "#111827",
      heading_size: "30px",
      subheading_color: "#6b7280",
      padding_top: 40, padding_right: 32, padding_bottom: 40, padding_left: 32,
    },
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
          { key: "heading_size", label: "Heading size", type: "text", placeholder: "30px" },
          { key: "heading_color", label: "Heading color", type: "color" },
          { key: "subheading_color", label: "Subheading color", type: "color" },
        ],
      },
    ],
  },

  text: {
    label: "Text",
    icon: "type",
    defaults: {
      content: "Start typing your message...",
      align: "left",
      font_size: "15px",
      font_weight: "400",
      text_color: "#374151",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
    sections: [
      {
        id: "typography",
        title: "Typography",
        fields: [
          { key: "align", label: "Alignment", type: "align" },
          { key: "font_size", label: "Font size", type: "text", placeholder: "15px" },
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
          { key: "line_height", label: "Line height", type: "text", placeholder: "1.6" },
          { key: "letter_spacing", label: "Letter spacing", type: "text", placeholder: "normal" },
        ],
      },
    ],
  },

  image: {
    label: "Image",
    icon: "image",
    defaults: {
      image_url: "",
      caption: "",
      alt: "",
      background_color: "#ffffff",
      border: "0.5px solid #383838",
      border_radius: "0",
      padding_top: 16, padding_right: 32, padding_bottom: 16, padding_left: 32,
      spacing_top: 0, spacing_bottom: 0,
    },
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
          { key: "border", label: "Border", type: "text", placeholder: "1px solid #e5e7eb" },
          { key: "border_radius", label: "Corners", type: "text", placeholder: "8px" },
          { key: "caption_color", label: "Caption color", type: "color" },
        ],
      },
    ],
  },

  section_label: {
    label: "Section Label",
    icon: "tag",
    defaults: {
      label: "SECTION TITLE",
      text_color: "#383838",
      line_color: "#ededed",
      line_position: "below",
      align: "left",
      padding_top: 12, padding_right: 32, padding_bottom: 12, padding_left: 32,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "text_color", label: "Text color", type: "color" },
          { key: "font_size", label: "Font size", type: "text", placeholder: "11px" },
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
          { key: "align", label: "Alignment", type: "align" },
        ],
      },
    ],
  },

  image_text: {
    label: "Image + Text",
    icon: "sidebar",
    defaults: {
      image_url: "",
      text: "Describe the image here. Keep it short and compelling.",
      image_position: "left",
      image_width: "160px",
      layout_mode: "side",
      background_color: "#ffffff",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
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
          { key: "image_width", label: "Image width", type: "text", placeholder: "160px" },
          {
            key: "layout_mode",
            label: "Layout",
            type: "select",
            options: [
              { label: "Side by side", value: "side" },
              { label: "Text wraps image", value: "wrap" },
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
    icon: "square",
    defaults: {
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
          { key: "font_size", label: "Font size", type: "text", placeholder: "14px" },
          {
            key: "button_padding",
            label: "Button size",
            type: "select",
            options: [
              { label: "Compact",  value: "compact" },
              { label: "Normal",   value: "normal" },
              { label: "Large",    value: "large" },
            ],
          },
          { key: "border_radius", label: "Corners", type: "text", placeholder: "8px" },
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
    icon: "more-horizontal",
    defaults: {
      border_color: "#e5e7eb",
      thickness: 1,
      style: "solid",
      width: "100%",
      align: "center",
      padding_top: 16, padding_right: 32, padding_bottom: 16, padding_left: 32,
    },
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
              { label: "Solid",  value: "solid" },
              { label: "Dashed", value: "dashed" },
              { label: "Dotted", value: "dotted" },
            ],
          },
          { key: "thickness", label: "Thickness (px)", type: "number", min: 1, max: 10 },
          { key: "width", label: "Length", type: "text", placeholder: "100%" },
          { key: "align", label: "Alignment", type: "align" },
        ],
      },
    ],
  },

  columns: {
    label: "Columns",
    icon: "columns",
    defaults: {
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
          { key: "col_gap", label: "Column gap (px)", type: "number", min: 0, max: 80 },
        ],
      },
      {
        id: "dividers",
        title: "Dividers",
        fields: [
          {
            key: "show_dividers",
            label: "Column lines",
            type: "select",
            options: [
              { label: "None",       value: false },
              { label: "Show lines", value: true  },
            ],
          },
          { key: "divider_color", label: "Line color", type: "color" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          { key: "heading_color",    label: "Heading color", type: "color" },
          { key: "text_color",       label: "Text color", type: "color" },
          { key: "button_color",     label: "Button color", type: "color" },
        ],
      },
    ],
  },

  container: {
    label: "Container",
    icon: "box",
    defaults: {
      layout: "column",
      gap: 12,
      width: "100%",
      height: "auto",
      background_color: "#f8fafc",
      border_color: "#e2e8f0",
      border_radius: "12px",
      padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16,
    },
    sections: [
      {
        id: "layout",
        title: "Layout",
        fields: [
          {
            key: "layout",
            label: "Direction",
            type: "select",
            options: [
              { label: "Column (stacked)", value: "column" },
              { label: "Row (side by side)", value: "row" },
            ],
          },
          { key: "gap", label: "Gap between blocks", type: "number", min: 0, max: 64, unit: "px" },
          { key: "width", label: "Width", type: "dimension" },
          { key: "height", label: "Min height", type: "dimension" },
          { key: "align", label: "Alignment", type: "align" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          { key: "border_color",  label: "Border color", type: "color" },
          { key: "border_radius", label: "Corners", type: "text", placeholder: "12px" },
        ],
      },
    ],
  },

  footer: {
    label: "Footer",
    icon: "align-justify",
    defaults: {
      text: "You received this email because you signed up.",
      background_color: "#f9fafb",
      text_color: "#6b7280",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
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

  spacer: {
    label: "Spacer",
    icon: "minus",
    defaults: {
      height: 32,
      background_color: "transparent",
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "height", label: "Height (px)", type: "number", min: 4, max: 300 },
          { key: "background_color", label: "Background", type: "color" },
        ],
      },
    ],
  },

  quote: {
    label: "Quote",
    icon: "message-square",
    defaults: {
      quote: "This is a wonderful product that changed how we work.",
      author: "Jane Doe",
      role: "CEO, Acme Inc.",
      style: "left-border",
      quote_color: "#111827",
      author_color: "#6b7280",
      border_color: "#e5e7eb",
      background_color: "#f9fafb",
      padding_top: 24, padding_right: 32, padding_bottom: 24, padding_left: 32,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          {
            key: "style",
            label: "Style",
            type: "select",
            options: [
              { label: "Left border", value: "left-border" },
              { label: "Centered",    value: "centered" },
            ],
          },
          { key: "background_color", label: "Background", type: "color" },
          { key: "border_color",     label: "Accent color", type: "color" },
          { key: "quote_color",      label: "Quote color", type: "color" },
          { key: "author_color",     label: "Author color", type: "color" },
        ],
      },
    ],
  },

  social: {
    label: "Social",
    icon: "share-2",
    defaults: {
      x_url: "",
      linkedin_url: "",
      instagram_url: "",
      facebook_url: "",
      youtube_url: "",
      github_url: "",
      website_url: "",
      color: "#374151",
      background_color: "#ffffff",
      align: "center",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
    sections: [
      {
        id: "links",
        title: "Links",
        fields: [
          { key: "x_url",         label: "X / Twitter URL",  type: "text", placeholder: "https://x.com/…" },
          { key: "linkedin_url",  label: "LinkedIn URL",     type: "text", placeholder: "https://linkedin.com/…" },
          { key: "instagram_url", label: "Instagram URL",    type: "text", placeholder: "https://instagram.com/…" },
          { key: "facebook_url",  label: "Facebook URL",     type: "text", placeholder: "https://facebook.com/…" },
          { key: "youtube_url",   label: "YouTube URL",      type: "text", placeholder: "https://youtube.com/…" },
          { key: "github_url",    label: "GitHub URL",       type: "text", placeholder: "https://github.com/…" },
          { key: "website_url",   label: "Website URL",      type: "text", placeholder: "https://…" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "color",            label: "Icon color",  type: "color" },
          { key: "background_color", label: "Background",  type: "color" },
          { key: "align",            label: "Alignment",   type: "align" },
        ],
      },
    ],
  },

  product_card: {
    label: "Product",
    icon: "shopping-bag",
    defaults: {
      image_url: "",
      title: "Product Name",
      description: "Short description of your product that highlights its key benefits.",
      price: "$99",
      button_label: "Shop Now",
      button_url: "#",
      background_color: "#ffffff",
      border_color: "#e5e7eb",
      border_radius: "12px",
      button_color: "#111827",
      title_color: "#111827",
      text_color: "#6b7280",
      padding_top: 20, padding_right: 32, padding_bottom: 20, padding_left: 32,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "image_url",    label: "Image URL",    type: "text", placeholder: "https://…" },
          { key: "button_url",   label: "Button URL",   type: "text", placeholder: "https://…" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Card background", type: "color" },
          { key: "border_color",     label: "Border color",    type: "color" },
          { key: "border_radius", label: "Corners", type: "text", placeholder: "12px" },
          { key: "button_color", label: "Button color", type: "color" },
          { key: "title_color",  label: "Title color",  type: "color" },
          { key: "text_color",   label: "Text color",   type: "color" },
        ],
      },
    ],
  },

  video_thumb: {
    label: "Video",
    icon: "play-circle",
    defaults: {
      thumbnail_url: "",
      video_url: "#",
      caption: "Watch the video →",
      play_button_color: "#ffffff",
      play_icon_color: "#111827",
      overlay_color: "rgba(0,0,0,0.3)",
      border_radius: "8px",
      padding_top: 16, padding_right: 32, padding_bottom: 16, padding_left: 32,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "thumbnail_url", label: "Thumbnail URL", type: "text", placeholder: "https://…" },
          { key: "video_url",     label: "Video link URL", type: "text", placeholder: "https://youtube.com/…" },
          { key: "caption",       label: "Caption",        type: "text", placeholder: "Watch the video…" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "play_button_color", label: "Play button",   type: "color" },
          { key: "play_icon_color",   label: "Play icon",     type: "color" },
          { key: "border_radius", label: "Corners", type: "text", placeholder: "8px" },
        ],
      },
    ],
  },
};
