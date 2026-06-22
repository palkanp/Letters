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
// Supported control types: "color", "select", "text", "number", "slider", "align", "dimension".
// Fields may include a `hint` string shown as a tooltip on the label.

import { FONT_OPTIONS, fontWeightOptions } from "./fonts";

// Reusable font-weight field — options are dynamic based on the selected font.
// System fonts (Arial, Georgia…) only show Normal/Bold since they ship with two
// weight files. Web fonts (Inter, Poppins…) show all available weights.
const fontWeightField = (label = "Weight") => ({
  key: "font_weight",
  label,
  type: "select",
  options: (blockProps) => fontWeightOptions(blockProps?.font_family),
});

// Reusable "Font" control. Spread into a block's typography/style section.
// `value` is the human font name (e.g. "Arial"); the email-safe CSS stack is
// resolved from it at render time. See fonts.js / fonts.py.
const fontField = { key: "font_family", label: "Font", type: "select", options: FONT_OPTIONS, hint: "Web-safe font for this block" };

const letterSpacingField = { key: "letter_spacing", label: "Letter spacing", type: "select", options: [
  { label: "Normal",          value: "normal"  },
  { label: "Tight (−0.02em)", value: "-0.02em" },
  { label: "Snug (−0.01em)",  value: "-0.01em" },
  { label: "Wide (0.05em)",   value: "0.05em"  },
  { label: "Wider (0.1em)",   value: "0.1em"   },
  { label: "Tracked (0.15em)",value: "0.15em"  },
  { label: "Widest (0.2em)",  value: "0.2em"   },
]};

// Shared block-level border + rounding fields (applied by BlockWrapper)
const borderFields = [
  { key: "block_border_color",  label: "Border color", type: "color" },
  { key: "block_border_radius", label: "Corner radius", type: "text", placeholder: "8px" },
];
const borderDefaults = { block_border_color: "", block_border_radius: "0" };

export const BLOCK_SCHEMA = {
  hero: {
    label: "Hero",
    icon: "layout",
    sub_layers: [
      { label: "Heading", icon: "type" },
      { label: "Subheading", icon: "type" },
    ],
    defaults: {
      heading: "",
      subheading: "",
      background_color: "#ffffff",
      text_align: "center",
      heading_color: "#111827",
      heading_size: "30px",
      subheading_color: "#6b7280",
      font_family: "Georgia",
      padding_top: 40, padding_right: 16, padding_bottom: 40, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "heading",    label: "Heading",    type: "text", placeholder: "Your headline here" },
          { key: "subheading", label: "Subheading", type: "text", placeholder: "Supporting text" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          ...borderFields,
        ],
      },
      {
        id: "typography",
        title: "Typography",
        fields: [
          fontField,
          { key: "text_align", label: "Alignment", type: "align" },
          { key: "heading_size", label: "Heading size", type: "text", placeholder: "30px" },
          { key: "heading_color", label: "Heading color", type: "color" },
          { key: "subheading_color", label: "Subheading color", type: "color" },
          letterSpacingField,
        ],
      },
    ],
  },

  text: {
    label: "Text",
    icon: "type",
    defaults: {
      html_content: "",
      align: "left",
      font_family: "Arial",
      font_size: "15px",
      font_weight: "400",
      font_style: "normal",
      text_color: "#374151",
      line_height: "1.6",
      background_color: "transparent",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "typography",
        title: "Typography",
        fields: [
          fontField,
          { key: "align", label: "Alignment", type: "align" },
          { key: "font_size", label: "Font size", type: "text", placeholder: "15px" },
          fontWeightField(),
          { key: "font_style", label: "Italic", type: "select", options: [
            { label: "Normal", value: "normal" },
            { label: "Italic", value: "italic" },
          ]},
          { key: "text_color", label: "Text color", type: "color" },
          { key: "line_height", label: "Line height", type: "text", placeholder: "1.6", hint: "Vertical space between lines, e.g. 1.5 or 160%" },
          letterSpacingField,
          { key: "background_color", label: "Background", type: "color" },
          ...borderFields,
        ],
      },
    ],
  },

  image: {
    label: "Image",
    icon: "image",
    defaults: {
      image_url: "",
      alt: "",
      image_width: "100%",
      image_align: "center",
      image_fit: "cover",
      image_height: "",
      background_color: "#ffffff",
      border: "none",
      border_radius: "0",
      padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16,
      spacing_top: 0, spacing_bottom: 0,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "image_url", label: "Image URL", type: "text", placeholder: "https://example.com" },
          { key: "link_url", label: "Link URL", type: "text", placeholder: "https://example.com" },
          { key: "alt", label: "Alt text", type: "text", placeholder: "Describe the image" },
        ],
      },
      {
        id: "layout",
        title: "Layout",
        fields: [
          { key: "image_align", label: "Align", type: "align", hint: "Position the image horizontally within the block" },
          { key: "block_width", label: "Column width", type: "text", placeholder: "auto", hint: "When inside a row container, sets this column's width — e.g. 200px or 40%" },
          { key: "image_width", label: "Image width", type: "text", placeholder: "100%", hint: "Width of the image element — 100% fills the column, e.g. 300px or 50%" },
          { key: "image_height", label: "Image height", type: "text", placeholder: "auto", hint: "Fixed height for the image area, e.g. 200px" },
          {
            key: "image_fit",
            label: "Fit",
            type: "select",
            options: [
              { label: "Cover (crop to fill)", value: "cover" },
              { label: "Contain (fit inside)",  value: "contain" },
              { label: "Fill (stretch)",         value: "fill" },
            ],
            hint: "How the image fills its area when a fixed height is set",
          },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          { key: "border", label: "Image border", type: "text", placeholder: "1px solid #e5e7eb" },
          { key: "border_radius", label: "Image corners", type: "text", placeholder: "8px" },
          ...borderFields,
        ],
      },
    ],
  },

  section_label: {
    label: "Section Label",
    icon: "tag",
    sub_layers: [
      { label: "Label text", icon: "type" },
      { label: "Divider line", icon: "minus" },
    ],
    defaults: {
      label: "SECTION TITLE",
      text_color: "#383838",
      font_size: "11px",
      font_weight: "600",
      letter_spacing: "0.15em",
      line_color: "#ededed",
      line_thickness: 0.5,
      line_position: "below",
      align: "left",
      font_family: "Arial",
      padding_top: 12, padding_right: 16, padding_bottom: 12, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          { key: "text_color", label: "Text color", type: "color" },
          { key: "font_size", label: "Font size", type: "text", placeholder: "11px" },
          fontWeightField(),
          letterSpacingField,
          { key: "line_color", label: "Line color", type: "color" },
          { key: "line_thickness", label: "Line thickness", type: "number", placeholder: "0.5" },
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
          ...borderFields,
        ],
      },
    ],
  },

  image_text: {
    label: "Image + Text",
    icon: "sidebar",
    sub_layers: [
      { label: "Image", icon: "image" },
      { label: "Text", icon: "type" },
    ],
    defaults: {
      image_url: "",
      heading: "",
      heading_color: "#111827",
      text: "Describe the image here. Keep it short and compelling.",
      text_color: "#555555",
      image_position: "left",
      image_width: "160px",
      layout_mode: "side",
      background_color: "#ffffff",
      font_family: "Arial",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "image",
        title: "Image",
        fields: [
          { key: "image_url", label: "Image URL", type: "text", placeholder: "https://example.com" },
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
        id: "text",
        title: "Text",
        fields: [
          { key: "heading", label: "Heading", type: "text", placeholder: "Optional heading" },
          { key: "heading_color", label: "Heading color", type: "color" },
          { key: "text_color", label: "Text color", type: "color" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          letterSpacingField,
          { key: "background_color", label: "Background", type: "color" },
          ...borderFields,
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
      background_color: "#ffffff",
      align: "center",
      border_radius: "8px",
      font_family: "Arial",
      font_size: "14px",
      button_padding: "normal",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "url", label: "Link URL", type: "text", placeholder: "https://example.com" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          { key: "color", label: "Button color", type: "color" },
          { key: "text_color", label: "Text color", type: "color" },
          { key: "background_color", label: "Background", type: "color" },
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
          letterSpacingField,
          ...borderFields,
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
      orientation: "horizontal",
      width: "100%",
      height: 80,
      align: "center",
      padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          {
            key: "orientation",
            label: "Orientation",
            type: "select",
            options: [
              { label: "Horizontal", value: "horizontal" },
              { label: "Vertical",   value: "vertical" },
            ],
          },
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
          { key: "thickness", label: "Thickness", type: "number", min: 1, max: 10, unit: "px" },
          { key: "width", label: "H Length", type: "text", placeholder: "100%" },
          { key: "height", label: "V Height", type: "number", min: 8, max: 600, unit: "px" },
          { key: "align", label: "Alignment", type: "align" },
          ...borderFields,
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
      show_dividers: false,
      divider_color: "#e5e7eb",
      col_gap: 24,
      vertical_align: "top",
      padding_top: 20, padding_right: 24, padding_bottom: 20, padding_left: 24,
      ...borderDefaults,
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
          { key: "col_gap", label: "Column gap", type: "number", min: 0, max: 80, unit: "px" },
          { key: "vertical_align", label: "V Align", type: "valign" },
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
          ...borderFields,
        ],
      },
    ],
  },

  link_list: {
    label: "Link List",
    icon: "list",
    sub_layers: [
      { label: "Heading", icon: "type" },
      { label: "Links", icon: "list" },
    ],
    defaults: {
      heading: "",
      items: [
        { title: "Article title", url: "https://example.com", description: "Brief description of this article." },
        { title: "Another read", url: "https://example.com", description: "" },
      ],
      style: "bullet",
      link_color: "#2563eb",
      text_color: "#6b7280",
      accent_color: "#9ca3af",
      background_color: "#ffffff",
      font_family: "Arial",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          {
            key: "style",
            label: "List style",
            type: "select",
            options: [
              { label: "Bullets",   value: "bullet" },
              { label: "Numbers",   value: "numbered" },
              { label: "No marker", value: "none" },
            ],
          },
          { key: "background_color", label: "Background",   type: "color" },
          { key: "link_color",       label: "Link color",   type: "color" },
          { key: "text_color",       label: "Description",  type: "color" },
          { key: "accent_color",     label: "Marker color", type: "color" },
          letterSpacingField,
          ...borderFields,
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
      background_color: "transparent",
      vertical_align: "flex-start",
      padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "layout",
        title: "Layout",
        fields: [
          { key: "layout", label: "Direction", type: "direction" },
          { key: "gap", label: "Gap", type: "number", min: 0, max: 64, unit: "px", hint: "Space between child blocks" },
          { key: "width", label: "Width", type: "dimension", hint: "Sets the column width when inside a row container — use % for fluid, px for fixed" },
          { key: "height", label: "Min height", type: "dimension", hint: "Minimum height: block grows taller if content overflows" },
          { key: "align", label: "H Align", type: "align" },
          { key: "vertical_align", label: "V Align", type: "valign" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "background_color", label: "Background", type: "color" },
          ...borderFields,
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
      font_family: "Arial",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "text", label: "Footer text", type: "text", placeholder: "You received this email because you signed up." },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          letterSpacingField,
          { key: "background_color", label: "Background", type: "color" },
          { key: "text_color", label: "Text color", type: "color" },
          ...borderFields,
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
      ...borderDefaults,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "height", label: "Height (px)", type: "number", min: 4, max: 300 },
          { key: "background_color", label: "Background", type: "color" },
          ...borderFields,
        ],
      },
    ],
  },

  quote: {
    label: "Quote",
    icon: "message-square",
    sub_layers: [
      { label: "Quote text", icon: "message-square" },
      { label: "Author", icon: "user" },
    ],
    defaults: {
      quote: "This is a wonderful product that changed how we work.",
      author: "Jane Doe",
      role: "CEO, Acme Inc.",
      style: "left-border",
      quote_color: "#111827",
      author_color: "#6b7280",
      border_color: "#e5e7eb",
      background_color: "#f9fafb",
      font_family: "Georgia",
      padding_top: 24, padding_right: 16, padding_bottom: 24, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
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
          letterSpacingField,
          ...borderFields,
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
      color: "#9ca3af",
      background_color: "#ffffff",
      align: "center",
      icon_size: 20,
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "links",
        title: "Links",
        fields: [
          { key: "x_url",         label: "X / Twitter URL",  type: "text", placeholder: "https://x.com/yourhandle" },
          { key: "linkedin_url",  label: "LinkedIn URL",     type: "text", placeholder: "https://linkedin.com/in/yourname" },
          { key: "instagram_url", label: "Instagram URL",    type: "text", placeholder: "https://instagram.com/yourhandle" },
          { key: "facebook_url",  label: "Facebook URL",     type: "text", placeholder: "https://facebook.com/yourpage" },
          { key: "youtube_url",   label: "YouTube URL",      type: "text", placeholder: "https://youtube.com/yourchannel" },
          { key: "github_url",    label: "GitHub URL",       type: "text", placeholder: "https://github.com/yourhandle" },
          { key: "website_url",   label: "Website URL",      type: "text", placeholder: "https://example.com" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "icon_size",        label: "Icon size",   type: "number", min: 16, max: 64, unit: "px" },
          { key: "color",            label: "Icon color",  type: "color" },
          { key: "background_color", label: "Background",  type: "color" },
          { key: "align",            label: "Alignment",   type: "align" },
          ...borderFields,
        ],
      },
    ],
  },

  product_card: {
    label: "Product",
    icon: "shopping-bag",
    sub_layers: [
      { label: "Image", icon: "image" },
      { label: "Title & text", icon: "type" },
      { label: "Button", icon: "square" },
    ],
    defaults: {
      image_url: "",
      title: "Product Name",
      description: "Short description of your product that highlights its key benefits.",
      price: "$99",
      button_label: "Shop Now",
      button_url: "#",
      background_color: "#ffffff",
      button_color: "#111827",
      title_color: "#111827",
      text_color: "#6b7280",
      font_family: "Arial",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "image_url",    label: "Image URL",    type: "text", placeholder: "https://example.com" },
          { key: "button_url",   label: "Button URL",   type: "text", placeholder: "https://example.com" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          { key: "background_color", label: "Card background", type: "color" },
          { key: "button_color", label: "Button color", type: "color" },
          { key: "title_color",  label: "Title color",  type: "color" },
          { key: "text_color",   label: "Text color",   type: "color" },
          ...borderFields,
        ],
      },
    ],
  },

  header: {
    label: "Logo",
    icon: "award",
    sub_layers: [
      { label: "Logo image", icon: "image" },
      { label: "Tagline", icon: "type" },
    ],
    defaults: {
      logo_url: "",
      logo_height: "40px",
      tagline: "",
      align: "center",
      background_color: "#ffffff",
      border_bottom: true,
      tagline_color: "#6b7280",
      font_family: "Arial",
      padding_top: 20, padding_right: 16, padding_bottom: 20, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "logo_url",   label: "Logo URL",    type: "text", placeholder: "https://example.com/logo.png" },
          { key: "logo_height", label: "Logo height", type: "text", placeholder: "40px" },
          { key: "tagline",    label: "Tagline",     type: "text", placeholder: "Monthly newsletter" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          fontField,
          { key: "align",            label: "Alignment",    type: "align" },
          { key: "background_color", label: "Background",   type: "color" },
          { key: "tagline_color",    label: "Tagline color", type: "color" },
          {
            key: "border_bottom",
            label: "Bottom border",
            type: "select",
            options: [
              { label: "Show", value: true },
              { label: "Hide", value: false },
            ],
          },
          letterSpacingField,
          ...borderFields,
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
      caption: "Watch the video",
      border_radius: "8px",
      overlay_color: "rgba(0,0,0,0.3)",
      play_button_color: "#ffffff",
      play_icon_color: "#111827",
      background_color: "#000000",
      padding_top: 16, padding_right: 16, padding_bottom: 16, padding_left: 16,
      ...borderDefaults,
    },
    sections: [
      {
        id: "content",
        title: "Content",
        fields: [
          { key: "thumbnail_url", label: "Thumbnail URL", type: "text", placeholder: "https://example.com" },
          { key: "video_url",     label: "Video URL",      type: "text", placeholder: "https://youtube.com/watch?v=…" },
          { key: "caption",       label: "Caption",        type: "text", placeholder: "Watch the video" },
        ],
      },
      {
        id: "style",
        title: "Style",
        fields: [
          { key: "border_radius",     label: "Corner radius",    type: "text", placeholder: "8px" },
          { key: "background_color",  label: "Background",       type: "color" },
          { key: "overlay_color",     label: "Overlay tint",     type: "color", hint: "Semi-transparent overlay on the thumbnail — use rgba() for opacity" },
          { key: "play_button_color", label: "Play button",      type: "color" },
          { key: "play_icon_color",   label: "Play icon",        type: "color" },
          ...borderFields,
        ],
      },
    ],
  },
};
