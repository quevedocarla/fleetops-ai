CREATE EXTENSION IF NOT EXISTS vector;


CREATE TABLE IF NOT EXISTS contracts
(
    id              INTEGER PRIMARY KEY,
    customer_name   VARCHAR(200) NOT NULL,
    status          VARCHAR(50) NOT NULL
);


CREATE TABLE IF NOT EXISTS service_orders
(
    id              INTEGER PRIMARY KEY,
    contract_id     INTEGER NOT NULL
                    REFERENCES contracts(id),

    vehicle_plate   VARCHAR(20) NOT NULL,
    type            VARCHAR(50) NOT NULL,
    status          VARCHAR(50) NOT NULL,

    created_at      TIMESTAMP NOT NULL
                    DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS processing_queue
(
    id                  SERIAL PRIMARY KEY,

    service_order_id    INTEGER NOT NULL
                        REFERENCES service_orders(id),

    action              VARCHAR(100),
    status              VARCHAR(50) NOT NULL,
    error               TEXT,

    created_at          TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS knowledge_documents
(
    id          SERIAL PRIMARY KEY,
    source      VARCHAR(300) NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(768) NOT NULL
);


INSERT INTO contracts
(
    id,
    customer_name,
    status
)
VALUES
    (2001, 'Alpha', 'ACTIVE'),
    (2002, 'Beta', 'INACTIVE'),
    (2003, 'Gamma', 'ACTIVE')
ON CONFLICT (id)
DO UPDATE SET
    customer_name = EXCLUDED.customer_name,
    status = EXCLUDED.status;


INSERT INTO service_orders
(
    id,
    contract_id,
    vehicle_plate,
    type,
    status
)
VALUES
    (
        10234,
        2001,
        'ABC1D23',
        'INSTALLATION',
        'PENDING'
    ),
    (
        10235,
        2002,
        'DEF4G56',
        'INSTALLATION',
        'PENDING'
    ),
    (
        10236,
        2003,
        'GHI7J89',
        'MAINTENANCE',
        'COMPLETED'
    ),
    (
        10237,
        2001,
        'JKL1M23',
        'CANCELLATION',
        'PENDING'
    )
ON CONFLICT (id)
DO UPDATE SET
    contract_id = EXCLUDED.contract_id,
    vehicle_plate = EXCLUDED.vehicle_plate,
    type = EXCLUDED.type,
    status = EXCLUDED.status;


INSERT INTO processing_queue
(
    service_order_id,
    action,
    status,
    error
)
SELECT
    10234,
    'PROCESS_SERVICE_ORDER',
    'PENDING',
    NULL
WHERE NOT EXISTS
(
    SELECT 1
    FROM processing_queue
    WHERE service_order_id = 10234
);


INSERT INTO processing_queue
(
    service_order_id,
    action,
    status,
    error
)
SELECT
    10235,
    'PROCESS_SERVICE_ORDER',
    'ERROR',
    'Contract is inactive'
WHERE NOT EXISTS
(
    SELECT 1
    FROM processing_queue
    WHERE service_order_id = 10235
);


INSERT INTO processing_queue
(
    service_order_id,
    action,
    status,
    error
)
SELECT
    10236,
    'PROCESS_SERVICE_ORDER',
    'PROCESSED',
    NULL
WHERE NOT EXISTS
(
    SELECT 1
    FROM processing_queue
    WHERE service_order_id = 10236
);
