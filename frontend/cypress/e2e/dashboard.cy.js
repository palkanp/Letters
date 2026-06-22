/**
 * Dashboard smoke tests — verify the Letters dashboard loads and the main
 * UI controls are present and functional without needing a real campaign.
 *
 * Requires a running Frappe dev server at localhost:8000.
 * Set CYPRESS_frappe_user / CYPRESS_frappe_password env vars to override
 * the defaults (Administrator / admin).
 */

describe("Letters Dashboard", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/app/letter-builder");
    // Wait for the Vue app to mount inside Frappe Desk
    cy.get("#letter-builder", { timeout: 15000 }).should("exist");
  });

  it("shows the Letters sidebar and header", () => {
    cy.contains("Letters").should("be.visible");
    cy.contains("All Letters").should("be.visible");
  });

  it("shows the New Letter button", () => {
    cy.contains("button", "New Letter").should("be.visible");
  });

  it("shows the search input", () => {
    cy.get('input[placeholder="Filter by title…"]').should("be.visible");
  });

  it("filters the list when typing in the search box", () => {
    // Type something that is unlikely to match any real title
    cy.get('input[placeholder="Filter by title…"]').type("__no_match_xyz__");
    cy.contains("No letters match your filters.").should("be.visible");
  });

  it("shows grid and list view toggle buttons", () => {
    cy.get('[data-testid="view-grid"]').should("be.visible");
    cy.get('[data-testid="view-list"]').should("be.visible");
  });

  it("switches to list view", () => {
    cy.get('[data-testid="view-list"]').click();
    // Grid button should still be visible after switching
    cy.get('[data-testid="view-grid"]').should("be.visible");
  });

  it("shows the Folders section in the sidebar", () => {
    cy.contains("Folders").should("be.visible");
  });
});
