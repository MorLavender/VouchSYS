import matplotlib.pyplot as plt
from db import get_connection
import smtplib
from email.message import EmailMessage

def generate_spending_chart():
    conn = get_connection()
    if not conn:
        return
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT date::date, SUM(amount)
                FROM transactions
                GROUP BY date::date
                ORDER BY date::date;
            """)
            rows = cursor.fetchall()
            if not rows:
                print("No transactions to chart.")
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
            print("Chart saved as 'spending_history.png'.")

def send_weekly_summary():
    generate_spending_chart()

    msg = EmailMessage()
    msg["Subject"] = "Weekly Gift Card Summary"
    msg["From"] = "your_email@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content("Attached is your weekly gift card spending chart.")

    with open("spending_history.png", "rb") as f:
        msg.add_attachment(f.read(), maintype='image', subtype='png', filename='spending_history.png')

    try:
        with smtplib.SMTP('smtp.example.com', 587) as server:
            server.starttls()
            server.login("your_email@example.com", "yourpassword")
            server.send_message(msg)
            print("Weekly summary sent.")
    except Exception as e:
        print("Failed to send email:", e)
