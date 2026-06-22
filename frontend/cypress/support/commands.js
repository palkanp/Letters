/**
 * Login to Frappe via the API. Sets session cookies so subsequent cy.visit()
 * calls land inside an authenticated Desk session.
 */
Cypress.Commands.add("login", (user, password) => {
  const usr = user ?? Cypress.env("frappe_user");
  const pwd = password ?? Cypress.env("frappe_password");

  cy.request({
    method: "POST",
    url: "/api/method/login",
    body: { usr, pwd },
    form: true,
  });
});

/**
 * Navigate to the Letters builder inside Frappe Desk.
 * Pass a campaign name to open that campaign directly.
 */
Cypress.Commands.add("openBuilder", (campaignName) => {
  const url = campaignName
    ? `/app/letter-builder/${campaignName}`
    : "/app/letter-builder";
  cy.visit(url);
  // Wait for Frappe Desk JS to boot and mount the Vue app
  cy.get("#letter-builder", { timeout: 15000 }).should("exist");
});
