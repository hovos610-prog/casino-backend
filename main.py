from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import random

app = FastAPI()

# Տվյալների բազայի ստեղծում
def init_db():
    conn = sqlite3.connect("telegram_casino.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 1000.0
        )
    """)
    conn.commit()
    conn.close()

init_db()

class AuthModel(BaseModel):
    telegram_id: int
    username: str

class SpinModel(BaseModel):
    telegram_id: int
    bet: float

@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    return """
    <!DOCTYPE html>
    <html lang="hy">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Telegram Casino</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <style>
            body {
                background-color: #0f0c1b;
                color: #ffffff;
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
                margin: 0;
            }
            .container {
                max-width: 400px;
                margin: auto;
                background: #1a1528;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }
            .balance-box {
                font-size: 22px;
                margin-bottom: 20px;
                color: #ffd700;
            }
            .slot-machine {
                font-size: 40px;
                background: #2b2342;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                letter-spacing: 15px;
            }
            .btn {
                background: #ffb700;
                color: #000;
                border: none;
                padding: 12px 25px;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                cursor: pointer;
                width: 100%;
            }
            .btn:active {
                transform: scale(0.98);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎰 Telegram Casino</h2>
            <div class="balance-box">Բալանս: <span id="balance">1000</span> 🪙</div>
            <div class="slot-machine" id="slots">🍒 🍋 🔔</div>
            <button class="btn" onclick="spin()">ՊՏՏԵԼ (ԽԱՂԱԼ)</button>
        </div>

        <script>
            const tg = window.Telegram.WebApp;
            tg.expand();

            // Օգտատիրոջ տվյալները (եթե բացված է Telegram-ից, վերցնում ենք իրական ID-ն, թե չէ՝ թեստային)
            const user = tg.initDataUnsafe?.user || { id: 12345678, username: "TestUser" };

            let currentBalance = 1000;

            // Մուտք/Գրանցում բեքենդում
            fetch('/api/auth', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ telegram_id: user.id, username: user.username || "Player" })
            })
            .then(res => res.json())
            .then(data => {
                currentBalance = data.balance;
                document.getElementById('balance').innerText = currentBalance;
            });

            function spin() {
                const betAmount = 50; // Ֆիքսված խաղադրույք
                if (currentBalance < betAmount) {
                    alert("Բավարար միավորներ չկան!");
                    return;
                }

                fetch('/api/spin', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ telegram_id: user.id, bet: betAmount })
                })
                .then(res => res.json())
                .then(data => {
                    currentBalance = data.balance;
                    document.getElementById('balance').innerText = currentBalance;

                    if (data.result === 'win') {
                        document.getElementById('slots').innerText = '💎 💎 💎';
                        alert("Շնորհավորում ենք, դուք շահեցիք " + data.win_amount + " միավոր!");
                    } else {
                        document.getElementById('slots').innerText = '❌ 🍒 🍋';
                    }
                });
            }
        </script>
    </body>
    </html>
    """

@app.post("/api/auth")
def authenticate_user(data: AuthModel):
    conn = sqlite3.connect("telegram_casino.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (data.telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute("INSERT INTO users (telegram_id, username, balance) VALUES (?, ?, ?)", 
                       (data.telegram_id, data.username, 1000.0))
        conn.commit()
        balance = 1000.0
    else:
        balance = user[0]
        
    conn.close()
    return {"status": "ok", "balance": balance}

@app.post("/api/spin")
def play_slot(data: SpinModel):
    conn = sqlite3.connect("telegram_casino.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT balance FROM users WHERE telegram_id = ?", (data.telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    current_balance = user[0]
    
    if current_balance < data.bet:
        conn.close()
        raise HTTPException(status_code=400, detail="Insufficient balance")
        
    won = random.choice([True, False, False]) # 33% շահելու շանս
    
    if won:
        win_amount = data.bet * 2
        new_balance = current_balance - data.bet + win_amount
        result = "win"
    else:
        win_amount = 0
        new_balance = current_balance - data.bet
        result = "lose"
        
    cursor.execute("UPDATE users SET balance = ? WHERE telegram_id = ?", (new_balance, data.telegram_id))
    conn.commit()
    conn.close()
    
    return {"result": result, "win_amount": win_amount, "balance": new_balance}
    
