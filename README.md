*Abstract:*
*VouchSys is an intelligent, user-owned platform designed to transform how individuals store, retrieve, and utilize voucher-like information, including gift cards, discount codes, certifications, or personalized credentials — using AI-driven evidence parsing and context-aware statement generation. This research explores the system architecture for real-time retrieval of personalized "vouches" from semi-structured evidence using embedding-based clustering, large language models (LLMs), and user-controlled knowledge repositories. We describe our implementation pipeline and early evaluations based on user interaction simulations, showing promising results for statement relevancy and retrieval efficiency. The paper also highlights practical implications in domains such as job seeking, education, and digital commerce.*

How It Works:
1. Register & Upload:
   Snap a photo, scan, or import your gift cards, loyalty points, or coupons.

   <img width="652" alt="image" src="https://github.com/user-attachments/assets/71d40b2e-6c66-4778-9cc6-7abb789e4855" />

2. Auto-Sync & Update: Balances and expiration dates update automatically. Track spending history with visual insights.
   Auto-sync and update of gift card balances and expiration dates (e.g., from a mock external API).
   ✅ Step 1: Install Required Packages
   
   ```pip install psycopg2 matplotlib schedule```
   
   ✅ Step 2: Database Schema (PostgreSQL)
   
  ` CREATE TABLE gift_cards (
      id UUID PRIMARY KEY,
     name TEXT NOT NULL,
     balance NUMERIC NOT NULL,
     expiry DATE NOT NULL
   );`


   `CREATE TABLE transactions (
        id SERIAL PRIMARY KEY,
        gift_card_id UUID REFERENCES gift_cards(id),
        amount NUMERIC NOT NULL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );`


   Tracking spending history.

   Generating visual insights using matplotlib.

It assumes you're storing gift cards and transactions in PostgreSQL, and will use psycopg2 and matplotlib.

4. Auto-Sync & Update:
   Balances and expiration dates update automatically.
   Track spending history with visual insights.

5. AI-Powered Recommendations: 
   Discover matching deals based on your shopping patterns and favorite stores.

4. Stay Notified: 
   You can get timely alerts by app, email, or SMS before anything expires.

6. Access Anywhere: 
   Use the mobile app or web dashboard to manage and redeem on the go.

6. Save & Enjoy: 
   Maximize your value without changing your habits.

