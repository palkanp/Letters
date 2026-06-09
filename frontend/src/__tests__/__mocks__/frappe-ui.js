/**
 * Minimal frappe-ui stub for Vitest.
 * Only exports the symbols our source files actually import.
 * Components that appear in templates are stubbed with simple pass-through stubs
 * via @vue/test-utils's stubs option — they don't need to be real Vue components
 * here; we just need the named exports to not throw on import.
 */
import { defineComponent, h } from "vue";

// Generic stub component factory
function makeStub(name) {
  return defineComponent({
    name,
    inheritAttrs: false,
    setup(_, { slots, attrs }) {
      return () => h("div", { ...attrs, "data-stub": name }, slots.default?.());
    },
  });
}

export const Button    = makeStub("Button");
export const TextInput = makeStub("TextInput");
export const FeatherIcon = defineComponent({
  name: "FeatherIcon",
  props: { name: String },
  render() { return h("span", { "data-icon": this.name }); },
});

export const toast = {
  success: vi.fn(),
  error:   vi.fn(),
  warning: vi.fn(),
  info:    vi.fn(),
};

export const FrappeUIProvider = makeStub("FrappeUIProvider");
