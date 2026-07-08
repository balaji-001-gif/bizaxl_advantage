# Bizaxl Advantage Suite

A custom **Frappe app for ERPNext v15+** implementing the three structural
build plans from the bizaxl vs. C-Square gap analysis:

1. **B2B Ordering Portal** — closes the gap against C-Square's *LiveOrder*
2. **Field Sales Automation** — closes the gap against C-Square's *SFA360*
3. **Tiered Product Ladder** — packaging/access-control layer mirroring
   C-Square's EcoGreen Lite / Express / full-EcoGreen tiers

All business entities in scope (buyers, pricing tiers, orders, reps,
routes, visits, subscriptions) are shipped as **brand-new custom DocTypes**,
per your requirement to avoid reusing ERPNext's own Customer / Sales Order
/ Quotation masters. The one deliberate exception: **Item, Warehouse, and
the Stock Ledger stay as native ERPNext links**, not duplicated tables.
Rebuilding those from scratch would mean two competing stock truths, and
your own source document's exit criteria (portal stock must match the
desk-side Stock Balance report "with no manual refresh") is only
achievable against the real ledger. Treat this as a hard engineering
constraint, not a style choice.

---

## 1. What's in the box

```
bizaxl_advantage/
├── README.md                     <- this file
├── license.txt, pyproject.toml, requirements.txt, MANIFEST.in, .gitignore
└── bizaxl_advantage/              <- the actual Frappe module root
    ├── hooks.py                   <- fixtures, doc_events, permissions, scheduler
    ├── modules.txt                <- 3 modules (see below)
    ├── utils.py                   <- permission queries + scheduled jobs
    ├── fixtures/                  <- Workspace, Notification, Role, Web Form
    ├── b2b_ordering_portal/
    │   ├── doctype/                (9 DocTypes, 2 child tables)
    │   └── report/                 (1 script report, 1 query report)
    ├── field_sales_automation/
    │   ├── doctype/                (7 DocTypes, 1 child table)
    │   └── report/                 (1 script report)
    └── tiered_product_ladder/
        ├── doctype/                (3 DocTypes, 1 child table)
        └── report/                 (1 query report)
```

**20 DocTypes total** (15 standalone + 4 child tables + 1 log), **4
reports**, **1 Workspace**, **4 Notifications**, **2 custom Roles**, **1
Web Form**, **3 scheduled jobs**.

---

## 2. DocType reference

### B2B Ordering Portal (`b2b_ordering_portal`)

| DocType | Purpose | Maps to build-plan phase |
|---|---|---|
| **BA Portal Buyer** | Custom buyer master (replaces Customer for this app's purposes) — GSTIN, portal user link, territory, price tier, credit limit, status, restricted item groups | Phase 01 (buyer identity/access) |
| **BA Buyer Price Tier** | Named pricing tiers (e.g. "Hospital Pharmacy Rate") | Phase 02 |
| **BA Buyer Item Price** | Item price per tier | Phase 02 |
| **BA Portal Catalog Item** | Controls which Items show on the portal, min/max order qty, restricted flag (e.g. Schedule X) | Phase 02 |
| **BA Stock Snapshot** | System-managed cache of live availability, synced hourly from ERPNext's `Bin` table | Phase 03 |
| **BA Portal Order** | The submittable buyer order; header + child items; links out to `Sales Order` / `Delivery Note` / `Sales Invoice` once staff confirm | Phase 04–05 |
| **BA Portal Order Item** *(child table)* | Line items on a Portal Order | Phase 04 |
| **BA Buyer Restricted Item Group** *(child table)* | Per-buyer item-group blocklist | Phase 02 |
| **BA Order Status Log** | Immutable timeline of status changes per order (for the fulfilment-visibility view) | Phase 05 |

### Field Sales Automation (`field_sales_automation`)

| DocType | Purpose | Maps to build-plan phase |
|---|---|---|
| **BA Sales Territory** | Custom territory tree | Phase 01 |
| **BA Field Rep** | Rep master, linked User, territory, reporting line | Phase 01 |
| **BA Rep Buyer Assignment** | Which reps cover which buyers | Phase 01 |
| **BA Route Plan** | A rep's planned visits for a given date | Phase 02 |
| **BA Route Plan Visit** *(child table)* | One planned stop on a route | Phase 02 |
| **BA Visit Log** | Actual visit record: GPS, outcome, notes, optional linked order | Phase 03 |
| **BA Detailing Content** | e-Detailing assets (image/PDF/video/link) shown during a visit | Phase 03 |

### Tiered Product Ladder (`tiered_product_ladder`)

| DocType | Purpose |
|---|---|
| **BA Subscription Plan** | Named plan (Lite/Express/Full-equivalent), price, billing cycle, feature toggles |
| **BA Plan Feature** *(child table)* | Feature flag rows on a plan |
| **BA Buyer Subscription** | Which buyer is on which plan, start/end date, status |
| **BA Usage Counter** | Per-buyer metered usage (e.g. `orders_this_month`) against a plan's limit |

---

## 3. Reports

| Report | Type | What it shows |
|---|---|---|
| **BA Portal Order Summary** | Script Report | Orders by buyer/status/date range, with totals |
| **BA Buyer Price Comparison** | Query Report | Every item's price across all buyer tiers, side by side |
| **BA Field Rep Visit Compliance** | Script Report | Planned vs. completed vs. skipped visits per rep, with a compliance % |
| **BA Subscription Expiry Report** | Query Report | Buyer subscriptions expiring within 30 days |

## 4. Workspace

A single **"Bizaxl Advantage"** workspace groups all three modules with
shortcuts to the core DocTypes and reports, laid out to match the
priority order from the source document (B2B Portal → Tiered Ladder →
Field Sales, top to bottom).

## 5. Notifications

Shipped as `Notification` fixtures (Settings → Notification in the desk
once installed — editable there without touching code):

| Name | Trigger | Recipients |
|---|---|---|
| **BA New Portal Order Submitted** | `BA Portal Order` submitted | Sales Manager role |
| **BA Portal Order Dispatched** | `status` → Dispatched | Buyer's email (fetched field) + Sales Manager |
| **BA Subscription Expiring Soon** | 7 days before `end_date` | Sales Manager role |
| **BA Low Stock Alert** | `BA Stock Snapshot.stock_status` → Out of Stock | Sales Manager + Stock Manager roles |

A fifth alert — notifying a field rep's manager the moment a visit is
logged — isn't a fixture, because "who manages this rep" is a lookup, not
a static condition. It's wired as a Python `doc_event` in `hooks.py` →
`utils.notify_manager_of_visit`, which creates a `Notification Log` entry
for the rep's `reports_to` manager (falling back to any Sales Manager if
none is set).

## 6. Roles & permissions

- **B2B Buyer** (new, no desk access) — portal-only role for buyers.
  `permission_query_conditions` in `hooks.py` restrict `BA Portal Order`,
  `BA Portal Buyer`, and `BA Visit Log` list views so a buyer only ever
  sees rows tied to their own linked `BA Portal Buyer` record — the same
  scoping principle as the "Customer"-role restriction in the source
  build plan (Phase 01 exit criteria).
- **Field Sales Rep** (new, desk access) — for reps who need
  `BA Route Plan` / `BA Visit Log` access from the desk or a future
  mobile client.
- Internal roles (Sales Manager, Stock Manager, System Manager) are
  **reused from core ERPNext** — no reason to duplicate those.

## 7. Scheduled jobs (`hooks.py` → `scheduler_events`)

| Job | Frequency | What it does |
|---|---|---|
| `sync_stock_snapshot` | Hourly | Refreshes `BA Stock Snapshot` from `Bin` for every catalog item |
| `check_subscription_expiry` | Daily | Flips `BA Buyer Subscription.status` to Expired once `end_date` has passed |
| `reset_monthly_usage_counters` | Monthly | Zeroes `BA Usage Counter` rows older than 30 days |

---

## 8. Installation

```bash
# from your bench directory, with an ERPNext v15+ site already created
bench get-app bizaxl_advantage /path/to/bizaxl_advantage   # or a git URL, see §10
bench --site your-site.local install-app bizaxl_advantage
bench --site your-site.local migrate
bench restart
```

After install:

1. **Assign roles** — give buyer-facing portal logins the `B2B Buyer`
   role, and field staff the `Field Sales Rep` role (plus `Employee` /
   `Sales User` if they also need desk access).
2. **Create your first `BA Buyer Price Tier`** and populate
   `BA Buyer Item Price` rows for the items you'll sell through the
   portal.
3. **Mark items** `Show On Portal` in `BA Portal Catalog Item` — nothing
   is visible on the portal until you do this explicitly (matches the
   "restrict what's self-orderable" requirement in Phase 02).
4. **Create `BA Portal Buyer` records** and link each one's `portal_user`
   field to the buyer's Website User account, so the permission
   restrictions in §6 actually take effect.
5. **Visit `/b2b-order`** as a logged-in buyer to confirm the Web Form
   renders and only shows that buyer's own past orders.
6. Run `bench --site your-site.local execute bizaxl_advantage.utils.sync_stock_snapshot`
   once manually to seed `BA Stock Snapshot` before the hourly job kicks in.

## 9. Known gaps / things to build next

Being direct about what this ships with vs. what it doesn't, so nobody's
surprised later:

- **No offline-first mobile client.** Your source doc flags this as
  mandatory for rural field reps (build plan §B, Phase 00). `BA Visit
  Log` and `BA Route Plan` are ready to be consumed by a mobile app via
  the standard Frappe REST/Client API, but that app itself isn't built
  here — it's a separate mobile engineering effort (offline sync, local
  DB, background push), correctly flagged in your own document as
  "highest build effort... build on demand."
- **No automatic Quotation → Sales Order conversion.** `BA Portal
  Order.create_sales_order()` exists as a callable method (wire it to a
  button or Server Script) but isn't auto-triggered on submit, so your
  team keeps the manual confirmation step the source document
  recommends for newer accounts.
- **Buyer ↔ Customer linkage is by name match**, in
  `create_sales_order()`. If you don't already have a 1:1 `Customer`
  record per `BA Portal Buyer`, that lookup will fail loudly rather than
  silently create duplicates — deliberately, since silent duplication of
  customer masters is worse than a blocked action.
- **Distributor system-to-system integration (Section 6 of your doc)**
  is explicitly out of scope here, per your document's own "don't build
  one-off connectors speculatively" guidance. Frappe's native REST API
  is already enabled; a per-distributor mapping layer is a build-on-demand
  item, not a default.

## 10. Getting this into git

This folder *is* the app root — point a fresh repo at it directly:

```bash
cd bizaxl_advantage
git init
git add .
git commit -m "Initial scaffold: B2B Ordering Portal, Field Sales Automation, Tiered Product Ladder"
git remote add origin <your-repo-url>
git push -u origin main
```
