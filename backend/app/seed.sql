INSERT INTO branches (name) VALUES
    ('Scranton'),
    ('Stamford'),
    ('Utica');

INSERT INTO products (sku, name, low_stock_threshold) VALUES
    ('PPR-COPY-LTR-20', 'Standard Copy Paper (Letter, 20lb)', 50),
    ('PPR-CARD-PREM',   'Premium Cardstock',                  40),
    ('ENV-MANILA-9X12', 'Manila Envelopes (9x12)',            30),
    ('PAD-LEGAL-YELLOW', 'Legal Pads (Yellow, 8.5x11)',        60),
    ('PPR-RECYC-REAM',  'Recycled Reams',                     35),
    ('PPR-COPY-LGL-20', 'Legal-Size Copy Paper (20lb)',       50);

-- starting stock levels
INSERT INTO stock_levels (product_id, branch_id, quantity, version) VALUES
    (1, 1, 120, 0),
    (1, 2,  80, 0),
    (1, 3, 200, 0),
    (2, 1,  30, 0),
    (2, 2,  75, 0),
    (2, 3,  15, 0),
    (3, 1, 200, 0),
    (3, 2,  50, 0),
    (3, 3,  90, 0),
    (4, 1,  45, 0),
    (4, 2,  20, 0),
    (4, 3, 300, 0),
    (5, 1,  28, 0),
    (5, 2,  60, 0),
    (5, 3, 110, 0),
    (6, 1,  33, 0),
    (6, 2,  90, 0),
    (6, 3,  70, 0);

-- historical movements so the depletion-rate chart isn't empty on first load
-- (scranton, product 1)
INSERT INTO stock_movements (product_id, branch_id, change_qty, reason, created_at) VALUES
    (1, 1, 200, 'restock',  now() - interval '25 days'),
    (1, 1, -15, 'sale',     now() - interval '24 days'),
    (1, 1, -20, 'sale',     now() - interval '22 days'),
    (1, 1, -10, 'sale',     now() - interval '20 days'),
    (1, 1, 100, 'restock',  now() - interval '18 days'),
    (1, 1, -25, 'sale',     now() - interval '15 days'),
    (1, 1, -18, 'sale',     now() - interval '12 days'),
    (1, 1, 140, 'restock',  now() - interval '10 days'),
    (1, 1, -22, 'sale',     now() - interval '8 days'),
    (1, 1, -15, 'sale',     now() - interval '5 days'),
    (1, 1, -30, 'sale',     now() - interval '3 days'),
    (1, 1, -20, 'sale',     now() - interval '1 day'),
    -- scranton, product 2 (low stock)
    (2, 1,  100, 'restock', now() - interval '20 days'),
    (2, 1,  -20, 'sale',    now() - interval '18 days'),
    (2, 1,  -18, 'sale',    now() - interval '14 days'),
    (2, 1,  -15, 'damaged', now() - interval '10 days'),
    (2, 1,  -12, 'sale',    now() - interval '6 days'),
    (2, 1,  -25, 'sale',    now() - interval '2 days'),
    -- stamford, product 1
    (1, 2,  150, 'restock', now() - interval '20 days'),
    (1, 2,  -30, 'sale',    now() - interval '15 days'),
    (1, 2,  -20, 'sale',    now() - interval '10 days'),
    (1, 2,  -15, 'sale',    now() - interval '5 days'),
    (1, 2,  -18, 'sale',    now() - interval '1 day'),
    -- stamford, product 4 (low stock)
    (4, 2,  100, 'restock', now() - interval '15 days'),
    (4, 2,  -25, 'sale',    now() - interval '10 days'),
    (4, 2,  -18, 'sale',    now() - interval '7 days'),
    (4, 2,  -20, 'sale',    now() - interval '3 days'),
    (4, 2,  -12, 'sale',    now() - interval '1 day'),
    -- utica, product 2 (already low at 15)
    (2, 3,  100, 'restock', now() - interval '20 days'),
    (2, 3,  -30, 'sale',    now() - interval '12 days'),
    (2, 3,  -25, 'sale',    now() - interval '8 days'),
    (2, 3,  -18, 'damaged', now() - interval '4 days'),
    (2, 3,  -12, 'sale',    now() - interval '1 day');