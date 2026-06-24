/**
 * Recipients, Analytics, and Details settings tab tests.
 *
 * Each describe block creates all data it needs via Frappe API and cleans up
 * in afterEach. Tests do not depend on any pre-existing bench data.
 *
 * Requires a running Frappe dev server at localhost:8000.
 */

// ── Shared helpers ─────────────────────────────────────────────────────────────

/**
 * Create a Letter via the save_letter API and open the builder.
 * Stores the name in `letterName` (passed by reference as an object wrapper).
 */
function createAndOpenLetter(ref) {
  cy.login();
  cy.request("POST", "/api/method/letters.letters.api.save_letter", {})
    .its("body.message.name")
    .then((name) => {
      ref.name = name;
      cy.visit(`/app/letter-builder/${name}`);
      cy.get("#letter-builder", { timeout: 15000 }).should("exist");
      cy.contains("Start blank").click({ force: true });
    });
}

/**
 * Delete a Letter using the CSRF token from the currently loaded page.
 */
function deleteLetter(name) {
  if (!name) return;
  cy.window()
    .its("frappe.csrf_token")
    .then((csrfToken) => {
      cy.request({
        method: "POST",
        url: "/api/method/frappe.client.delete",
        headers: { "X-Frappe-CSRF-Token": csrfToken },
        body: { doctype: "Letter", name },
        failOnStatusCode: false,
      });
    });
}

/**
 * Open the Settings modal from the builder toolbar.
 * The toolbar button emits "open-settings"; it renders as a button with
 * aria-label "Campaign settings".
 */
function openSettings() {
  cy.get('button[aria-label="Campaign settings"]', { timeout: 10000 })
    .first()
    .click({ force: true });
  // Wait for the modal heading to appear
  cy.contains("Settings", { timeout: 10000 }).should("be.visible");
}

/**
 * Click a tab in the Settings modal left nav by label text.
 */
function clickSettingsTab(label) {
  cy.contains("aside nav button", label).click();
}

// ── Pre-send tests ─────────────────────────────────────────────────────────────

describe("Recipients tab — pre-send", () => {
  const letter = { name: null };

  beforeEach(() => {
    createAndOpenLetter(letter);
  });

  afterEach(() => {
    deleteLetter(letter.name);
    letter.name = null;
  });

  it("opens settings and navigates to Recipients tab", () => {
    openSettings();
    clickSettingsTab("Recipients");
    // RecipientsPicker renders "Add another source" button
    cy.contains("Add another source", { timeout: 15000 }).should("be.visible");
  });

  it("email group source — shows group selector after selecting Email group type", () => {
    // Create an Email Group so the selector has at least one option
    cy.window()
      .its("frappe.csrf_token")
      .then((csrfToken) => {
        cy.request({
          method: "POST",
          url: "/api/method/frappe.client.insert",
          headers: { "X-Frappe-CSRF-Token": csrfToken },
          body: {
            doc: JSON.stringify({ doctype: "Email Group", title: "Cypress Test Group" }),
          },
        }).then((res) => {
          const groupName = res.body.message.name;

          openSettings();
          clickSettingsTab("Recipients");

          // "Email group" is the default first pill — it should already be active.
          // The frappe-ui Select for the email group renders as a button-based dropdown.
          // Verify the group selector placeholder or the group option is present.
          cy.contains("Select email group", { timeout: 15000 }).should("exist");

          // Click the Select dropdown trigger (the button showing "Select email group")
          cy.contains("Select email group").click({ force: true });

          // Wait for the dropdown option matching our group title and click it
          cy.contains("Cypress Test Group", { timeout: 15000 }).click({ force: true });

          // The group name should now be reflected — count badge or selection text appears
          cy.contains("Cypress Test Group", { timeout: 10000 }).should("exist");

          // Cleanup the Email Group
          cy.window()
            .its("frappe.csrf_token")
            .then((token) => {
              cy.request({
                method: "POST",
                url: "/api/method/frappe.client.delete",
                headers: { "X-Frappe-CSRF-Token": token },
                body: { doctype: "Email Group", name: groupName },
                failOnStatusCode: false,
              });
            });
        });
      });
  });

  it("doctype source — shows doctype selector and Filter button", () => {
    openSettings();
    clickSettingsTab("Recipients");

    // Switch source type to DocType
    cy.contains("button", "DocType", { timeout: 10000 }).click({ force: true });

    // The frappe-ui Select for doctype renders with placeholder text
    cy.contains("Select DocType", { timeout: 10000 }).should("exist");

    // Open the DocType dropdown and pick "Contact"
    cy.contains("Select DocType").click({ force: true });
    cy.contains("Contact", { timeout: 15000 }).click({ force: true });

    // After selecting Contact, the Filter button should appear
    // (DoctypeTab shows Filter only when a doctype AND email_field are chosen;
    //  Contact has a single email field so it auto-selects)
    cy.contains("button", "Filter", { timeout: 15000 }).should("be.visible");
  });

  it("doctype source — filter panel opens with field selector and operator selector", () => {
    openSettings();
    clickSettingsTab("Recipients");

    cy.contains("button", "DocType", { timeout: 10000 }).click({ force: true });

    cy.contains("Select DocType").click({ force: true });
    cy.contains("Contact", { timeout: 15000 }).click({ force: true });

    // Wait for Filter button then click it
    cy.contains("button", "Filter", { timeout: 15000 }).click({ force: true });

    // Filter panel opens with one pre-populated row (DoctypeTab calls addRow on open).
    // The panel is a rounded bordered box; each row has a field Select and an operator Select.
    // We assert the panel container has at least 2 button-based Select triggers (field + operator).
    cy.get(".rounded-lg.border", { timeout: 10000 })
      .last()
      .find("button")
      .should("have.length.greaterThan", 1);
  });

  it("paste source — count badge updates as emails are typed", () => {
    openSettings();
    clickSettingsTab("Recipients");

    // Switch to Paste emails
    cy.contains("button", "Paste emails", { timeout: 10000 }).click({ force: true });

    // Type two valid email addresses into the Textarea
    // frappe-ui Textarea renders as <textarea>
    cy.get("textarea", { timeout: 10000 })
      .first()
      .type("alice@example.com{enter}bob@example.com", { force: true });

    // Count badge should update to 2
    cy.contains("2 valid addresses", { timeout: 10000 }).should("be.visible");
  });

  it("add another source — creates a second source block", () => {
    openSettings();
    clickSettingsTab("Recipients");

    // Initially one source block exists (rendered by RecipientsPicker on mount)
    // Click "Add another source"
    cy.contains("Add another source", { timeout: 10000 }).click({ force: true });

    // Two source blocks visible — each block has the segmented pill row.
    // The pill row wrapper has a bg-surface-gray-2 class; assert two exist.
    cy.get(".bg-surface-gray-2").should("have.length.at.least", 2);
  });
});

// ── Post-send tests ────────────────────────────────────────────────────────────

describe("Recipients tab — post-send", () => {
  const letter = { name: null };

  beforeEach(() => {
    cy.login();

    // Create a letter, set subject + recipient_config, then trigger a send
    cy.request("POST", "/api/method/letters.letters.api.save_letter", {})
      .its("body.message.name")
      .then((name) => {
        letter.name = name;

        // We need the CSRF token — visit a lightweight Frappe page first
        cy.visit("/app");
        cy.window()
          .its("frappe.csrf_token")
          .then((csrfToken) => {
            // Set subject (required for send)
            cy.request({
              method: "POST",
              url: "/api/method/frappe.client.set_value",
              headers: { "X-Frappe-CSRF-Token": csrfToken },
              body: { doctype: "Letter", name, fieldname: "subject", value: "Cypress Test Send" },
            });

            // Set recipient_config to a paste source with one address
            cy.request({
              method: "POST",
              url: "/api/method/frappe.client.set_value",
              headers: { "X-Frappe-CSRF-Token": csrfToken },
              body: {
                doctype: "Letter",
                name,
                fieldname: "recipient_config",
                value: JSON.stringify({ type: "paste", recipients: ["test@example.com"] }),
              },
            });

            // Trigger send
            cy.request({
              method: "POST",
              url: "/api/method/letters.letters.api.send_letter",
              headers: { "X-Frappe-CSRF-Token": csrfToken },
              body: { name },
              failOnStatusCode: false,
            });
          });

        // Now open the builder
        cy.visit(`/app/letter-builder/${name}`);
        cy.get("#letter-builder", { timeout: 15000 }).should("exist");
        cy.contains("Start blank").click({ force: true });
      });
  });

  afterEach(() => {
    deleteLetter(letter.name);
    letter.name = null;
  });

  it("shows source rows with recipient counts in sent view", () => {
    openSettings();

    // LetterSettings auto-switches to Analytics when letter transitions to sent;
    // navigate explicitly to Recipients
    clickSettingsTab("Recipients");

    // In the sent view, source rows are shown inside a bordered list
    // Each paste/doctype row has a count in parentheses, e.g. "Pasted addresses (1)"
    cy.contains("Pasted addresses", { timeout: 15000 }).should("be.visible");
  });

  it("paste source row expands to show recipient emails", () => {
    openSettings();
    clickSettingsTab("Recipients");

    // Click the "Pasted addresses" row to expand it
    cy.contains("Pasted addresses", { timeout: 15000 }).click({ force: true });

    // test@example.com should appear in the expanded list
    cy.contains("test@example.com", { timeout: 10000 }).should("be.visible");
  });
});

// ── Analytics tab tests ────────────────────────────────────────────────────────

describe("Analytics tab", () => {
  const letter = { name: null };

  beforeEach(() => {
    cy.login();

    cy.request("POST", "/api/method/letters.letters.api.save_letter", {})
      .its("body.message.name")
      .then((name) => {
        letter.name = name;

        cy.visit("/app");
        cy.window()
          .its("frappe.csrf_token")
          .then((csrfToken) => {
            cy.request({
              method: "POST",
              url: "/api/method/frappe.client.set_value",
              headers: { "X-Frappe-CSRF-Token": csrfToken },
              body: { doctype: "Letter", name, fieldname: "subject", value: "Cypress Analytics Test" },
            });

            cy.request({
              method: "POST",
              url: "/api/method/frappe.client.set_value",
              headers: { "X-Frappe-CSRF-Token": csrfToken },
              body: {
                doctype: "Letter",
                name,
                fieldname: "recipient_config",
                value: JSON.stringify({ type: "paste", recipients: ["analytics@example.com"] }),
              },
            });

            cy.request({
              method: "POST",
              url: "/api/method/letters.letters.api.send_letter",
              headers: { "X-Frappe-CSRF-Token": csrfToken },
              body: { name },
              failOnStatusCode: false,
            });
          });

        cy.visit(`/app/letter-builder/${name}`);
        cy.get("#letter-builder", { timeout: 15000 }).should("exist");
        cy.contains("Start blank").click({ force: true });
      });
  });

  afterEach(() => {
    deleteLetter(letter.name);
    letter.name = null;
  });

  it("shows delivered count and sent date after send", () => {
    openSettings();
    clickSettingsTab("Analytics");

    // "Delivered" stat card — the label text is "Delivered"
    cy.contains("Delivered", { timeout: 15000 }).should("be.visible");

    // "Sent on" prefix comes from formatDate(analytics.last_sent)
    cy.contains("Sent on", { timeout: 10000 }).should("be.visible");
  });

  it("shows open tracking note", () => {
    openSettings();
    clickSettingsTab("Analytics");

    // The pixel tracking disclaimer contains "pixel"
    cy.contains("pixel", { timeout: 15000 }).should("be.visible");
  });
});

// ── Details tab — unsubscribe setting ─────────────────────────────────────────

describe("Details tab — unsubscribe setting", () => {
  const letter = { name: null };

  beforeEach(() => {
    createAndOpenLetter(letter);
  });

  afterEach(() => {
    deleteLetter(letter.name);
    letter.name = null;
  });

  it("toggling include unsubscribe shows description text", () => {
    openSettings();
    // Details tab is active by default — no need to click it

    // Find the "Include unsubscribe link" checkbox
    cy.contains("Include unsubscribe link", { timeout: 10000 }).should("be.visible");

    // The description text is always present alongside the checkbox label
    cy.contains("For email group sends", { timeout: 10000 }).should("be.visible");

    // Check the checkbox if it is currently unchecked
    cy.get('input[type="checkbox"]')
      .first()
      .then(($cb) => {
        if (!$cb.prop("checked")) {
          cy.wrap($cb).click({ force: true });
        }
      });

    // Description text remains visible after toggling
    cy.contains("For email group sends").should("be.visible");
  });
});
