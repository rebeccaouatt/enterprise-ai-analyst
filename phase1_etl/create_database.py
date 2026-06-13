import sqlite3
import os

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/financial.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS quarterly_revenue (
    id INTEGER PRIMARY KEY,
    company TEXT,
    year INTEGER,
    quarter TEXT,
    segment TEXT,
    revenue_usd_billions REAL
)
''')

data = [
    # Apple
    ("Apple", 2022, "Q1", "iPhone",    71.6),
    ("Apple", 2022, "Q1", "Mac",       10.9),
    ("Apple", 2022, "Q1", "iPad",       7.2),
    ("Apple", 2022, "Q1", "Wearables",  8.7),
    ("Apple", 2022, "Q1", "Services",  19.5),
    ("Apple", 2022, "Q3", "iPhone",    40.7),
    ("Apple", 2022, "Q3", "Mac",        7.4),
    ("Apple", 2022, "Q3", "iPad",       7.2),
    ("Apple", 2022, "Q3", "Wearables",  8.1),
    ("Apple", 2022, "Q3", "Services",  19.6),
    ("Apple", 2023, "Q1", "iPhone",    65.8),
    ("Apple", 2023, "Q1", "Mac",        7.7),
    ("Apple", 2023, "Q1", "iPad",       9.4),
    ("Apple", 2023, "Q1", "Wearables",  8.8),
    ("Apple", 2023, "Q1", "Services",  20.9),
    ("Apple", 2023, "Q3", "iPhone",    39.7),
    ("Apple", 2023, "Q3", "Mac",        7.0),
    ("Apple", 2023, "Q3", "iPad",       5.8),
    ("Apple", 2023, "Q3", "Wearables",  8.3),
    ("Apple", 2023, "Q3", "Services",  21.2),
    # Microsoft
    ("Microsoft", 2022, "Q1", "Productivity", 16.5),
    ("Microsoft", 2022, "Q1", "Cloud",        20.3),
    ("Microsoft", 2022, "Q1", "Personal",     13.3),
    ("Microsoft", 2022, "Q3", "Productivity", 15.8),
    ("Microsoft", 2022, "Q3", "Cloud",        19.1),
    ("Microsoft", 2022, "Q3", "Personal",     14.5),
    ("Microsoft", 2023, "Q1", "Productivity", 17.5),
    ("Microsoft", 2023, "Q1", "Cloud",        22.1),
    ("Microsoft", 2023, "Q1", "Personal",     13.3),
    ("Microsoft", 2023, "Q3", "Productivity", 18.3),
    ("Microsoft", 2023, "Q3", "Cloud",        24.0),
    ("Microsoft", 2023, "Q3", "Personal",     13.2),
    # Google
    ("Google", 2022, "Q1", "Search",   39.6),
    ("Google", 2022, "Q1", "YouTube",   6.9),
    ("Google", 2022, "Q1", "Cloud",     5.8),
    ("Google", 2022, "Q3", "Search",   39.5),
    ("Google", 2022, "Q3", "YouTube",   7.1),
    ("Google", 2022, "Q3", "Cloud",     6.9),
    ("Google", 2023, "Q1", "Search",   40.4),
    ("Google", 2023, "Q1", "YouTube",   6.7),
    ("Google", 2023, "Q1", "Cloud",     7.5),
    ("Google", 2023, "Q3", "Search",   44.0),
    ("Google", 2023, "Q3", "YouTube",   7.9),
    ("Google", 2023, "Q3", "Cloud",     8.4),
    # Amazon
    ("Amazon", 2022, "Q1", "Online Stores", 51.1),
    ("Amazon", 2022, "Q1", "AWS",           18.4),
    ("Amazon", 2022, "Q1", "Advertising",    7.9),
    ("Amazon", 2022, "Q3", "Online Stores", 53.5),
    ("Amazon", 2022, "Q3", "AWS",           20.5),
    ("Amazon", 2022, "Q3", "Advertising",    9.5),
    ("Amazon", 2023, "Q1", "Online Stores", 51.1),
    ("Amazon", 2023, "Q1", "AWS",           21.4),
    ("Amazon", 2023, "Q1", "Advertising",   10.0),
    ("Amazon", 2023, "Q3", "Online Stores", 57.3),
    ("Amazon", 2023, "Q3", "AWS",           23.4),
    ("Amazon", 2023, "Q3", "Advertising",   12.1),
    # Meta
    ("Meta", 2022, "Q1", "Advertising", 27.9),
    ("Meta", 2022, "Q1", "Other",         0.7),
    ("Meta", 2022, "Q3", "Advertising", 27.2),
    ("Meta", 2022, "Q3", "Other",         0.3),
    ("Meta", 2023, "Q1", "Advertising", 28.1),
    ("Meta", 2023, "Q1", "Other",         0.2),
    ("Meta", 2023, "Q3", "Advertising", 33.6),
    ("Meta", 2023, "Q3", "Other",         0.3),
]

cursor.executemany(
    "INSERT INTO quarterly_revenue (company, year, quarter, segment, revenue_usd_billions) VALUES (?, ?, ?, ?, ?)",
    data
)

conn.commit()
conn.close()
print(f"Database created: {len(data)} rows inserted into data/financial.db")