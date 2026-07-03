
# Letters

Visual email design and letter sending system for [Frappe](https://frappeframework.com/). Build emails with a drag-and-drop block editor, preview them on desktop and mobile, and send to manual recipients or anyone pulled from any DocType in your site — all from within Frappe Desk.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

<img width="1470" height="839" alt="Screenshot 2026-07-03 at 7 43 30 PM" src="https://github.com/user-attachments/assets/8dbe9ed0-f4b1-4b82-8204-39db4a1e742a" />

## Features

- **Drag-and-drop editor** — build emails from blocks (hero, text, button, divider and other pre-sets) with a live layers panel for reordering and nesting.
- **Clean HTML output** — a table-based, inline-styled compiler with no MJML dependency, so emails render consistently across inboxes.
- **Flexible recipients** — send to a manual list or dynamically source recipients from any DocType on your site.
- **Delivery tracking** — every send creates an Email Send record with per-recipient status via Email Send Recipient.
- **Scheduled & bulk sends** — background jobs (via Frappe's scheduler) handle scheduled sends and reconcile in-flight ones every 5 minutes.
- **Templates** — start from a Letters Template instead of a blank canvas.
- **Inbox preheader** — set custom preview text shown in the recipient's inbox.
- **Role-based access** — access control follows standard Frappe roles/permissions.

See [ROADMAP.md](ROADMAP.md) for what's shipped, what's next, and the reasoning behind prioritization.

## Requirements

- [Frappe Framework](https://github.com/frappe/frappe) (bench-managed site)
- Python >= 3.10
- Node.js (for building the frontend)

## Installation

```bash
bench get-app letters https://github.com/palkanp/Letters
bench install-app letters
```

Then restart your bench (or `bench restart` in production) and open **Letters Builder** from Frappe Desk at `/app/letters-builder`.

## Development

The frontend is a Vue 3 app built with Vite and [frappe-ui](https://github.com/frappe/frappe-ui), mounted directly into a Frappe Desk page (no separate SPA route).

```bash
cd frontend
npm install
npm run dev     # dev server, proxies API calls to localhost:8000
npm run build    # builds and outputs to letters/public/js/
```

Common frontend scripts:

```bash
npm run lint       # eslint
npm run test       # vitest (unit tests)
npm run test:watch # vitest watch mode
npm run e2e         # cypress (headless)
npm run e2e:open    # cypress (interactive)
```

Backend Python tests run through Frappe's test runner from your bench:

```bash
bench --site your-site.local run-tests --app letters
```

## Architecture

- **`letters/`** — the Frappe app (Python). DocTypes, controllers, whitelisted APIs, scheduled jobs, and install hooks live here.
- **`frontend/`** — the Vue 3 builder UI. Built assets are emitted into `letters/public/js/letter-builder.js` and loaded by a Frappe Desk page (see `page_js` in `hooks.py`).
- **DocTypes**:
  - `Letter` — the email/letter being designed, with its block-based design tree.
  - `Letter Category`, `Letter Folder` — organization for letters.
  - `Letters Template` — reusable starting points for new letters.
  - `Email Send` / `Email Send Recipient` — a send record and its per-recipient delivery status.
- **Rendering** — the design tree is compiled to inline-styled, table-based HTML server-side before sending, so output is consistent regardless of the recipient's email client.
- **Scheduling** — `letters.letters.api.process_scheduled_sends` and `letters.letters.api.reconcile_active_sends` run every 5 minutes via Frappe's cron scheduler to handle scheduled and in-flight bulk sends.

## License

[AGPL-3.0](LICENSE) © Palkan Parsana
