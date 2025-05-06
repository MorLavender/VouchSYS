// pages/api/add-gift-card.ts

import type { NextApiRequest, NextApiResponse } from 'next'

type GiftCard = {
  id: string;
  name: string;
  balance: number;
  expiry: string;
};

let giftCards: GiftCard[] = []; // In-memory store for demo

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { id, name, balance, expiry } = req.body;

    if (!id || !name || balance === undefined || !expiry) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const newCard: GiftCard = { id, name, balance, expiry };
    giftCards.push(newCard);

    return res.status(200).json({ message: 'Gift card added', card: newCard });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
