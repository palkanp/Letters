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
    icon: "◻",
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
              { label: "Small — 120px",  value: "120px" },
              { label: "Medium — 160px", value: "160px" },
              { label: "Large — 220px",  value: "220px" },
              { label: "Half — 260px",   value: "260px" },
            ],
          },
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
            key: "font_size",
            label: "Font size",
            type: "select",
            options: [
              { label: "Small (12px)",  value: "12px" },
              { label: "Normal (14px)", value: "14px" },
              { label: "Medium (16px)", value: "16px" },
              { label: "Large (18px)",  value: "18px" },
            ],
          },
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
              { label: "Solid",  value: "solid" },
              { label: "Dashed", value: "dashed" },
              { label: "Dotted", value: "dotted" },
            ],
          },
          { key: "thickness", label: "Thickness (px)", type: "number", min: 1, max: 10 },
          {
            key: "width",
            label: "Length",
            type: "select",
            options: [
              { label: "25%",  value: "25%" },
              { label: "50%",  value: "50%" },
              { label: "75%",  value: "75%" },
              { label: "100%", value: "100%" },
            ],
          },
          { key: "align", label: "Alignment", type: "align" },
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
          {
            key: "col_gap",
            label: "Column gap",
            type: "select",
            options: [
              { label: "None",   value: 0  },
              { label: "Small",  value: 12 },
              { label: "Medium", value: 24 },
              { label: "Large",  value: 40 },
            ],
          },
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

  spacer: {
    label: "Spacer",
    icon: "↕",
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          {
            key: "height",
            label: "Height",
            type: "select",
            options: [
              { label: "XS — 8px",   value: 8 },
              { label: "S — 16px",   value: 16 },
              { label: "M — 32px",   value: 32 },
              { label: "L — 48px",   value: 48 },
              { label: "XL — 64px",  value: 64 },
              { label: "XXL — 96px", value: 96 },
            ],
          },
          { key: "background_color", label: "Background", type: "color" },
        ],
      },
    ],
  },

  quote: {
    label: "Quote",
    icon: "❝",
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
    icon: "⇄",
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
    icon: "🛍",
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
          {
            key: "border_radius",
            label: "Corners",
            type: "select",
            options: [
              { label: "None",       value: "0" },
              { label: "Small (4px)", value: "4px" },
              { label: "Rounded (8px)", value: "8px" },
              { label: "Large (12px)", value: "12px" },
              { label: "XL (16px)",  value: "16px" },
            ],
          },
          { key: "button_color", label: "Button color", type: "color" },
          { key: "title_color",  label: "Title color",  type: "color" },
          { key: "text_color",   label: "Text color",   type: "color" },
        ],
      },
    ],
  },

  video_thumb: {
    label: "Video",
    icon: "▶",
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
          {
            key: "border_radius",
            label: "Corners",
            type: "select",
            options: [
              { label: "None",          value: "0" },
              { label: "Rounded (8px)", value: "8px" },
              { label: "Large (12px)",  value: "12px" },
              { label: "XL (16px)",     value: "16px" },
            ],
          },
        ],
      },
    ],
  },
};
