<template>
  <div ref="el" class="flex-1 date-range-control" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from "vue";

const props = defineProps({
  modelValue: { type: [Array, String], default: null },
});
const emit = defineEmits(["update:modelValue"]);

const el = ref(null);
let control = null;

onMounted(() => {
  if (!window.frappe?.ui?.form?.ControlDateRange) return;

  control = new frappe.ui.form.ControlDateRange({
    parent: el.value,
    df: { fieldtype: "DateRange", fieldname: "date_range", label: "" },
    only_input: true,
  });
  control.make();
  control.refresh();

  const inputEl = control.$input[0];

  // Remove Bootstrap's form-control class and apply inline styles to match
  // frappe-ui Select size="sm" variant="subtle" exactly
  inputEl.classList.remove("form-control");
  // Match frappe-ui Select size="sm" variant="subtle":
  // sm  -> min-h-7 (28px), rounded (DEFAULT 8px in frappe-ui), px-2 (0.5rem)
  // font -> text-base = 14px / lineHeight 1.15 / letterSpacing 0.02em / weight 420
  Object.assign(inputEl.style, {
    display: "block",
    width: "100%",
    minHeight: "28px",
    height: "auto",
    fontSize: "14px",
    lineHeight: "1.15",
    letterSpacing: "0.02em",
    fontWeight: "420",
    padding: "0 0.5rem",
    borderRadius: "0.5rem",
    border: "1px solid var(--surface-gray-2)",
    backgroundColor: "var(--surface-gray-2)",
    color: "var(--ink-gray-7)",
    boxShadow: "none",
    transition: "background-color 0.15s, border-color 0.15s",
  });

  inputEl.addEventListener("mouseenter", () => {
    inputEl.style.borderColor = "var(--outline-gray-modals)";
    inputEl.style.backgroundColor = "var(--surface-gray-3)";
  });
  inputEl.addEventListener("mouseleave", () => {
    inputEl.style.borderColor = "var(--surface-gray-2)";
    inputEl.style.backgroundColor = "var(--surface-gray-2)";
  });

  // Remove air-datepicker's keydown handler so arrow keys move the text cursor
  control.$input.off("keydown.adp");

  if (props.modelValue) setControlValue(props.modelValue);

  control.$input.on("change", () => {
    const val = control.get_value();
    if (Array.isArray(val) && val.length === 2) {
      emit("update:modelValue", val);
    }
  });
});

onBeforeUnmount(() => {
  control?.$input?.off("change");
});

watch(() => props.modelValue, (val) => {
  if (control && val) setControlValue(val);
});

function setControlValue(val) {
  if (Array.isArray(val) && val.length === 2) {
    control.set_input(val[0], val[1]);
  }
}
</script>

<style scoped>
.date-range-control :deep(.form-group) {
  margin: 0;
}
.date-range-control :deep(input:focus) {
  outline: none;
  box-shadow: 0 0 0 2px var(--outline-gray-3) !important;
  border-color: var(--outline-gray-modals) !important;
}
</style>
