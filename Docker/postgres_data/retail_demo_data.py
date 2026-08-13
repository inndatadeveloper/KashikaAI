"""
Retail Demo Data Generator for Bag of Words
============================================
Realistic retail database with REAL-TIME feel:
  - 80% historical data (2022–2025)
  - 20% recent data (last 90 days including TODAY)
  - Today's orders, active sessions, pending shipments
  - Realistic weekly/seasonal patterns
  - Proper business hours distribution
"""

import argparse
import os
import random
from datetime import datetime, timedelta, date
import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from tqdm import tqdm

fake = Faker("en_US")
random.seed(42)
Faker.seed(42)

NOW        = datetime.now()
TODAY      = NOW.date()
START_DATE = datetime(2022, 1, 1)
END_DATE   = NOW   # up to RIGHT NOW
START_D    = START_DATE.date()

# ── helpers ────────────────────────────────────────────────────────────────────

def connect(args):
    url = os.environ.get("DATABASE_URL")
    if url:
        conn = psycopg2.connect(url)
    else:
        conn = psycopg2.connect(
            host=args.host, port=args.port,
            dbname=args.dbname, user=args.user, password=args.password,
        )
    conn.autocommit = False
    return conn

def bulk_insert(cur, table, columns, rows, page=5000):
    sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES %s"
    for i in range(0, len(rows), page):
        execute_values(cur, sql, rows[i:i+page])

def rand_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(0, delta)))

def rand_dt(start, end):
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.randint(0, max(0, int(delta))))

def business_hour_dt(target_date):
    """Return a datetime on target_date weighted toward business hours (9am-9pm)."""
    weights = [1,1,1,1,1,1,1,1,1,        # 0-8  (night, low)
               5,8,10,12,10,8,10,12,14,   # 9-17 (day, high)
               14,12,10,8,3,2]            # 18-23 (evening, med)
    hour = random.choices(range(24), weights=weights)[0]
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(target_date.year, target_date.month, target_date.day, hour, minute, second)

def weighted_date(start_date, end_date):
    """
    Pick a date with realistic distribution:
    - Recent 90 days get 3x more weight (feels live)
    - Weekends get slightly more orders
    - Dec/Nov get more (holiday season)
    """
    cutoff_recent = end_date - timedelta(days=90)
    if random.random() < 0.25:   # 25% of data in last 90 days
        d = rand_date(max(start_date, cutoff_recent.date()), end_date.date())
    else:
        d = rand_date(start_date, cutoff_recent.date())

    # boost holiday months
    if d.month in (11, 12) and random.random() < 0.3:
        d = rand_date(date(d.year, d.month, 1),
                      date(d.year, d.month, 28))
    return d

# ── schema ─────────────────────────────────────────────────────────────────────

SCHEMA = """
DROP TABLE IF EXISTS website_sessions  CASCADE;
DROP TABLE IF EXISTS product_reviews   CASCADE;
DROP TABLE IF EXISTS promotions        CASCADE;
DROP TABLE IF EXISTS returns           CASCADE;
DROP TABLE IF EXISTS order_items       CASCADE;
DROP TABLE IF EXISTS orders            CASCADE;
DROP TABLE IF EXISTS inventory         CASCADE;
DROP TABLE IF EXISTS employees         CASCADE;
DROP TABLE IF EXISTS products          CASCADE;
DROP TABLE IF EXISTS suppliers         CASCADE;
DROP TABLE IF EXISTS categories        CASCADE;
DROP TABLE IF EXISTS stores            CASCADE;
DROP TABLE IF EXISTS customers         CASCADE;

CREATE TABLE customers (
    customer_id     SERIAL PRIMARY KEY,
    first_name      VARCHAR(80)  NOT NULL,
    last_name       VARCHAR(80)  NOT NULL,
    email           VARCHAR(200) NOT NULL UNIQUE,
    phone           VARCHAR(30),
    date_of_birth   DATE,
    gender          VARCHAR(30),
    address_line1   VARCHAR(200),
    address_line2   VARCHAR(200),
    city            VARCHAR(100),
    state           VARCHAR(50),
    zip_code        VARCHAR(20),
    country         VARCHAR(80)  DEFAULT 'United States',
    loyalty_tier    VARCHAR(20)  DEFAULT 'Bronze',
    total_spent     NUMERIC(12,2) DEFAULT 0,
    created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE categories (
    category_id   SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE,
    parent_id     INT REFERENCES categories(category_id),
    description   TEXT,
    is_active     BOOLEAN DEFAULT TRUE
);

CREATE TABLE suppliers (
    supplier_id   SERIAL PRIMARY KEY,
    company_name  VARCHAR(200) NOT NULL,
    contact_name  VARCHAR(150),
    email         VARCHAR(200),
    phone         VARCHAR(30),
    country       VARCHAR(80),
    city          VARCHAR(100),
    rating        NUMERIC(3,2),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    sku             VARCHAR(50) NOT NULL UNIQUE,
    name            VARCHAR(300) NOT NULL,
    category_id     INT REFERENCES categories(category_id),
    supplier_id     INT REFERENCES suppliers(supplier_id),
    description     TEXT,
    cost_price      NUMERIC(10,2) NOT NULL,
    selling_price   NUMERIC(10,2) NOT NULL,
    weight_kg       NUMERIC(8,3),
    brand           VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE stores (
    store_id      SERIAL PRIMARY KEY,
    store_code    VARCHAR(20) NOT NULL UNIQUE,
    name          VARCHAR(200) NOT NULL,
    type          VARCHAR(30),
    address       VARCHAR(300),
    city          VARCHAR(100),
    state         VARCHAR(50),
    zip_code      VARCHAR(20),
    phone         VARCHAR(30),
    manager_name  VARCHAR(150),
    opened_date   DATE,
    is_active     BOOLEAN DEFAULT TRUE
);

CREATE TABLE employees (
    employee_id   SERIAL PRIMARY KEY,
    store_id      INT REFERENCES stores(store_id),
    first_name    VARCHAR(80)  NOT NULL,
    last_name     VARCHAR(80)  NOT NULL,
    email         VARCHAR(200) NOT NULL UNIQUE,
    role          VARCHAR(80),
    hire_date     DATE,
    salary        NUMERIC(10,2),
    is_active     BOOLEAN DEFAULT TRUE
);

CREATE TABLE inventory (
    inventory_id     SERIAL PRIMARY KEY,
    product_id       INT REFERENCES products(product_id),
    store_id         INT REFERENCES stores(store_id),
    quantity_on_hand INT NOT NULL DEFAULT 0,
    reorder_level    INT NOT NULL DEFAULT 20,
    last_restocked   DATE,
    UNIQUE (product_id, store_id)
);

CREATE TABLE orders (
    order_id        SERIAL PRIMARY KEY,
    customer_id     INT REFERENCES customers(customer_id),
    store_id        INT REFERENCES stores(store_id),
    order_date      TIMESTAMP NOT NULL,
    status          VARCHAR(30) DEFAULT 'Completed',
    channel         VARCHAR(30),
    subtotal        NUMERIC(12,2),
    discount_amount NUMERIC(10,2) DEFAULT 0,
    tax_amount      NUMERIC(10,2) DEFAULT 0,
    shipping_amount NUMERIC(10,2) DEFAULT 0,
    total_amount    NUMERIC(12,2),
    payment_method  VARCHAR(50),
    notes           TEXT
);

CREATE TABLE order_items (
    order_item_id   SERIAL PRIMARY KEY,
    order_id        INT REFERENCES orders(order_id),
    product_id      INT REFERENCES products(product_id),
    quantity        INT NOT NULL,
    unit_price      NUMERIC(10,2) NOT NULL,
    discount_pct    NUMERIC(5,2)  DEFAULT 0,
    line_total      NUMERIC(12,2) NOT NULL
);

CREATE TABLE returns (
    return_id       SERIAL PRIMARY KEY,
    order_id        INT REFERENCES orders(order_id),
    order_item_id   INT REFERENCES order_items(order_item_id),
    customer_id     INT REFERENCES customers(customer_id),
    return_date     TIMESTAMP NOT NULL,
    reason          VARCHAR(100),
    quantity        INT NOT NULL DEFAULT 1,
    refund_amount   NUMERIC(10,2),
    status          VARCHAR(30) DEFAULT 'Approved'
);

CREATE TABLE promotions (
    promotion_id    SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    type            VARCHAR(50),
    discount_value  NUMERIC(8,2),
    start_date      DATE,
    end_date        DATE,
    min_order_value NUMERIC(10,2),
    category_id     INT REFERENCES categories(category_id),
    is_active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE product_reviews (
    review_id       SERIAL PRIMARY KEY,
    product_id      INT REFERENCES products(product_id),
    customer_id     INT REFERENCES customers(customer_id),
    order_id        INT REFERENCES orders(order_id),
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title           VARCHAR(200),
    body            TEXT,
    is_verified     BOOLEAN DEFAULT TRUE,
    helpful_votes   INT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE website_sessions (
    session_id      SERIAL PRIMARY KEY,
    customer_id     INT REFERENCES customers(customer_id),
    session_start   TIMESTAMP NOT NULL,
    session_end     TIMESTAMP,
    device_type     VARCHAR(30),
    os              VARCHAR(50),
    browser         VARCHAR(50),
    source          VARCHAR(80),
    landing_page    VARCHAR(300),
    pages_viewed    INT DEFAULT 1,
    converted       BOOLEAN DEFAULT FALSE,
    order_id        INT REFERENCES orders(order_id)
);

CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_store      ON orders(store_id);
CREATE INDEX idx_orders_date       ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_prod  ON order_items(product_id);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_store   ON inventory(store_id);
CREATE INDEX idx_reviews_product   ON product_reviews(product_id);
CREATE INDEX idx_sessions_customer ON website_sessions(customer_id);
CREATE INDEX idx_sessions_start    ON website_sessions(session_start);
"""

# ── reference data ─────────────────────────────────────────────────────────────

CATEGORY_TREE = {
    "Electronics":        ["Smartphones","Laptops","Tablets","Cameras","Audio","Smart Home","Wearables"],
    "Clothing & Apparel": ["Men's Clothing","Women's Clothing","Kids' Clothing","Sportswear","Footwear","Accessories"],
    "Home & Garden":      ["Furniture","Kitchen","Bedding","Garden & Outdoors","Lighting","Storage & Organization"],
    "Sports & Fitness":   ["Exercise Equipment","Outdoor Sports","Team Sports","Yoga & Pilates","Water Sports"],
    "Beauty & Personal":  ["Skincare","Hair Care","Makeup","Fragrances","Men's Grooming"],
    "Books & Media":      ["Fiction","Non-Fiction","Educational","Music","Movies & TV"],
    "Food & Grocery":     ["Snacks & Beverages","Organic & Natural","International Foods","Bakery","Dairy & Eggs"],
    "Toys & Games":       ["Action Figures","Board Games","Educational Toys","Outdoor Play","Video Games"],
    "Automotive":         ["Car Accessories","Tools & Equipment","Cleaning","Lighting & Electrical"],
    "Health & Wellness":  ["Vitamins & Supplements","Medical Supplies","Personal Care","Baby & Child"],
}

BRANDS = ["TechNova","UrbanStyle","PeakPerform","NatureBliss","HomeComfort","SwiftGear",
          "LuxeLine","EcoWave","ProCraft","Vitality","SmartHome+","FreshPick","TrendSet",
          "ActiveLife","PurePath","ClearVision","SoundWave","FitPulse","GreenLeaf","BoldMove",
          "Samsung","Apple","Nike","Adidas","Sony","LG","Philips","Bosch","Levi's","Zara"]

STORE_TYPES     = ["Flagship","Standard","Outlet","Online"]
CHANNELS        = ["In-Store","In-Store","Online","Online","Mobile App"]   # weighted
PAYMENT_METHODS = ["Credit Card","Credit Card","Debit Card","PayPal","Apple Pay","Google Pay","Cash","Gift Card"]
RETURN_REASONS  = ["Wrong size","Defective product","Changed mind","Not as described",
                   "Wrong item shipped","Damaged in shipping","Duplicate order","Better price found"]
LOYALTY_TIERS   = ["Bronze","Silver","Gold","Platinum"]
REVIEW_TITLES   = ["Excellent product!","Very satisfied","Good value for money","Highly recommend",
                   "Exceeded my expectations","Average product","Not what I expected",
                   "Would buy again","Great quality","Fast shipping, great product",
                   "Decent but could be better","Five stars!","Love it!","OK for the price"]

# Realistic order statuses — recent ones stay Pending/Shipped
def order_status(order_date):
    days_ago = (NOW - order_date).days
    if days_ago == 0:
        return random.choices(["Pending","Processing"], weights=[60,40])[0]
    elif days_ago <= 2:
        return random.choices(["Processing","Shipped","Pending"], weights=[40,40,20])[0]
    elif days_ago <= 7:
        return random.choices(["Shipped","Completed","Processing"], weights=[40,50,10])[0]
    elif days_ago <= 30:
        return random.choices(["Completed","Shipped","Cancelled"], weights=[80,15,5])[0]
    else:
        return random.choices(["Completed","Cancelled","Returned"], weights=[88,8,4])[0]

# ── generators ─────────────────────────────────────────────────────────────────

def gen_categories(cur):
    print("  → categories")
    rows = [(p, None, fake.sentence(nb_words=8), True) for p in CATEGORY_TREE]
    bulk_insert(cur, "categories", ["name","parent_id","description","is_active"], rows)
    cur.execute("SELECT category_id, name FROM categories")
    cat_map = {name: cid for cid, name in cur.fetchall()}
    child_rows = []
    for parent, children in CATEGORY_TREE.items():
        for child in children:
            child_rows.append((child, cat_map[parent], fake.sentence(nb_words=8), True))
    bulk_insert(cur, "categories", ["name","parent_id","description","is_active"], child_rows)
    cur.execute("SELECT category_id FROM categories")
    return [r[0] for r in cur.fetchall()]

def gen_suppliers(cur, n=200):
    print(f"  → suppliers ({n})")
    countries = ["United States","China","Germany","India","Japan","South Korea","Italy","France","UK","Canada"]
    rows = []
    for _ in range(n):
        rows.append((fake.company(), fake.name(), fake.company_email(),
                     fake.phone_number()[:20], random.choice(countries), fake.city(),
                     round(random.uniform(2.5,5.0),2), True, rand_dt(START_DATE, NOW)))
    bulk_insert(cur, "suppliers",
        ["company_name","contact_name","email","phone","country","city","rating","is_active","created_at"], rows)
    cur.execute("SELECT supplier_id FROM suppliers")
    return [r[0] for r in cur.fetchall()]

def gen_products(cur, cat_ids, supplier_ids, n=2000):
    print(f"  → products ({n})")
    rows = []
    for i in range(n):
        cost  = round(random.uniform(2,800),2)
        price = round(cost * random.uniform(1.15,3.5),2)
        rows.append((f"SKU-{1000000+i}", fake.catch_phrase()[:200],
                     random.choice(cat_ids), random.choice(supplier_ids),
                     fake.paragraph(nb_sentences=3), cost, price,
                     round(random.uniform(0.1,20.0),3), random.choice(BRANDS),
                     True, rand_dt(START_DATE, NOW)))
    bulk_insert(cur, "products",
        ["sku","name","category_id","supplier_id","description","cost_price","selling_price",
         "weight_kg","brand","is_active","created_at"], rows)
    cur.execute("SELECT product_id, selling_price FROM products")
    return {r[0]: r[1] for r in cur.fetchall()}

def gen_stores(cur, n=50):
    print(f"  → stores ({n})")
    rows = []
    for i in range(n):
        stype = STORE_TYPES[i % len(STORE_TYPES)]
        rows.append((f"STR-{1000+i}",
                     f"{fake.city()} {stype} Store" if stype != "Online" else "Online Store",
                     stype, fake.street_address(), fake.city(), fake.state(), fake.zipcode(),
                     fake.phone_number()[:20], fake.name(),
                     rand_date(date(2010,1,1), date(2023,12,31)), True))
    bulk_insert(cur, "stores",
        ["store_code","name","type","address","city","state","zip_code",
         "phone","manager_name","opened_date","is_active"], rows)
    cur.execute("SELECT store_id FROM stores")
    return [r[0] for r in cur.fetchall()]

def gen_employees(cur, store_ids, n=500):
    print(f"  → employees ({n})")
    roles = ["Store Manager","Assistant Manager","Sales Associate","Cashier",
             "Inventory Specialist","Customer Service Rep","Visual Merchandiser",
             "Security","Logistics Coordinator","HR Specialist"]
    rows = []
    for _ in range(n):
        rows.append((random.choice(store_ids), fake.first_name(), fake.last_name(),
                     fake.unique.email(), random.choice(roles),
                     rand_date(date(2015,1,1), TODAY),
                     round(random.uniform(28000,95000),2), True))
    bulk_insert(cur, "employees",
        ["store_id","first_name","last_name","email","role","hire_date","salary","is_active"], rows)

def gen_customers(cur, n=15000):
    print(f"  → customers ({n})")
    rows = []
    for _ in range(n):
        tier     = random.choices(LOYALTY_TIERS, weights=[50,30,15,5])[0]
        # 15% of customers signed up in last 90 days (new customers!)
        if random.random() < 0.15:
            signup = rand_dt(NOW - timedelta(days=90), NOW)
        else:
            signup = rand_dt(START_DATE, NOW - timedelta(days=90))
        rows.append((fake.first_name(), fake.last_name(), fake.unique.email(),
                     fake.phone_number()[:20],
                     rand_date(date(1955,1,1), date(2005,12,31)),
                     random.choice(["Male","Female","Non-binary","Other"]),
                     fake.street_address(), fake.secondary_address(),
                     fake.city(), fake.state(), fake.zipcode(), "United States",
                     tier, 0, signup, signup))
    bulk_insert(cur, "customers",
        ["first_name","last_name","email","phone","date_of_birth","gender",
         "address_line1","address_line2","city","state","zip_code","country",
         "loyalty_tier","total_spent","created_at","updated_at"], rows)
    cur.execute("SELECT customer_id FROM customers")
    return [r[0] for r in cur.fetchall()]

def gen_inventory(cur, product_ids, store_ids):
    print(f"  → inventory (~10,000 rows, includes low-stock alerts)")
    combos = set()
    while len(combos) < min(10000, len(product_ids)*len(store_ids)):
        combos.add((random.choice(product_ids), random.choice(store_ids)))
    rows = []
    for pid, sid in combos:
        qty = random.randint(0, 500)
        # 8% of items are critically low stock (good for demo alerts)
        if random.random() < 0.08:
            qty = random.randint(0, 5)
        rows.append((pid, sid, qty, random.randint(10,50),
                     rand_date(date(2024,1,1), TODAY)))
    bulk_insert(cur, "inventory",
        ["product_id","store_id","quantity_on_hand","reorder_level","last_restocked"], rows)

def gen_promotions(cur, cat_ids, n=200):
    print(f"  → promotions ({n}, some active RIGHT NOW)")
    promo_types = ["Percentage","Fixed","BOGO","Free Shipping"]
    rows = []
    for i in range(n):
        # 20% of promotions are currently active
        if i < 40:
            start = TODAY - timedelta(days=random.randint(1,10))
            end   = TODAY + timedelta(days=random.randint(1,20))
            is_active = True
        else:
            start = rand_date(START_D, TODAY)
            end   = start + timedelta(days=random.randint(7,60))
            is_active = end >= TODAY
        rows.append((f"PROMO-{i+1} "+fake.catch_phrase()[:80],
                     random.choice(promo_types),
                     round(random.uniform(5,50),2),
                     start, end,
                     round(random.uniform(0,100),2),
                     random.choice(cat_ids), is_active))
    bulk_insert(cur, "promotions",
        ["name","type","discount_value","start_date","end_date",
         "min_order_value","category_id","is_active"], rows)

def gen_orders_and_items(cur, customer_ids, store_ids, product_price_map, n_orders=50000):
    print(f"  → orders ({n_orders}) + order_items with real-time distribution")
    product_ids = list(product_price_map.keys())
    order_rows  = []

    for _ in tqdm(range(n_orders), desc="     building orders"):
        # pick date with realistic recency weighting
        order_d  = weighted_date(START_D, END_DATE)
        order_dt = business_hour_dt(order_d)
        # don't exceed NOW
        if order_dt > NOW:
            order_dt = NOW - timedelta(minutes=random.randint(1,120))

        channel = random.choice(CHANNELS)
        picked  = random.sample(product_ids, random.randint(1,6))

        subtotal     = 0
        item_details = []
        for pid in picked:
            qty    = random.randint(1,5)
            disc   = round(random.choice([0,0,0,5,10,15,20]),2)
            uprice = float(product_price_map[pid])
            line   = round(qty * uprice * (1-disc/100),2)
            subtotal += line
            item_details.append((pid, qty, uprice, disc, line))

        discount = round(subtotal * random.choice([0,0,0.05,0.10]),2)
        tax      = round((subtotal-discount)*0.08,2)
        shipping = 0 if channel=="In-Store" else round(random.choice([0,4.99,7.99,12.99]),2)
        total    = round(subtotal-discount+tax+shipping,2)
        status   = order_status(order_dt)

        order_rows.append((random.choice(customer_ids), random.choice(store_ids),
                           order_dt, status, channel, round(subtotal,2),
                           discount, tax, shipping, total,
                           random.choice(PAYMENT_METHODS), None, item_details))

    # ── insert orders ──
    pure = [r[:-1] for r in order_rows]
    bulk_insert(cur, "orders",
        ["customer_id","store_id","order_date","status","channel","subtotal",
         "discount_amount","tax_amount","shipping_amount","total_amount",
         "payment_method","notes"], pure)

    cur.execute("SELECT order_id FROM orders ORDER BY order_id")
    order_ids = [r[0] for r in cur.fetchall()]

    # ── insert order_items ──
    item_rows = []
    for oid, order in zip(order_ids, order_rows):
        for pid,qty,uprice,disc,line in order[-1]:
            item_rows.append((oid, pid, qty, uprice, disc, line))
    bulk_insert(cur, "order_items",
        ["order_id","product_id","quantity","unit_price","discount_pct","line_total"], item_rows)

    # ── update customer totals + loyalty tier ──
    print("     updating customer totals …")
    cur.execute("""
        UPDATE customers c SET
            total_spent  = sub.total,
            loyalty_tier = CASE
                WHEN sub.total >= 5000 THEN 'Platinum'
                WHEN sub.total >= 2000 THEN 'Gold'
                WHEN sub.total >= 500  THEN 'Silver'
                ELSE 'Bronze' END,
            updated_at = NOW()
        FROM (SELECT customer_id, SUM(total_amount) AS total
              FROM orders GROUP BY customer_id) sub
        WHERE c.customer_id = sub.customer_id
    """)
    return order_ids

def gen_returns(cur, n=10000):
    print(f"  → returns ({n})")
    cur.execute("""
        SELECT oi.order_item_id, oi.order_id, o.customer_id, oi.line_total, oi.quantity
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status IN ('Completed','Returned')
        LIMIT 60000
    """)
    candidates = cur.fetchall()
    sampled    = random.sample(candidates, min(n, len(candidates)))
    rows = []
    for item_id, oid, cid, line_total, qty in sampled:
        ret_qty    = random.randint(1, max(1,qty))
        # recent returns within last 30 days
        if random.random() < 0.15:
            ret_dt = rand_dt(NOW-timedelta(days=30), NOW)
        else:
            ret_dt = rand_dt(START_DATE, NOW-timedelta(days=30))
        rows.append((oid, item_id, cid, ret_dt,
                     random.choice(RETURN_REASONS), ret_qty,
                     round(float(line_total)*ret_qty/qty,2),
                     random.choices(["Approved","Rejected","Pending"],weights=[75,10,15])[0]))
    bulk_insert(cur, "returns",
        ["order_id","order_item_id","customer_id","return_date","reason",
         "quantity","refund_amount","status"], rows)

def gen_reviews(cur, n=20000):
    print(f"  → product_reviews ({n})")
    cur.execute("""
        SELECT oi.product_id, oi.order_id, o.customer_id
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status = 'Completed'
        LIMIT 80000
    """)
    candidates = cur.fetchall()
    sampled    = random.sample(candidates, min(n, len(candidates)))
    rows = []
    for pid, oid, cid in sampled:
        rating = random.choices([1,2,3,4,5], weights=[3,5,10,30,52])[0]
        if random.random() < 0.1:
            created = rand_dt(NOW-timedelta(days=14), NOW)   # fresh reviews
        else:
            created = rand_dt(START_DATE, NOW-timedelta(days=14))
        rows.append((pid, cid, oid, rating, random.choice(REVIEW_TITLES),
                     fake.paragraph(nb_sentences=random.randint(1,5)),
                     random.random()>0.1, random.randint(0,200), created))
    bulk_insert(cur, "product_reviews",
        ["product_id","customer_id","order_id","rating","title","body",
         "is_verified","helpful_votes","created_at"], rows)

def gen_sessions(cur, customer_ids, order_ids, n=30000):
    print(f"  → website_sessions ({n}, includes active TODAY sessions)")
    devices  = ["Desktop","Mobile","Mobile","Tablet"]   # mobile heavy
    oses     = ["Windows","macOS","iOS","iOS","Android","Linux"]
    browsers = ["Chrome","Chrome","Firefox","Safari","Edge","Samsung Browser"]
    sources  = ["Organic Search","Organic Search","Paid Search","Email","Social Media","Direct","Referral"]
    pages    = ["/home","/products","/sale","/new-arrivals","/account",
                "/cart","/checkout","/category/electronics","/category/clothing","/category/home"]
    rows = []
    for i in range(n):
        cid   = random.choice(customer_ids) if random.random()<0.65 else None

        # 10% of sessions are from TODAY (live traffic feel)
        if i < n * 0.10:
            start = business_hour_dt(TODAY)
            if start > NOW:
                start = NOW - timedelta(minutes=random.randint(1,60))
            # some still active (no end time)
            if random.random() < 0.3:
                end = None   # session still open!
            else:
                end = start + timedelta(seconds=random.randint(30,1800))
        else:
            d     = weighted_date(START_D, END_DATE)
            start = business_hour_dt(d)
            if start > NOW:
                start = NOW - timedelta(hours=random.randint(1,24))
            end   = start + timedelta(seconds=random.randint(30,3600))

        converted = random.random() < 0.12 and end is not None
        oid       = random.choice(order_ids) if converted else None

        rows.append((cid, start, end,
                     random.choice(devices), random.choice(oses), random.choice(browsers),
                     random.choice(sources), random.choice(pages),
                     random.randint(1,20), converted, oid))
    bulk_insert(cur, "website_sessions",
        ["customer_id","session_start","session_end","device_type","os","browser",
         "source","landing_page","pages_viewed","converted","order_id"], rows)

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",     default="localhost")
    parser.add_argument("--port",     default=5432, type=int)
    parser.add_argument("--dbname",   default="retail_demo")
    parser.add_argument("--user",     default="postgres")
    parser.add_argument("--password", default="")
    args = parser.parse_args()

    print(f"\n🛍️  Retail Demo Data Generator — Bag of Words")
    print(f"   Data range: Jan 2022 → NOW ({NOW.strftime('%Y-%m-%d %H:%M')})\n")
    print("Connecting to PostgreSQL …")
    conn = connect(args)
    cur  = conn.cursor()

    print("Creating schema …")
    cur.execute(SCHEMA)
    conn.commit()

    print(f"\nGenerating realistic retail data …\n")

    cat_ids           = gen_categories(cur);                         conn.commit()
    supplier_ids      = gen_suppliers(cur);                          conn.commit()
    product_price_map = gen_products(cur, cat_ids, supplier_ids);   conn.commit()
    store_ids         = gen_stores(cur);                             conn.commit()
    gen_employees(cur, store_ids);                                   conn.commit()
    customer_ids      = gen_customers(cur);                          conn.commit()
    gen_inventory(cur, list(product_price_map.keys()), store_ids);  conn.commit()
    gen_promotions(cur, cat_ids);                                    conn.commit()
    order_ids         = gen_orders_and_items(cur, customer_ids, store_ids, product_price_map); conn.commit()
    gen_returns(cur);                                                conn.commit()
    gen_reviews(cur);                                                conn.commit()
    gen_sessions(cur, customer_ids, order_ids);                     conn.commit()

    # ── summary ──
    tables = ["customers","categories","suppliers","products","stores","employees",
              "inventory","promotions","orders","order_items","returns",
              "product_reviews","website_sessions"]
    print("\n✅  Done! Row counts:\n")
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"   {t:<25} {cur.fetchone()[0]:>10,}")

    # quick sanity: today's orders
    cur.execute("SELECT COUNT(*) FROM orders WHERE order_date::date = CURRENT_DATE")
    todays = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM website_sessions WHERE session_end IS NULL")
    active_sessions = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Pending','Processing','Shipped')")
    live_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM inventory WHERE quantity_on_hand <= reorder_level")
    low_stock = cur.fetchone()[0]

    print(f"""
┌─────────────────────────────────────────────────┐
│  📊  REAL-TIME SNAPSHOT (as of {NOW.strftime('%Y-%m-%d %H:%M')})   │
├─────────────────────────────────────────────────┤
│  Orders placed TODAY          {todays:>6,}           │
│  Active website sessions      {active_sessions:>6,}           │
│  Live orders (pending/shipped){live_orders:>6,}           │
│  Low stock alerts             {low_stock:>6,}           │
└─────────────────────────────────────────────────┘

🎉  Try these in Bag of Words:
  • "How many orders have we received today?"
  • "Show me this week's revenue vs last week"
  • "Which products are low on stock right now?"
  • "What are active promotions running this week?"
  • "Show pending and processing orders"
  • "Which customers placed orders in the last 24 hours?"
  • "Monthly revenue trend from 2022 to today"
  • "Top selling products this month vs last month"
""")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
