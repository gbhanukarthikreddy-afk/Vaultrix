
# Vaultrix Full Bot

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:

```env
TOKEN=YOUR_BOT_TOKEN_HERE
```

Run:

```bash
python main.py
```

## Commands

Economy:
- v!balance / v!bal
- v!daily
- v!work
- v!deposit <amount>
- v!withdraw <amount>
- v!give @user <amount>
- v!history
- v!leaderboard / v!lb

Profile:
- v!profile
- v!stats
- v!shop
- v!buy <item_id>
- v!petshop
- v!buypet <pet_id>

Casino:
- v!casino
- v!coinflip <amount>
- v!dice <amount>
- v!slots <amount>
- v!roulette <amount> <red/black>
- v!blackjack <amount>
- v!crash <amount> <cashout_multiplier>
- v!mines <amount>
- v!duel @user <amount>
- v!case

Admin:
- v!resetbalance @user
- v!addcoins @user <amount>
