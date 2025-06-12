import datetime
import requests
from models import Paycheck, Bill

# Your OpenRouter API Key
OPENROUTER_API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gpt-4o-mini"

def allocate_offline(paycheck: Paycheck, bills: list[Bill]):
    today = datetime.date.today()
    upcoming = [b for b in bills if b.due_date >= today]
    bill_total = sum(b.amount for b in upcoming)
    leftover = paycheck.amount - bill_total

    if leftover <= 0:
        return {
            "Bills": paycheck.amount,
            "Savings": 0,
            "Gas": 0,
            "Food": 0,
            "Extra": 0
        }, 0

    savings = round(leftover * 0.4, 2)
    gas     = round(leftover * 0.2, 2)
    food    = round(leftover * 0.2, 2)
    extra   = round(leftover - savings - gas - food, 2)

    return {
        "Bills": bill_total,
        "Savings": savings,
        "Gas": gas,
        "Food": food,
        "Extra": extra
    }, leftover

def ai_plan(paycheck: Paycheck, bills: list[Bill], goals: str = "") -> str:
    key = OPENROUTER_API_KEY.strip()
    if not key:
        return "⚠️ No OpenRouter key provided."

    today = datetime.date.today()
    upcoming = [b for b in bills if b.due_date >= today]
    if not upcoming:
        return "✅ No upcoming bills. You're good to go!"

    bills_section = "\n".join(
        f"- {b.name}: ${b.amount:.2f}, due in {(b.due_date - today).days} day(s)"
        for b in sorted(upcoming, key=lambda x: x.due_date)
    )

    prompt = f"""
You are a smart budgeting assistant. I was paid ${paycheck.amount:.2f} on {paycheck.date}.
Here are my upcoming bills:
{bills_section}

Please:
1. List all upcoming bills with due dates and total them.
2. Subtract the total bills from my paycheck.
3. Allocate the leftover like this:
   - 40% to Savings
   - 20% to Gas
   - 20% to Food
   - The rest to Extra Spending
4. If I include any personal goal (like "I want to take a vacation"), factor that in too.

Respond in clear, bullet point or numbered format.
Goals: {goals if goals else "None"}
"""

    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt.strip()}]
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(API_URL, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        fallback, _ = allocate_offline(paycheck, bills)
        return f"❌ AI call failed: {e}\n\n💡 Offline Fallback Plan:\n{fallback}"
