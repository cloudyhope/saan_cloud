# Saan App Admin Panel

Persian (RTL) web admin panel for the [Saan App](https://saanapp.ir) platform. Used to manage field operations, stores, users, visits, surveys, and related business workflows across multiple projects.


## Requirements

- Node.js 
- npm

## Setup

```bash
npm install
npm run serve
```

The dev server starts with hot reload. Default API target is set in `.env.development`.

## Environment

API base URL is configured per environment

## Scripts

| Command | Description |
|---------|-------------|
| `npm run serve` | Start development server |
| `npm run build-test` | Production build (test mode) |
| `npm run build-production` | Production build (production mode) |
| `npm run lint` | Run ESLint |

## Project Structure

```
src/
├── api/              # HTTP layer (Axios)
├── components/       # Shared UI components
├── layout/           # App shell, sidebar, topbar
├── router/           # Route definitions
├── store/            # Vuex modules (user, app config)
├── utils/            # Global helpers, paths, directives
└── views/            # Page-level views by feature
```

Navigation menu items are loaded dynamically from the API based on the active project (`setProjectId` in Vuex).

## Main Features

- **Dashboard** — overview and reporting
- **Visit & Supervision** — field visit tracking, approval workflows, answer details
- **Survey Management** — surveys, responses, census results
- **Store Management** — stores, chain/multi-brand, warnings, brand shop
- **User & Customer Management** — users, promoters, customers
- **Warehouse** — inventory and transactions
- **Wallet** — account management and recharge
- **Tickets** — support ticket list, create, and detail
- **File & Media** — file upload/list, media management
- **Elevator Management** — buildings, groups, elevators
- **Action Plans, Reports, Excel Export, Instructions**

