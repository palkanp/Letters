// Pure helpers shared across the builder page and its composables. No reactive
// state here — just stateless transforms kept out of the page component.

// Turn a Frappe API error into a clean, user-safe string. Prefers the
// structured _server_messages; never falls back to e.exc (a raw traceback).
export function describeError(e) {
  let msg = "";
  try {
    const msgs = e?._server_messages;
    if (msgs) {
      const parsed = JSON.parse(msgs);
      const first = parsed[0];
      try { msg = JSON.parse(first).message || first; } catch { msg = first; }
    }
  } catch { /* fall through */ }
  if (!msg) msg = e?.message || "Something went wrong. Please try again.";
  // Frappe messages may contain HTML; strip tags so toasts stay clean.
  return String(msg).replace(/<[^>]*>/g, "").trim() || "Something went wrong. Please try again.";
}

// Format a "YYYY-MM-DD HH:mm:ss" datetime for compact display; echoes the
// input untouched if it can't be parsed.
export function formatScheduledAt(s) {
  try { return new Date(s.replace(" ", "T")).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }); }
  catch { return s; }
}

// Drop runtime-only `id` fields before persisting, recursing into nested
// children and column blocks.
export function stripIds(block) {
  const { id: _id, ...rest } = block;
  if (rest.children?.length) {
    rest.children = rest.children.map(stripIds);
  }
  if (rest.columns?.length) {
    rest.columns = rest.columns.map(col => ({
      ...col,
      blocks: (col.blocks || []).map(stripIds),
    }));
  }
  return rest;
}

// Collect every font_family used anywhere in the block tree (including columns
// and children) so the editor can inject the matching Google Font weights.
export function collectFontFamilies(blocks) {
  const names = [];
  for (const block of blocks || []) {
    if (block.props?.font_family) names.push(block.props.font_family);
    for (const col of block.props?.columns || []) {
      names.push(...collectFontFamilies(col.blocks));
    }
    names.push(...collectFontFamilies(block.children));
  }
  return names;
}
