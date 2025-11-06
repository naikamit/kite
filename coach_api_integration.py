"""
Coach API Integration Example

This file shows how to integrate the self-improving coach system with memory layer
into your FastAPI application.

IMPORTANT: This is an EXAMPLE file showing the integration pattern.
To actually use this, you'll need to:
1. Run database_migrations.py to create memory tables
2. Get an OpenAI or Anthropic API key
3. Install: pip install openai
4. Add these endpoints to your main.py

"""

from fastapi import Request
from datetime import datetime
import json

# These imports would be in your main.py
# from coach_system_prompt import SelfImprovingCoach, CoachMemory
# import openai

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Add to your environment variables or config
OPENAI_API_KEY = "sk-..."  # Get from https://platform.openai.com/api-keys
OPENAI_MODEL = "gpt-4"  # or "gpt-3.5-turbo" for cheaper option

# Alternative: Use Anthropic Claude
# ANTHROPIC_API_KEY = "sk-ant-..."
# ANTHROPIC_MODEL = "claude-3-sonnet-20240229"


# ═══════════════════════════════════════════════════════════════════════════
# COACHING ENDPOINT (Main conversation interface)
# ═══════════════════════════════════════════════════════════════════════════

"""
Add this to main.py:

@app.post("/api/coach")
async def ask_coach(request: Request):
    '''
    Main coaching endpoint - handles user questions and provides personalized feedback.

    Request body:
    {
        "message": "I'm feeling scared to scale up my position size",
        "user_id": "default_user",
        "session_id": "session_123"  # optional
    }

    Response:
    {
        "response": "Remember you told me about losing 50k in 2020?...",
        "conversation_id": 123,
        "memories_used": [1, 5, 8]
    }
    '''
    try:
        data = await request.json()
        user_message = data.get("message")
        user_id = data.get("user_id", "default_user")
        session_id = data.get("session_id")

        print(f"💬 Coach request from {user_id}: {user_message[:50]}...")

        # === STEP 1: Initialize coach and memory ===
        coach = SelfImprovingCoach(kite_client.db)
        memory = CoachMemory(kite_client.db)

        # === STEP 2: Build personalized prompt WITH memory ===
        system_prompt = coach.build_prompt_with_memory(
            user_id=user_id,
            current_message=user_message,
            memory_manager=memory
        )

        print(f"🎯 Built prompt for journey stage: {coach.get_journey_stage(user_id)}")

        # === STEP 3: Get coaching response from LLM ===
        import openai
        openai.api_key = OPENAI_API_KEY

        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=300
        )

        coaching_response = response.choices[0].message.content
        print(f"✅ Got coaching response ({len(coaching_response)} chars)")

        # === STEP 4: Save conversation history ===
        conversation_id = kite_client.db.save_conversation(
            user_id=user_id,
            user_message=user_message,
            coach_response=coaching_response,
            session_id=session_id
        )

        # === STEP 5: Extract and save any new memories ===
        memory_id = memory.extract_and_save_insights(
            user_id=user_id,
            user_message=user_message,
            use_llm=False  # Set to True when you want LLM-based extraction
        )

        if memory_id:
            print(f"💾 Saved new memory (ID: {memory_id})")

        return {
            "success": True,
            "response": coaching_response,
            "conversation_id": conversation_id
        }

    except Exception as e:
        print(f"❌ Coach endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }
"""


# ═══════════════════════════════════════════════════════════════════════════
# POST-TRADE AUTOMATIC JOURNALING
# ═══════════════════════════════════════════════════════════════════════════

"""
Add to your existing /api/trade-log endpoint in main.py:

@app.post("/api/trade-log")
async def save_trade_log(request: Request):
    '''Save trade log and generate automatic journal entry'''
    try:
        data = await request.json()

        # ... existing trade log saving code ...

        # === NEW: Generate automatic journal entry ===
        if log_id:  # After successfully saving trade log

            # Build trade summary
            trade_summary = f'''
            Trade: {order['symbol']} {order['action']}
            Entry: ₹{order['entry_price']}, Target: ₹{target_price}, SL: ₹{stop_loss}
            R:R: 1:{risk_reward_ratio}
            Quantity: {order['quantity']}
            Emotions: {', '.join(emotions)}
            Strategy: {strategy}
            Notes: {notes}
            '''

            # Get coaching analysis
            coach = SelfImprovingCoach(kite_client.db)
            memory = CoachMemory(kite_client.db)

            system_prompt = coach.build_prompt_with_memory(
                user_id="default_user",
                current_message=trade_summary,
                memory_manager=memory
            )

            import openai
            openai.api_key = OPENAI_API_KEY

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this trade I just logged:\\n{trade_summary}"}
                ],
                temperature=0.7,
                max_tokens=200
            )

            journal_entry = response.choices[0].message.content

            print(f"📝 Generated journal entry: {journal_entry[:100]}...")

            return {
                "success": True,
                "log_id": log_id,
                "journal_entry": journal_entry  # Send to frontend to display
            }

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
"""


# ═══════════════════════════════════════════════════════════════════════════
# WEEKLY SUMMARY REPORT
# ═══════════════════════════════════════════════════════════════════════════

"""
Add this endpoint to main.py:

@app.get("/api/weekly-summary")
async def get_weekly_summary(user_id: str = "default_user"):
    '''
    Generate AI-powered weekly trading summary.

    Example response:
    {
        "week_summary": "You logged 12 trades this week. Your win rate was 58%...",
        "insights": ["FOMO appeared in 60% of losses", "Best performance in mornings"],
        "recommendations": ["Set hard stop time at 1pm", "Journal immediately after trades"]
    }
    '''
    try:
        coach = SelfImprovingCoach(kite_client.db)
        memory = CoachMemory(kite_client.db)

        # Get last 7 days of trades
        recent_trades = kite_client.db.get_trade_logs(user_id, limit=50)

        # Build context
        system_prompt = coach.build_prompt_with_memory(
            user_id=user_id,
            current_message="weekly summary",
            memory_manager=memory
        )

        # Generate summary
        import openai
        openai.api_key = OPENAI_API_KEY

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze my week. I logged {len(recent_trades)} trades. What patterns do you see? Give me 3 specific insights and 2 actionable recommendations."}
            ],
            temperature=0.8,
            max_tokens=500
        )

        summary = response.choices[0].message.content

        return {
            "success": True,
            "week_summary": summary,
            "trades_count": len(recent_trades)
        }

    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return {"success": False, "error": str(e)}
"""


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

"""
Optional: Add these endpoints for memory management:

@app.get("/api/memories")
async def get_memories(user_id: str = "default_user"):
    '''Get all stored memories for a user'''
    try:
        memories = kite_client.db.get_memories_by_user(user_id)

        return {
            "success": True,
            "memories": [
                {
                    "id": m["id"],
                    "type": m["memory_type"],
                    "content": m["content"],
                    "importance": m["importance"],
                    "times_referenced": m["times_referenced"],
                    "created_at": m["created_at"]
                }
                for m in memories
            ],
            "total": len(memories)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.delete("/api/memories/{memory_id}")
async def delete_memory(memory_id: int):
    '''Archive a memory'''
    try:
        success = kite_client.db.archive_memory(memory_id)
        return {"success": success}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/memory-stats")
async def get_memory_stats(user_id: str = "default_user"):
    '''Get memory statistics'''
    try:
        memory = CoachMemory(kite_client.db)
        stats = memory.get_memory_stats(user_id)

        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
"""


# ═══════════════════════════════════════════════════════════════════════════
# FRONTEND INTEGRATION EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════

"""
Add to static/app.js:

// ═══════════════════════════════════════════════════════════════════════════
// COACHING CHAT INTERFACE
// ═══════════════════════════════════════════════════════════════════════════

async function askCoach(message) {
    const response = await fetch('/api/coach', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            message: message,
            user_id: 'default_user',
            session_id: getCurrentSessionId()
        })
    });

    const data = await response.json();

    if (data.success) {
        displayCoachResponse(data.response);
    }
}

function displayCoachResponse(response) {
    const chatContainer = document.getElementById('coach-chat');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'coach-message';
    messageDiv.innerHTML = `
        <div class="coach-avatar">🧠</div>
        <div class="coach-text">${response}</div>
    `;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════════════════
// WEEKLY SUMMARY
// ═══════════════════════════════════════════════════════════════════════════

async function loadWeeklySummary() {
    const response = await fetch('/api/weekly-summary');
    const data = await response.json();

    if (data.success) {
        document.getElementById('weekly-summary').innerHTML = `
            <h3>Your Week in Review</h3>
            <p>${data.week_summary}</p>
            <small>${data.trades_count} trades logged</small>
        `;
    }
}

// Call on dashboard load
loadWeeklySummary();


// ═══════════════════════════════════════════════════════════════════════════
// AUTO-JOURNAL ON TRADE LOG
// ═══════════════════════════════════════════════════════════════════════════

// Modify your existing trade log submission:
async function submitTradeLog(tradeData) {
    const response = await fetch('/api/trade-log', {
        method: 'POST',
        body: JSON.stringify(tradeData)
    });

    const data = await response.json();

    if (data.success && data.journal_entry) {
        // Show automatic journal entry
        showModal({
            title: 'Coach Analysis',
            content: data.journal_entry,
            actions: [
                {text: 'Got it', action: () => closeModal()},
                {text: 'Chat with coach', action: () => openCoachChat()}
            ]
        });
    }
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# SETUP INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════

SETUP_INSTRUCTIONS = """
🚀 SETUP INSTRUCTIONS
════════════════════════════════════════════════════════════════════════════

STEP 1: Run Database Migration
-------------------------------
python database_migrations.py

This creates the memory layer tables (coach_memory, coach_conversations, feedback_effectiveness).


STEP 2: Install OpenAI Library
-------------------------------
pip install openai


STEP 3: Get API Key
-------------------
Option A - OpenAI (Recommended):
  1. Go to https://platform.openai.com/api-keys
  2. Create new secret key
  3. Copy key (starts with sk-...)

Option B - Anthropic Claude:
  1. Go to https://console.anthropic.com/
  2. Create API key
  3. pip install anthropic


STEP 4: Add API Key to Environment
-----------------------------------
# Add to .env file or export in terminal:
export OPENAI_API_KEY="sk-..."

# Or in your main.py:
import os
openai.api_key = os.getenv("OPENAI_API_KEY")


STEP 5: Add Endpoints to main.py
---------------------------------
Copy the endpoint code from this file into your main.py.

At minimum, add:
- /api/coach endpoint (main coaching interface)

Optional:
- Weekly summary endpoint
- Post-trade journaling in existing /api/trade-log
- Memory management endpoints


STEP 6: Test It!
----------------
1. Start your server: python main.py
2. Open browser console
3. Test coaching:

fetch('/api/coach', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    message: "I'm scared to increase my position size because I lost 50k in 2020",
    user_id: "default_user"
  })
}).then(r => r.json()).then(console.log)

4. Check if memory was saved:
   - Look for "💾 Saved fear memory" in logs
   - Check database: SELECT * FROM coach_memory;


STEP 7: Add Frontend UI (Optional)
-----------------------------------
Add a chat interface to your static/index.html:

<div id="coach-panel" style="position: fixed; bottom: 20px; right: 20px;">
  <button onclick="toggleCoach()">💬 Ask Coach</button>
  <div id="coach-chat" style="display: none;">
    <input id="coach-input" placeholder="Ask me anything...">
    <button onclick="sendToCoach()">Send</button>
    <div id="coach-messages"></div>
  </div>
</div>


════════════════════════════════════════════════════════════════════════════

💡 USAGE TIPS
════════════════════════════════════════════════════════════════════════════

START SIMPLE:
- Begin with just the /api/coach endpoint
- Test with a few conversations
- Check that memories are being saved

COST CONSIDERATIONS:
- GPT-4: ~$0.03 per conversation (300 tokens)
- GPT-3.5-turbo: ~$0.002 per conversation (much cheaper for testing)
- Start with gpt-3.5-turbo, upgrade to gpt-4 when it works

MEMORY EXTRACTION:
- Currently uses keyword matching (no LLM needed)
- Works well for: goals, fears, rules, context
- To use LLM for extraction, set use_llm=True and implement the extraction prompt

META-LEARNING:
- Track which feedback works by saving feedback_effectiveness records
- Over time, the coach learns what style works best for you

════════════════════════════════════════════════════════════════════════════

🎯 WHAT YOU GET
════════════════════════════════════════════════════════════════════════════

✅ Personalized coaching that adapts to your journey stage
✅ Long-term memory of everything you tell it
✅ Pattern recognition from your trade data
✅ Automatic journal entries after trades
✅ Weekly summaries and insights
✅ Direct, honest feedback that calls out BS
✅ Self-improving system that learns what works for you

════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(SETUP_INSTRUCTIONS)
