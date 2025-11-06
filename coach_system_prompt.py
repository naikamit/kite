"""
Self-Improving Trading Psychology Coach System Prompt

This module implements a dynamic, self-evolving system prompt architecture for
providing personalized trading psychology coaching. The prompt adapts based on
the user's journey stage, behavioral patterns, and feedback effectiveness.

Usage:
    from coach_system_prompt import SelfImprovingCoach

    coach = SelfImprovingCoach(db_client)
    system_prompt = coach.build_prompt(user_id="trader123")

    # Use with OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "I just took a loss..."}
        ]
    )
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


# ═══════════════════════════════════════════════════════════════════════════
# BASE SYSTEM PROMPT (IMMUTABLE CORE)
# ═══════════════════════════════════════════════════════════════════════════

BASE_SYSTEM_PROMPT = """You are a trading psychology coach with a direct, personal communication style.

CORE IDENTITY:
- You analyze patterns in trading behavior, not markets
- You remember everything the user tells you
- You call out self-deception and rationalization
- You celebrate genuine progress, not activity
- You use the user's own data as your primary evidence

COMMUNICATION STYLE:
- Write like you're texting a friend who knows you well
- Use short sentences, direct questions, occasional humor
- Mirror the user's energy level
- Never be preachy or formulaic
- Ask uncomfortable questions when needed

YOUR APPROACH:
1. Pattern Recognition: "I noticed you only journal wins. What about the 3 losses?"
2. Emotional Honesty: "FOMO is in your top 3 emotions. Let's talk about that."
3. Self-Confrontation: "You said 'I'll never revenge trade again' 4 times now."
4. Genuine Celebration: "14 day streak. That's real discipline."
5. Data-Driven: "Your win rate drops 30% when you log 'rushed' as an emotion."

WHAT YOU DON'T DO:
- Don't give market predictions or trade ideas
- Don't repeat generic trading wisdom
- Don't let them off easy with excuses
- Don't praise effort without examining results
- Don't ignore red flags in their patterns

REMEMBER: You're not here to make them feel good. You're here to make them trade better."""


# ═══════════════════════════════════════════════════════════════════════════
# JOURNEY STAGES (ADAPTIVE COACHING APPROACH)
# ═══════════════════════════════════════════════════════════════════════════

JOURNEY_STAGES = {
    "ACTIVATION": {
        "criteria": {"logs_count": (0, 3)},
        "tone": "Friendly guide",
        "focus": "Building the habit loop",
        "prompt_addition": """
CURRENT STAGE: ACTIVATION (Getting Started)

Your goal right now is to make logging feel natural, not forced.

APPROACH:
- Keep feedback short and encouraging
- Celebrate the act of logging, not just the trade outcome
- Ask simple questions: "How did that trade feel?" "What surprised you?"
- Point out what they're doing right: "Good detail on the emotion"
- Make it conversational, not clinical

AVOID:
- Heavy analysis (they don't have enough data yet)
- Comparing them to others
- Complex trading psychology concepts
- Overwhelming them with insights

SAMPLE RESPONSE STYLE:
"Nice work logging this. Quick question - you marked 'confident' but took a loss.
Was that confidence based on your setup or something else? Just curious."
"""
    },

    "EARLY_HABIT_FORMATION": {
        "criteria": {"logs_count": (3, 20)},
        "tone": "Encouraging but challenging",
        "focus": "Identifying first patterns",
        "prompt_addition": """
CURRENT STAGE: EARLY HABIT FORMATION (Building Consistency)

The user is building momentum. Now you start connecting dots.

APPROACH:
- Point out emerging patterns: "3 out of 4 losses had 'rushed' in emotions"
- Ask probing questions: "Why do you think you're more patient with longs than shorts?"
- Introduce light challenges: "Try logging immediately after the trade, not EOD"
- Celebrate consistency: "5 days in a row. That's the habit forming."
- Start gentle accountability: "You said you'd wait for your setup. Did you?"

PATTERNS TO WATCH FOR:
- Emotion-outcome correlations
- Time-of-day patterns
- Win streak behavior changes
- Loss response patterns
- Discrepancies between stated strategy and actual execution

SAMPLE RESPONSE STYLE:
"I'm seeing something. Your last 3 losses all happened after 2pm. And you logged
'tired' in 2 of them. Think there's a connection? What if you set a hard stop
trading time at 1:30pm for a week and see what happens?"
"""
    },

    "INSIGHT_ACCUMULATION": {
        "criteria": {"logs_count": (20, 50)},
        "tone": "Trusted advisor",
        "focus": "Deep pattern recognition and intervention",
        "prompt_addition": """
CURRENT STAGE: INSIGHT ACCUMULATION (Pattern Recognition)

They have enough data for real analysis. Time to get direct.

APPROACH:
- Present hard truths backed by their data
- Call out self-deception: "You keep saying 'I followed my plan' but your R:R is under 2"
- Offer specific interventions: "Your win rate is 65% when you wait 5min before entry"
- Challenge rationalizations: "Is that really why you exited early, or were you scared?"
- Dig into blind spots: "You never log when you break rules. Why?"

KEY INSIGHTS TO SURFACE:
- Emotional triggers that predict losses
- Rule violations they're blind to
- Winning patterns they don't recognize
- The gap between their self-image and their data
- Hidden beliefs driving behavior

INTERVENTION EXAMPLES:
- "You're overtrading after wins. That's classic dopamine seeking."
- "Your 'intuition' has a 40% win rate. Your plan has 70%. Choose."
- "You only journal on green days. The red days are where the gold is."

SAMPLE RESPONSE STYLE:
"Let's be real - you've logged 'FOMO' in 9 trades. All 9 were losses. Every. Single. One.
Your brain is giving you a giant red flag and you're ignoring it. What needs to
happen for you to actually pause when you feel FOMO?"
"""
    },

    "MASTERY": {
        "criteria": {"logs_count": (50, None)},
        "tone": "Performance coach",
        "focus": "Optimization and advanced self-awareness",
        "prompt_addition": """
CURRENT STAGE: MASTERY (Performance Optimization)

They're consistent. Now it's about edges and blind spots.

APPROACH:
- Focus on marginal gains: "Your best setups have 75% win rate. Why aren't you waiting for only those?"
- Explore psychological edges: "You're calmer in losses than wins. That's rare. How can you use that?"
- Challenge comfort zones: "You've been profitable for 6 weeks. Now what?"
- Introduce advanced concepts: Risk of ruin, position sizing psychology, scaling strategies
- Meta-awareness: "You're aware of your FOMO. But are you aware of what triggers the trigger?"

ADVANCED PATTERNS:
- Second-order emotions (fear of being fearful, guilt about greed)
- Unconscious sabotage patterns
- Identity conflicts ("I'm not the kind of person who...")
- Peak performance states and how to access them
- Psychological risk of success (fear of losing gains)

SAMPLE RESPONSE STYLE:
"You've crushed it lately. 12% this month. But I'm curious - you're taking smaller
size now than when you were less profitable. What's that about? Are you afraid of
success? Or protecting what you've built? There's a difference."
"""
    },

    "PLATEAU": {
        "criteria": {"stagnant_metrics": True},
        "tone": "Tough love interventionist",
        "focus": "Breaking through resistance",
        "prompt_addition": """
CURRENT STAGE: PLATEAU (Stuck)

Performance has flatlined. Time for intervention.

APPROACH:
- Direct confrontation: "You've been break-even for 3 weeks. What changed?"
- Question the story: "You keep saying 'market conditions' but your setup win rate hasn't changed"
- Identify the real blocker: "Is this about trading or something else in your life?"
- Challenge autopilot behavior: "When did logging become a checkbox instead of reflection?"
- Offer hard resets: "What if you took a week off and came back fresh?"

ROOT CAUSES TO EXPLORE:
- Boredom with the process
- Fear of the next level
- Life stress bleeding into trading
- Loss of purpose/motivation
- Burnout from over-monitoring
- Unconscious self-sabotage

SAMPLE RESPONSE STYLE:
"Real talk - you're going through the motions. Your logs used to have detail and
reflection. Now they're just boxes checked. Something shifted. What is it? And
don't say 'nothing' because your equity curve says otherwise."
"""
    },

    "RELAPSE": {
        "criteria": {"streak_broken": True, "missed_logs": True},
        "tone": "Concerned friend",
        "focus": "Rebuilding without shame",
        "prompt_addition": """
CURRENT STAGE: RELAPSE (Rebuilding)

They fell off. No judgment - it happens. Focus on the comeback.

APPROACH:
- Acknowledge without dwelling: "You went quiet for 2 weeks. Welcome back."
- Remove shame: "Streaks break. What matters is what you do next."
- Understand what happened: "What made it hard to log? Busy? Or something else?"
- Start small: "Don't try to do everything at once. Just log today's trade."
- Reconnect to purpose: "Why did you start this in the first place?"

AVOID:
- Guilt trips ("You were doing so well...")
- Minimizing ("It's no big deal")
- Over-analysis of the gap period
- Pressure to get back to where they were immediately

REBUILDING STRATEGY:
- Lower the bar: "Just open the app. Don't even log yet."
- Celebrate returns: "You came back. That's what matters."
- Short-term focus: "Let's just get through this week."
- Find the hook: "What's one thing you missed about logging?"

SAMPLE RESPONSE STYLE:
"Hey. I noticed you went dark. No lecture - I'm just glad you're back. What made
you log again today? Start there. One day at a time."
"""
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# META-LEARNING (WHAT'S WORKING?)
# ═══════════════════════════════════════════════════════════════════════════

FEEDBACK_TYPES = {
    "CONFRONTATIONAL": "Direct challenge to behavior",
    "SUPPORTIVE": "Encouragement and validation",
    "ANALYTICAL": "Data-driven pattern observation",
    "QUESTIONING": "Probing questions for self-reflection",
    "HUMOROUS": "Light humor to ease tension",
    "PREDICTIVE": "Forecasting likely outcomes based on patterns"
}


# ═══════════════════════════════════════════════════════════════════════════
# COACH MEMORY CLASS (Long-term conversational memory)
# ═══════════════════════════════════════════════════════════════════════════

class CoachMemory:
    """
    Manages long-term conversational memory for the coaching system.

    This class:
    - Extracts important insights from conversations using LLM
    - Stores memories with importance scores and tags
    - Retrieves relevant memories based on context
    - Tracks which memories are most useful

    Think of this as the coach's notebook where they write down everything
    important the user tells them, then reference it later.
    """

    def __init__(self, db_client):
        """
        Initialize memory manager with database access.

        Args:
            db_client: Database client with coach_memory methods
        """
        self.db = db_client

    def extract_and_save_insights(self, user_id: str, user_message: str,
                                  use_llm: bool = True) -> Optional[int]:
        """
        Extract important information from user message and save as memory.

        This is the "second LLM call" that analyzes the conversation to decide
        what's worth remembering long-term.

        Args:
            user_id: User identifier
            user_message: The user's message
            use_llm: Whether to use LLM for extraction (if False, uses keyword matching)

        Returns:
            Memory ID if saved, None otherwise
        """

        if not use_llm:
            # Simple keyword-based extraction (no LLM needed)
            return self._extract_with_keywords(user_id, user_message)

        # TODO: Implement LLM-based extraction when API is integrated
        # For now, use keyword matching
        return self._extract_with_keywords(user_id, user_message)

    def _extract_with_keywords(self, user_id: str, user_message: str) -> Optional[int]:
        """Extract memories using keyword patterns (no LLM needed)."""

        message_lower = user_message.lower()

        # Pattern matching for different memory types
        memory_data = None

        # GOALS: "I want to", "My goal is", "I'm trying to"
        if any(phrase in message_lower for phrase in ["i want to", "my goal", "i'm trying to", "hoping to"]):
            memory_data = {
                "memory_type": "goal",
                "content": user_message,
                "importance": 8,
                "tags": json.dumps(["goal", "intention"]),
                "emotional_weight": "positive"
            }

        # FEARS: "I'm scared", "I'm afraid", "I lost", "trauma"
        elif any(phrase in message_lower for phrase in ["scared", "afraid", "fear", "lost big", "trauma", "burned"]):
            memory_data = {
                "memory_type": "fear",
                "content": user_message,
                "importance": 9,
                "tags": json.dumps(["fear", "past_experience"]),
                "emotional_weight": "negative"
            }

        # RULES: "I won't", "never again", "I promise", "rule"
        elif any(phrase in message_lower for phrase in ["i won't", "never again", "i promise", "my rule", "i'll never"]):
            memory_data = {
                "memory_type": "rule",
                "content": user_message,
                "importance": 8,
                "tags": json.dumps(["rule", "commitment"]),
                "emotional_weight": "neutral"
            }

        # CONTEXT: "I have", "my schedule", "I can only", "I work"
        elif any(phrase in message_lower for phrase in ["i have a", "my schedule", "i can only", "i work", "family", "day job"]):
            memory_data = {
                "memory_type": "context",
                "content": user_message,
                "importance": 7,
                "tags": json.dumps(["context", "constraints"]),
                "emotional_weight": "neutral"
            }

        # INSIGHTS: "I noticed", "I realize", "pattern", "always"
        elif any(phrase in message_lower for phrase in ["i noticed", "i realize", "pattern", "i always", "tends to"]):
            memory_data = {
                "memory_type": "insight",
                "content": user_message,
                "importance": 7,
                "tags": json.dumps(["insight", "self_awareness"]),
                "emotional_weight": "neutral"
            }

        # Save if we found something important
        if memory_data and memory_data["importance"] >= 6:
            memory_id = self.db.save_memory(
                user_id=user_id,
                memory_type=memory_data["memory_type"],
                content=memory_data["content"],
                importance=memory_data["importance"],
                tags=memory_data["tags"],
                emotional_weight=memory_data["emotional_weight"]
            )

            if memory_id:
                print(f"💾 Saved {memory_data['memory_type']} memory (ID: {memory_id})")
                return memory_id

        return None

    def get_relevant_memories(self, user_id: str, current_message: str,
                             limit: int = 5) -> List[Dict]:
        """
        Retrieve memories relevant to the current conversation.

        Uses simple keyword matching to find related memories.

        Args:
            user_id: User identifier
            current_message: Current user message for context
            limit: Maximum memories to return

        Returns:
            List of memory dictionaries
        """

        # Extract keywords from current message
        keywords = self._extract_keywords(current_message)

        # Get memories matching keywords
        memories = self.db.get_relevant_memories(
            user_id=user_id,
            keywords=keywords,
            limit=limit
        )

        # Update reference tracking
        for memory in memories:
            self.db.update_memory_reference(memory['id'])

        return memories

    def _extract_keywords(self, message: str) -> List[str]:
        """Extract important keywords from message for memory search."""

        message_lower = message.lower()

        # Trading-specific keywords to look for
        keyword_map = {
            "position": ["position", "size", "scaling"],
            "loss": ["loss", "losing", "lost", "down"],
            "fear": ["fear", "scared", "afraid", "anxiety"],
            "fomo": ["fomo", "missing out", "chase"],
            "revenge": ["revenge", "make it back", "get even"],
            "discipline": ["discipline", "rules", "plan", "strategy"],
            "emotion": ["emotion", "feeling", "felt"],
            "time": ["time", "morning", "afternoon", "schedule"],
            "consistency": ["consistent", "streak", "daily", "routine"]
        }

        found_keywords = []

        for key, variations in keyword_map.items():
            if any(variation in message_lower for variation in variations):
                found_keywords.append(key)

        return found_keywords[:5]  # Limit to 5 keywords

    def format_memories_for_prompt(self, memories: List[Dict]) -> str:
        """
        Format retrieved memories for inclusion in system prompt.

        Args:
            memories: List of memory dictionaries

        Returns:
            Formatted string for prompt injection
        """

        if not memories:
            return ""

        # Group by type
        sections = {
            "goal": [],
            "fear": [],
            "rule": [],
            "context": [],
            "insight": []
        }

        for mem in memories:
            mem_type = mem.get('memory_type', 'insight')
            if mem_type in sections:
                sections[mem_type].append(mem['content'])

        # Build formatted output
        formatted = "\n\n" + "=" * 80
        formatted += "\nLONG-TERM MEMORY (Reference these in your responses):\n"
        formatted += "=" * 80 + "\n"

        if sections["goal"]:
            formatted += "\n🎯 THEIR GOALS:\n"
            for goal in sections["goal"]:
                formatted += f"  • {goal}\n"

        if sections["fear"]:
            formatted += "\n⚠️ FEARS & BLOCKS:\n"
            for fear in sections["fear"]:
                formatted += f"  • {fear}\n"

        if sections["rule"]:
            formatted += "\n📋 RULES THEY SET:\n"
            for rule in sections["rule"]:
                formatted += f"  • {rule}\n"

        if sections["context"]:
            formatted += "\n📌 IMPORTANT CONTEXT:\n"
            for context in sections["context"]:
                formatted += f"  • {context}\n"

        if sections["insight"]:
            formatted += "\n💡 THEIR INSIGHTS:\n"
            for insight in sections["insight"]:
                formatted += f"  • {insight}\n"

        formatted += "=" * 80 + "\n"

        return formatted

    def get_memory_stats(self, user_id: str) -> Dict:
        """Get statistics about stored memories."""

        memories = self.db.get_memories_by_user(user_id)

        if not memories:
            return {"total": 0}

        stats = {
            "total": len(memories),
            "by_type": {},
            "avg_importance": 0,
            "most_referenced": None
        }

        # Count by type
        for memory in memories:
            mem_type = memory.get('memory_type', 'unknown')
            stats["by_type"][mem_type] = stats["by_type"].get(mem_type, 0) + 1

        # Average importance
        importances = [m.get('importance', 5) for m in memories]
        stats["avg_importance"] = sum(importances) / len(importances)

        # Most referenced
        sorted_by_refs = sorted(memories,
                               key=lambda x: x.get('times_referenced', 0),
                               reverse=True)
        if sorted_by_refs:
            stats["most_referenced"] = sorted_by_refs[0].get('content', '')[:100]

        return stats


# ═══════════════════════════════════════════════════════════════════════════
# SELF-IMPROVING COACH CLASS
# ═══════════════════════════════════════════════════════════════════════════

class SelfImprovingCoach:
    """
    Builds dynamic, personalized system prompts that evolve over time.

    The prompt adapts based on:
    1. User's journey stage (activation → mastery)
    2. Behavioral patterns in their trading data
    3. Which feedback types have been most effective
    4. Recent engagement levels
    """

    def __init__(self, db_client):
        """
        Initialize the coach with database access.

        Args:
            db_client: Database client with access to trade_logs, orders, etc.
        """
        self.db = db_client

    def get_journey_stage(self, user_id: str) -> str:
        """
        Determine which journey stage the user is in.

        Args:
            user_id: User identifier

        Returns:
            Journey stage key (e.g., "ACTIVATION", "MASTERY")
        """
        # Get user stats
        logs = self.db.get_trade_logs(user_id)
        logs_count = len(logs)

        # Check for relapse (missed logs after being consistent)
        recent_logs = [log for log in logs if self._is_recent(log['created_at'], days=14)]
        if logs_count > 10 and len(recent_logs) < 3:
            return "RELAPSE"

        # Check for plateau (stagnant win rate over last 20 trades)
        if logs_count >= 30:
            recent_20 = logs[-20:]
            if self._is_stagnant(recent_20):
                return "PLATEAU"

        # Journey stage based on log count
        if logs_count < 3:
            return "ACTIVATION"
        elif logs_count < 20:
            return "EARLY_HABIT_FORMATION"
        elif logs_count < 50:
            return "INSIGHT_ACCUMULATION"
        else:
            return "MASTERY"

    def build_dynamic_context(self, user_id: str) -> str:
        """
        Build personalized context based on user's trading patterns.

        Args:
            user_id: User identifier

        Returns:
            Formatted context string with user-specific insights
        """
        logs = self.db.get_trade_logs(user_id)

        if not logs:
            return "\nUSER CONTEXT: No trading history yet."

        context_parts = ["\nUSER CONTEXT (Use this data in your responses):"]

        # Basic stats
        total_logs = len(logs)
        wins = sum(1 for log in logs if log.get('pnl', 0) > 0)
        losses = sum(1 for log in logs if log.get('pnl', 0) < 0)
        win_rate = (wins / total_logs * 100) if total_logs > 0 else 0

        context_parts.append(f"- Total trades logged: {total_logs}")
        context_parts.append(f"- Win rate: {win_rate:.1f}% ({wins}W / {losses}L)")

        # Emotion patterns
        emotion_stats = self._analyze_emotions(logs)
        if emotion_stats:
            context_parts.append(f"- Most common emotions: {', '.join(emotion_stats[:3])}")

            # Emotion-outcome correlations
            emotion_correlations = self._emotion_outcome_correlation(logs)
            if emotion_correlations:
                context_parts.append("- Emotion patterns:")
                for emotion, correlation in emotion_correlations.items():
                    context_parts.append(f"  • {emotion}: {correlation}")

        # Risk:Reward patterns
        avg_rr = self._average_risk_reward(logs)
        if avg_rr:
            context_parts.append(f"- Average R:R: 1:{avg_rr:.2f}")

        # Consistency
        streak = self._current_streak(logs)
        if streak > 1:
            context_parts.append(f"- Current logging streak: {streak} days")

        # Recent behavior changes
        if total_logs >= 10:
            changes = self._detect_behavior_changes(logs)
            if changes:
                context_parts.append("- Recent changes detected:")
                for change in changes:
                    context_parts.append(f"  • {change}")

        return "\n".join(context_parts)

    def get_meta_learning_context(self, user_id: str) -> str:
        """
        Build context about what feedback types work best for this user.

        Args:
            user_id: User identifier

        Returns:
            Meta-learning context string
        """
        # This would track feedback effectiveness over time
        # For now, return a placeholder that can be implemented
        return """
META-LEARNING CONTEXT (Adapt your style based on what works):
- Track which feedback types lead to behavior change
- Note: This feature tracks effectiveness over time as you interact
- High engagement indicators: User asks follow-up questions, implements suggestions
- Low engagement indicators: Short responses, defensive language, stops logging
"""

    def build_prompt(self, user_id: str) -> str:
        """
        Build the complete self-improving system prompt.

        Args:
            user_id: User identifier

        Returns:
            Complete system prompt string
        """
        # Get journey stage
        stage = self.get_journey_stage(user_id)
        stage_config = JOURNEY_STAGES[stage]

        # Build complete prompt
        prompt_parts = [
            BASE_SYSTEM_PROMPT,
            "\n" + "═" * 80 + "\n",
            stage_config["prompt_addition"],
            "\n" + "═" * 80 + "\n",
            self.build_dynamic_context(user_id),
            "\n" + "═" * 80 + "\n",
            self.get_meta_learning_context(user_id),
            "\n" + "═" * 80 + "\n",
            self._get_response_guidelines()
        ]

        return "\n".join(prompt_parts)

    def build_prompt_with_memory(self, user_id: str, current_message: str,
                                 memory_manager: CoachMemory) -> str:
        """
        Build system prompt with long-term memory integration.

        This is the FULL SYSTEM that combines:
        1. Base prompt (identity + approach)
        2. Journey stage (where they are)
        3. Trade data context (what their data shows)
        4. Long-term memories (what they've told you)
        5. Meta-learning (what feedback works)

        Args:
            user_id: User identifier
            current_message: Current conversation message for context
            memory_manager: CoachMemory instance for retrieving memories

        Returns:
            Complete system prompt with memory context
        """
        # Get base prompt
        base_prompt = self.build_prompt(user_id)

        # Get relevant memories for this conversation
        relevant_memories = memory_manager.get_relevant_memories(
            user_id=user_id,
            current_message=current_message,
            limit=5
        )

        # Format memories for prompt
        memory_context = memory_manager.format_memories_for_prompt(relevant_memories)

        # Insert memory context before response guidelines
        if memory_context:
            # Split at response guidelines and insert memory
            parts = base_prompt.split("RESPONSE GUIDELINES:")
            if len(parts) == 2:
                return parts[0] + memory_context + "\n\nRESPONSE GUIDELINES:" + parts[1]

        return base_prompt

    def _get_response_guidelines(self) -> str:
        """Get guidelines for response format."""
        return """
RESPONSE GUIDELINES:
- Keep responses under 150 words unless deep analysis is needed
- Ask 1-2 specific questions to drive self-reflection
- Reference their specific data when making points
- Use their language and emotion words back to them
- End with a clear next action or thought to consider
- Be conversational, not robotic

RESPONSE FORMAT:
[1-2 sentences acknowledging their message]
[Insight or pattern observation]
[Question or challenge]
[Optional: Specific next action]
"""

    # ═══════════════════════════════════════════════════════════════════════
    # HELPER METHODS FOR ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════

    def _is_recent(self, timestamp: str, days: int = 7) -> bool:
        """Check if timestamp is within recent days."""
        try:
            log_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return (datetime.now() - log_date).days <= days
        except:
            return False

    def _is_stagnant(self, recent_logs: List[Dict]) -> bool:
        """Detect if performance has plateaued."""
        if len(recent_logs) < 20:
            return False

        # Check if win rate variance is low over last 20 trades
        first_half = recent_logs[:10]
        second_half = recent_logs[10:]

        first_wr = sum(1 for log in first_half if log.get('pnl', 0) > 0) / 10
        second_wr = sum(1 for log in second_half if log.get('pnl', 0) > 0) / 10

        # Plateau if win rates are within 10% and both around break-even
        return abs(first_wr - second_wr) < 0.1 and 0.4 < first_wr < 0.6

    def _analyze_emotions(self, logs: List[Dict]) -> List[str]:
        """Get most common emotions from logs."""
        emotion_counts = {}
        for log in logs:
            emotions = log.get('emotions', [])
            if isinstance(emotions, str):
                emotions = json.loads(emotions)
            for emotion in emotions:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1

        # Sort by frequency
        sorted_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)
        return [emotion for emotion, _ in sorted_emotions[:5]]

    def _emotion_outcome_correlation(self, logs: List[Dict]) -> Dict[str, str]:
        """Find correlations between emotions and outcomes."""
        if len(logs) < 10:
            return {}

        emotion_outcomes = {}

        for log in logs:
            emotions = log.get('emotions', [])
            if isinstance(emotions, str):
                emotions = json.loads(emotions)

            pnl = log.get('pnl', 0)
            outcome = 'win' if pnl > 0 else 'loss'

            for emotion in emotions:
                if emotion not in emotion_outcomes:
                    emotion_outcomes[emotion] = {'wins': 0, 'losses': 0}
                emotion_outcomes[emotion][outcome + 's'] += 1

        # Find notable correlations
        correlations = {}
        for emotion, outcomes in emotion_outcomes.items():
            total = outcomes['wins'] + outcomes['losses']
            if total >= 3:  # Need at least 3 instances
                win_rate = outcomes['wins'] / total
                if win_rate >= 0.7:
                    correlations[emotion] = f"Strong positive correlation ({win_rate:.0%} win rate)"
                elif win_rate <= 0.3:
                    correlations[emotion] = f"Strong negative correlation ({win_rate:.0%} win rate)"

        return correlations

    def _average_risk_reward(self, logs: List[Dict]) -> Optional[float]:
        """Calculate average risk:reward ratio."""
        rr_ratios = []
        for log in logs:
            if log.get('risk_reward_ratio'):
                rr_ratios.append(float(log['risk_reward_ratio']))

        return sum(rr_ratios) / len(rr_ratios) if rr_ratios else None

    def _current_streak(self, logs: List[Dict]) -> int:
        """Calculate current consecutive logging streak."""
        if not logs:
            return 0

        # Sort by date
        sorted_logs = sorted(logs, key=lambda x: x.get('created_at', ''), reverse=True)

        streak = 0
        current_date = datetime.now().date()

        for log in sorted_logs:
            try:
                log_date = datetime.fromisoformat(log['created_at'].replace('Z', '+00:00')).date()
                days_diff = (current_date - log_date).days

                if days_diff <= streak:
                    streak += 1
                else:
                    break
            except:
                continue

        return streak

    def _detect_behavior_changes(self, logs: List[Dict]) -> List[str]:
        """Detect significant changes in recent behavior."""
        changes = []

        if len(logs) < 10:
            return changes

        recent = logs[-10:]
        previous = logs[-20:-10] if len(logs) >= 20 else logs[:-10]

        # Compare average R:R
        recent_rr = [log.get('risk_reward_ratio', 0) for log in recent]
        previous_rr = [log.get('risk_reward_ratio', 0) for log in previous]

        if recent_rr and previous_rr:
            recent_avg = sum(recent_rr) / len(recent_rr)
            previous_avg = sum(previous_rr) / len(previous_rr)

            if recent_avg < previous_avg * 0.7:
                changes.append("R:R ratios have decreased significantly")
            elif recent_avg > previous_avg * 1.3:
                changes.append("R:R ratios have improved significantly")

        # Compare logging detail
        recent_notes = [len(log.get('notes', '')) for log in recent]
        previous_notes = [len(log.get('notes', '')) for log in previous]

        if recent_notes and previous_notes:
            recent_avg_length = sum(recent_notes) / len(recent_notes)
            previous_avg_length = sum(previous_notes) / len(previous_notes)

            if recent_avg_length < previous_avg_length * 0.5:
                changes.append("Notes becoming shorter (possible disengagement)")

        return changes


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════

"""
EXAMPLE 1: Basic Usage with OpenAI
-----------------------------------

from coach_system_prompt import SelfImprovingCoach
import openai

# Initialize coach
coach = SelfImprovingCoach(db_client=your_db_client)

# Build personalized prompt
system_prompt = coach.build_prompt(user_id="trader123")

# Use with OpenAI API
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "I just took a big loss and feel terrible..."}
    ],
    temperature=0.7,
    max_tokens=300
)

print(response.choices[0].message.content)


EXAMPLE 2: Integration with FastAPI Endpoint
----------------------------------------------

@app.post("/api/coach")
async def get_coaching(request: Request):
    data = await request.json()
    user_message = data.get("message")
    user_id = data.get("user_id")

    # Build adaptive prompt
    coach = SelfImprovingCoach(kite_client.db)
    system_prompt = coach.build_prompt(user_id)

    # Get coaching response
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )

    coaching_response = response.choices[0].message.content

    # Track feedback effectiveness (meta-learning)
    track_interaction(user_id, user_message, coaching_response)

    return {"response": coaching_response}


EXAMPLE 3: Post-Trade Automatic Journaling
-------------------------------------------

@app.post("/api/trade-log")
async def save_trade_log(request: Request):
    # Save trade log...

    # Generate automatic journal entry
    coach = SelfImprovingCoach(kite_client.db)
    system_prompt = coach.build_prompt(user_id)

    trade_summary = f'''
    Trade: {symbol} {action}
    Entry: ₹{entry_price}, Target: ₹{target}, SL: ₹{stop_loss}
    R:R: 1:{risk_reward}
    Emotions: {emotions}
    Notes: {notes}
    '''

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this trade:\n{trade_summary}"}
        ]
    )

    auto_journal = response.choices[0].message.content

    return {
        "success": True,
        "journal_entry": auto_journal
    }


EXAMPLE 4: Weekly Summary Report
---------------------------------

@app.get("/api/weekly-summary")
async def get_weekly_summary(user_id: str):
    coach = SelfImprovingCoach(kite_client.db)

    # Get last 7 days of trades
    recent_trades = coach.db.get_recent_trade_logs(user_id, days=7)

    # Build context-aware prompt
    system_prompt = coach.build_prompt(user_id)

    # Generate weekly insights
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze my week: {len(recent_trades)} trades logged. What patterns do you see?"}
        ],
        temperature=0.8,
        max_tokens=500
    )

    return {
        "week_summary": response.choices[0].message.content,
        "trades_count": len(recent_trades)
    }


EVOLUTION EXAMPLE: How the prompt changes over time
----------------------------------------------------

Day 1 (ACTIVATION stage):
User: "I just logged my first trade!"
Prompt focus: Celebration, simple questions, habit formation
Response: "Nice! That's step one. Quick question - you marked 'nervous'.
Is that usual for you, or was this trade different somehow?"

Day 15 (EARLY_HABIT_FORMATION):
User: "Another loss today..."
Prompt focus: Pattern detection, light challenges
Response: "I'm noticing something. That's your 3rd loss with 'rushed' in the
emotions. And all 3 happened after 2pm. See the pattern? What if you set a
hard stop time at 1:30pm tomorrow and see how you feel?"

Day 35 (INSIGHT_ACCUMULATION):
User: "I followed my rules this time"
Prompt focus: Calling out discrepancies, using data
Response: "Did you though? Your entry was 2% away from your planned level,
and you logged 'FOMO' as an emotion. That's not following rules, that's
convincing yourself you did. What actually happened?"

Day 75 (MASTERY):
User: "I'm feeling stuck lately"
Prompt focus: Advanced optimization, meta-awareness
Response: "Your win rate is 68% but you're still taking 2:1 R:R trades.
You've proven you can wait for setups. Why aren't you waiting for ONLY
your best setups? What's the real blocker - impatience, boredom, or fear
of missing moves?"
"""


# ═══════════════════════════════════════════════════════════════════════════
# META-LEARNING TRACKER (Optional Enhancement)
# ═══════════════════════════════════════════════════════════════════════════

def track_feedback_effectiveness(
    user_id: str,
    feedback_given: str,
    feedback_type: str,
    user_response_length: int,
    user_implemented_suggestion: bool
):
    """
    Track which feedback types lead to behavior change.

    This function would store data about:
    - What type of feedback was given
    - How the user responded
    - Whether they implemented suggestions
    - Changes in subsequent trading behavior

    Over time, this builds a profile of what coaching style works best
    for each user, allowing the prompt to self-optimize.

    Implementation example:
    - Store in meta_learning table
    - Update weights for feedback_types per user
    - Influence prompt_addition selection in real-time
    """
    # This would be implemented with a database table:
    # CREATE TABLE meta_learning (
    #     id INTEGER PRIMARY KEY,
    #     user_id TEXT,
    #     feedback_type TEXT,
    #     engagement_score REAL,
    #     behavior_change BOOLEAN,
    #     timestamp TEXT
    # )
    pass


# ═══════════════════════════════════════════════════════════════════════════
# EXPORT FOR USE
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    'SelfImprovingCoach',
    'CoachMemory',
    'BASE_SYSTEM_PROMPT',
    'JOURNEY_STAGES',
    'FEEDBACK_TYPES',
    'track_feedback_effectiveness'
]
