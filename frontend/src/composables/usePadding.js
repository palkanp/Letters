import { computed } from "vue";

/**
 * Returns a reactive padding style object for a block, reading from
 * padding_top / padding_right / padding_bottom / padding_left props.
 *
 * @param {import('vue').Ref} blockProps  reactive ref to block.props
 * @param {{ top, right, bottom, left }} defaults  fallback px values
 */
export function usePadding(blockProps, defaults = { top: 20, right: 16, bottom: 20, left: 16 }) {
  return computed(() => {
    const p = blockProps.value;
    return {
      paddingTop:    `${p.padding_top    ?? defaults.top}px`,
      paddingRight:  `${p.padding_right  ?? defaults.right}px`,
      paddingBottom: `${p.padding_bottom ?? defaults.bottom}px`,
      paddingLeft:   `${p.padding_left   ?? defaults.left}px`,
    };
  });
}
