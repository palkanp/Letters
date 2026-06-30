/**
 * Tests for editor store: isReadOnly computed and selectBlock guard.
 *
 * Covers:
 *  - isReadOnly is false when letter is null or Draft
 *  - isReadOnly is true for Sent, Sending, Partial, Failed
 *  - selectBlock is a no-op when isReadOnly
 *  - selectBlock works normally when not read-only
 */
import { describe, it, expect, beforeEach } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useEditorStore } from "../stores/editor";

beforeEach(() => {
  setActivePinia(createPinia());
});

describe("isReadOnly", () => {
  it("is false when letterDoc is null", () => {
    const store = useEditorStore();
    expect(store.isReadOnly).toBe(false);
  });

  it("is false for Draft", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Draft" };
    expect(store.isReadOnly).toBe(false);
  });

  it("is false for Scheduled", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Scheduled" };
    expect(store.isReadOnly).toBe(false);
  });

  it("is true for Sent", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Sent" };
    expect(store.isReadOnly).toBe(true);
  });

  it("is true for Sending", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Sending" };
    expect(store.isReadOnly).toBe(true);
  });

  it("is true for Partial", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Partial" };
    expect(store.isReadOnly).toBe(true);
  });

  it("is true for Failed", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Failed" };
    expect(store.isReadOnly).toBe(true);
  });
});

describe("selectBlock when read-only", () => {
  it("does not change selectedBlockId when isReadOnly", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Sent" };
    store.selectBlock("block-123");
    expect(store.selectedBlockId).toBeNull();
  });

  it("changes selectedBlockId normally when not read-only", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Draft" };
    store.selectBlock("block-123");
    expect(store.selectedBlockId).toBe("block-123");
  });

  it("clears selectedBlockId when not read-only and null is passed", () => {
    const store = useEditorStore();
    store.letterDoc = { status: "Draft" };
    store.selectBlock("block-123");
    store.selectBlock(null);
    expect(store.selectedBlockId).toBeNull();
  });
});
