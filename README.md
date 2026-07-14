# Schrute Paper Co. — Smart Inventory Management System

Track paper stock across branches, log every inbound/outbound movement, and auto-flag low-stock or fast-depleting items — with concurrency-safe writes so multiple reps can update the same SKU at once.

Fictional mid-sized paper distribution company. Warehouses are "branches," products are paper goods.

## Stack

- **Backend:** FastAPI + psycopg2 (raw SQL, no ORM)
- **Frontend:** React + Vite + Recharts
- **DB:** PostgreSQL 16 (Docker)
- **Containers:** Docker Compose (db + backend + frontend)

## Quick Start

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API / Swagger: http://localhost:8000/docs

Schema and seed data (3 branches, 6 products, opening stock + historical movements) load automatically on first boot.

## What It Does

- **Stock tracking** — current stock per product per branch with a derived `stock_levels` table kept in sync with an append-only `stock_movements` ledger.
- **Concurrency-safe movements** — `POST /api/movements` uses an atomic conditional `UPDATE … WHERE quantity + change_qty >= 0` inside a single transaction with the ledger insert. Oversell attempts return HTTP 409 and nothing is written.
- **Low-stock alerts** — two rule-based checks run as a background task after each movement:
  - _Threshold:_ quantity < product's `low_stock_threshold`
  - _Depletion-rate:_ current stock runs out within 3 days at the recent 7-day avg daily outbound rate
- **Ledger browser** — `GET /api/movements` with pagination + filtering (branch, product, reason), rendered as a table in the dashboard.
- **Dashboard** — stock levels table with red "Low" badges, grouped bar chart (stock by product, per branch), stock movements ledger, and active alerts panel.
- **Real-time** — polling (7 s / 10 s) plus immediate refetch after recording a movement.

## API Endpoints

| Method | Endpoint                    | Purpose                                                     |
|--------|-----------------------------|-------------------------------------------------------------|
| POST   | `/api/movements`            | Record a stock movement (transactional, concurrency-safe)   |
| GET    | `/api/movements`            | Paginated, filterable append-only ledger                    |
| GET    | `/api/stock`                | Current stock levels (filter by `branch_id` / `product_id`) |
| GET    | `/api/products`             | List products with thresholds                               |
| GET    | `/api/branches`             | List branches                                               |
| GET    | `/api/alerts`               | Active low-stock alerts                                     |
| GET    | `/api/stats/depletion-rate` | Average daily outbound quantity per product (7/30 days)     |
| GET    | `/api/health`               | Health check                                                |
## Testing Concurrency

After the stack is running:

```bash
python3 tests/test_concurrency.py \
  --base http://localhost:8000 \
  --product-id 1 --branch-id 1 --each 30 --workers 8
```

Fires N concurrent outbound requests against the same SKU and asserts the quantity never goes negative and never drifts from the ledger sum.

```bash
bash tests/smoke_test.sh http://localhost:8000
```

Hits every endpoint and prints the responses.

## Project Structure

```
├── docker-compose.yml
├── .env
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── schema.sql          # DB schema (auto-loads on first boot)
│       ├── seed.sql            # seed data (branches, products, stock, history)
│       ├── db.py               # connection pool
│       ├── models.py           # pydantic schemas
│       ├── alerts.py           # low-stock + depletion-rate rules
│       └── main.py             # FastAPI app (8 endpoints)
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── api.js
│       ├── usePolling.js
│       ├── App.jsx
│       ├── styles.css
│       └── components/
│           ├── StockTable.jsx
│           ├── MovementsForm.jsx
│           ├── BarChart.jsx
│           ├── AlertsPanel.jsx
│           └── Ledger.jsx
└── tests/
    ├── test_concurrency.py
```

## Reset

```bash
docker compose down -v && docker compose up --build
```

`-v` wipes the DB volume so schema + seed reload from scratch.
