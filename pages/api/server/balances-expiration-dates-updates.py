import psycopg2
import schedule
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname='yourdb',
    user='youruser',
    password='yourpassword',
    host='localhost'
)
cursor = conn.cursor()

# --- Mock external API call ---
def fetch_updated_card_data(card_id):
    # Simulate balance changes and expiry updates
    new_balance = round(random.uniform(0, 100), 2)
    new_expiry = datetime.now() + timedelta(days=random.randint(30, 365))
    return new_balance, new_expiry.date()

# --- Update card balances and expirations ---
def sync_gift_cards():
    cursor.execute("SELECT id FROM gift_cards;")
    for (card_id,) in cursor.fetchall():
        new_balance, new_expiry = fetch_updated_card_data(card_id)
        cursor.execute("""
            UPDATE gift_cards
            SET balance = %s, expiry = %s
            WHERE id = %s;
        """, (new_balance, new_expiry, card_id))
        print(f"Synced card {card_id}: balance={new_balance}, expiry={new_expiry}")
    conn.commit()

# --- Spending History Visualization ---
def generate_spending_chart():
    cursor.execute("""
        SELECT date::date, SUM(amount)
        FROM transactions
        GROUP BY date::date
        ORDER BY date::date;
    """)
    rows = cursor.fetchall()
    if not rows:
        print("No transactions yet.")
        return

    dates, amounts = zip(*rows)
    plt.figure(figsize=(8, 4))
    plt.plot(dates, amounts, marker='o')
    plt.title("Daily Spending History")
    plt.xlabel("Date")
    plt.ylabel("Amount Spent")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("spending_history.png")
    print("Spending chart saved as 'spending_history.png'.")

# --- Scheduled Jobs ---
schedule.every(10).seconds.do(sync_gift_cards)
schedule.every().day.at("20:00").do(generate_spending_chart)

print("Gift Card Auto-Sync Service running...")
while True:
    schedule.run_pending()
    time.sleep(1)
