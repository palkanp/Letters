/**
 * Builder smoke tests — create a new letter and verify the editor loads.
 *
 * Each test creates a fresh Letter campaign via the API (same as clicking
 * "New Letter" in the UI) and opens the builder directly. The campaign is
 * cleaned up after each test so tests stay independent.
 *
 * Requires a running Frappe dev server at localhost:8000.
 */

describe("Letter Builder", () => {
  let campaignName;

  beforeEach(() => {
    cy.login();

    // Create a campaign via the API so we have a known name to open
    cy.request("POST", "/api/method/letters.letters.api.save_campaign", {})
      .its("body.message.name")
      .then((name) => {
        campaignName = name;
        cy.visit(`/app/letter-builder/${name}`);
        cy.get("#letter-builder", { timeout: 15000 }).should("exist");
        // New campaigns auto-open the template picker; select "Blank" so each
        // test starts with the builder canvas unobstructed.
        // The "Start blank" button is hidden inside a hover overlay, so force.
        cy.contains("Start blank").click({ force: true });
      });
  });

  afterEach(() => {
    if (!campaignName) return;
    // Frappe requires the CSRF token for mutations; grab it from the loaded page.
    cy.window()
      .its("frappe.csrf_token")
      .then((csrfToken) => {
        cy.request({
          method: "POST",
          url: "/api/method/frappe.client.delete",
          headers: { "X-Frappe-CSRF-Token": csrfToken },
          body: { doctype: "Letter", name: campaignName },
        });
      });
  });

  it("loads the builder canvas", () => {
    // BuilderPage renders a canvas area; it shouldn't show the dashboard
    cy.contains("All Letters").should("not.exist");
    cy.get("#letter-builder").should("be.visible");
  });

  it("shows the toolbar / top bar", () => {
    // The builder has a header with a back/close button
    cy.get("#letter-builder [aria-label='Close'], #letter-builder button")
      .should("have.length.greaterThan", 0);
  });

  it("closes the builder and returns to dashboard", () => {
    // The builder header's first button is the brand "L" campaign-menu dropdown
    cy.get(".letter-builder header button").first().click();
    // "Back to Letters" is the first item in that dropdown
    cy.contains("Back to Letters").click();
    cy.contains("All Letters", { timeout: 10000 }).should("be.visible");
  });
});
