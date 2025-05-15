import schedule
import time
from gift_cards import sync_gift_cards, get_total_balance
from reports import generate_spending_chart, send_weekly_summary

schedule.every(10).seconds.do(sync_gift_cards)
schedule.every().hour.do(get_total_balance)
schedule.every().day.at("20:00").do(generate_spending_chart)
schedule.every().sunday.at("08:00").do(send_weekly_summary)

print("Gift Card Tracker running...")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Service stopped.")
