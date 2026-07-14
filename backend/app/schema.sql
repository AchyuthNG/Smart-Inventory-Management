CREATE TABLE branches (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(150) NOT NULL,
    low_stock_threshold  INTEGER NOT NULL DEFAULT 50
);

CREATE TABLE stock_levels (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    branch_id   INTEGER NOT NULL REFERENCES branches(id),
    quantity    INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    version     INTEGER NOT NULL DEFAULT 0,
    UNIQUE (product_id, branch_id)
);

CREATE TABLE stock_movements (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    branch_id       INTEGER NOT NULL REFERENCES branches(id),
    change_qty      INTEGER NOT NULL,
    reason          VARCHAR(100),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE low_stock_alerts (
    id              SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL REFERENCES products(id),
    branch_id       INTEGER NOT NULL REFERENCES branches(id),
    triggered_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved        BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX idx_movements_product_branch ON stock_movements(product_id, branch_id);
CREATE INDEX idx_movements_created_at ON stock_movements(created_at);
CREATE INDEX idx_alerts_unresolved ON low_stock_alerts(resolved) WHERE resolved = false;