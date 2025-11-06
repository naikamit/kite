"""
Database migrations for adding coach memory layer

This script adds tables for:
- Long-term conversational memory (coach_memory)
- Conversation history tracking (coach_conversations)
- Feedback effectiveness meta-learning (feedback_effectiveness)

Usage:
    python database_migrations.py
"""

import sqlite3
import os
from datetime import datetime


def add_coach_memory_tables(db_path: str = "kite_data.db"):
    """
    Add memory layer tables to existing database.

    Tables created:
    1. coach_memory: Long-term insights, goals, fears, rules
    2. coach_conversations: Full conversation history
    3. feedback_effectiveness: Meta-learning about what works

    Args:
        db_path: Path to SQLite database file
    """

    if not os.path.exists(db_path):
        print(f"⚠️  Database not found at {db_path}")
        print(f"📁 Creating new database...")

    print(f"🔄 Adding memory layer tables to {db_path}...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # ═══════════════════════════════════════════════════════════════
        # TABLE 1: Coach Memory (Long-term insights)
        # ═══════════════════════════════════════════════════════════════

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coach_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory_type TEXT NOT NULL,  -- 'insight', 'goal', 'fear', 'rule', 'context'
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 5,  -- 1-10 scale
                created_at TEXT NOT NULL,
                last_referenced TEXT,  -- When was this last used in a prompt
                times_referenced INTEGER DEFAULT 0,
                emotional_weight TEXT,  -- 'positive', 'negative', 'neutral'
                tags TEXT,  -- JSON array of tags
                is_active BOOLEAN DEFAULT 1,  -- Can be archived if no longer relevant

                -- Indexes for performance
                CHECK (importance >= 1 AND importance <= 10),
                CHECK (memory_type IN ('insight', 'goal', 'fear', 'rule', 'context'))
            )
        """)

        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coach_memory_user
            ON coach_memory(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coach_memory_type
            ON coach_memory(memory_type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coach_memory_importance
            ON coach_memory(importance DESC)
        """)

        print("✅ Created coach_memory table")

        # ═══════════════════════════════════════════════════════════════
        # TABLE 2: Coach Conversations (Full history)
        # ═══════════════════════════════════════════════════════════════

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS coach_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                coach_response TEXT NOT NULL,
                session_id TEXT,  -- Group related conversations
                created_at TEXT NOT NULL,

                -- Optional: Track which memories were used
                memories_used TEXT,  -- JSON array of memory IDs

                -- Optional: User feedback
                user_rating INTEGER,  -- 1-5 stars
                user_found_helpful BOOLEAN
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coach_conversations_user
            ON coach_conversations(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_coach_conversations_session
            ON coach_conversations(session_id)
        """)

        print("✅ Created coach_conversations table")

        # ═══════════════════════════════════════════════════════════════
        # TABLE 3: Feedback Effectiveness (Meta-learning)
        # ═══════════════════════════════════════════════════════════════

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback_effectiveness (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id INTEGER,  -- Links to coach_conversations
                feedback_type TEXT NOT NULL,  -- 'confrontational', 'supportive', 'analytical', etc.
                user_engagement_score INTEGER,  -- 1-10 based on response length/depth
                behavior_changed BOOLEAN,  -- Did they act on the feedback?
                created_at TEXT NOT NULL,

                -- What was the feedback about?
                topic_tags TEXT,  -- JSON array

                FOREIGN KEY (conversation_id) REFERENCES coach_conversations(id),
                CHECK (user_engagement_score >= 1 AND user_engagement_score <= 10)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_effectiveness_user
            ON feedback_effectiveness(user_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_effectiveness_type
            ON feedback_effectiveness(feedback_type)
        """)

        print("✅ Created feedback_effectiveness table")

        # ═══════════════════════════════════════════════════════════════
        # Commit changes
        # ═══════════════════════════════════════════════════════════════

        conn.commit()

        print("\n🎉 Memory layer tables created successfully!")
        print("\nTables added:")
        print("  1. coach_memory - Long-term insights, goals, fears, rules")
        print("  2. coach_conversations - Full conversation history")
        print("  3. feedback_effectiveness - Meta-learning about what works")

        return True

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


def verify_tables(db_path: str = "kite_data.db"):
    """Verify that all tables were created successfully."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ['coach_memory', 'coach_conversations', 'feedback_effectiveness']

    print("\n🔍 Verifying tables...")
    for table in tables:
        cursor.execute(f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table} exists ({count} rows)")
        else:
            print(f"  ❌ {table} missing")

    conn.close()


def add_sample_memories(db_path: str = "kite_data.db", user_id: str = "default_user"):
    """Add sample memories for testing (optional)."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sample_memories = [
        {
            "memory_type": "fear",
            "content": "User lost 50k in 2020 due to overconfidence. Hesitant to scale position size.",
            "importance": 9,
            "tags": '["position_sizing", "overconfidence", "past_trauma"]',
            "emotional_weight": "negative"
        },
        {
            "memory_type": "goal",
            "content": "Wants to become a consistent, emotionally-disciplined trader within 6 months.",
            "importance": 10,
            "tags": '["consistency", "discipline", "emotional_control"]',
            "emotional_weight": "positive"
        },
        {
            "memory_type": "rule",
            "content": "Committed to never revenge trade. Has broken this rule 3 times.",
            "importance": 8,
            "tags": '["revenge_trading", "rule_violation"]',
            "emotional_weight": "neutral"
        },
        {
            "memory_type": "context",
            "content": "Has day job, can only trade in mornings. Family time after 4pm is non-negotiable.",
            "importance": 7,
            "tags": '["time_constraints", "work_life_balance"]',
            "emotional_weight": "neutral"
        },
        {
            "memory_type": "insight",
            "content": "Performs better on low-volatility days. Gets anxious and overtrades when market moves fast.",
            "importance": 8,
            "tags": '["volatility", "anxiety", "overtrading"]',
            "emotional_weight": "neutral"
        }
    ]

    print("\n📝 Adding sample memories for testing...")

    for memory in sample_memories:
        cursor.execute("""
            INSERT INTO coach_memory
            (user_id, memory_type, content, importance, tags, emotional_weight, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            user_id,
            memory["memory_type"],
            memory["content"],
            memory["importance"],
            memory["tags"],
            memory["emotional_weight"],
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

    print(f"✅ Added {len(sample_memories)} sample memories")


if __name__ == "__main__":
    import sys

    # Get database path from command line or use default
    db_path = sys.argv[1] if len(sys.argv) > 1 else "kite_data.db"

    print("=" * 60)
    print("  KITE TRADING LOG - MEMORY LAYER MIGRATION")
    print("=" * 60)

    # Run migration
    success = add_coach_memory_tables(db_path)

    if success:
        # Verify tables
        verify_tables(db_path)

        # Ask if user wants sample data
        add_samples = input("\n💭 Add sample memories for testing? (y/n): ").strip().lower()
        if add_samples == 'y':
            add_sample_memories(db_path)

        print("\n🎉 Migration complete! You're ready to use the memory layer.")
        print("\nNext steps:")
        print("  1. Update kite_client.py with new database methods")
        print("  2. Use CoachMemory class in coach_system_prompt.py")
        print("  3. Integrate with /api/coach endpoint")
    else:
        print("\n❌ Migration failed. Check errors above.")
        sys.exit(1)
