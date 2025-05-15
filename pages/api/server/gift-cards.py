from datetime import datetime, timedelta
import random
from db import get_connection

def fetch_updated_card_data(card_id):
    new_balance = round(random.uniform(0, 100), 2)
    new_expiry = datetime.now() + timedelta(days=random.randint(30, 365))
    return new_balance, new_expiry.date()

def sync_gift_cards():
    conn = get_connection()
    if not conn:
        return
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM gift_cards;")
            for (card_id,) in cursor.fetchall():
                new_balance, new_expiry = fetch_updated_card_data(card_id)
                cursor.execute("""
                    UPDATE gift_cards
                    SET balance = %s, expiry = %s
                    WHERE id = %s;
                """, (new_balance, new_expiry, card_id))
                print(f"Synced card {card_id}: balance={new_balance}, expiry={new_expiry}")

def get_total_balance():
    conn = get_connection()
    if not conn:
        return
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT SUM(balance) FROM gift_cards;")
            total = cursor.fetchone()[0] or 0
            print(f"Total gift card value: ${total:.2f}")
