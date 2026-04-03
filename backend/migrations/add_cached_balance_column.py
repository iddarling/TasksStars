"""
Migration: Add cached_balance column to users table
Run this before init_balance_cache.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import aiosqlite
from app.core.config import settings


async def migrate_add_column():
    """Add cached_balance column to users table."""
    # Extract database path from DATABASE_URL
    # Format: sqlite+aiosqlite:///path/to/db.sqlite
    db_url = settings.DATABASE_URL
    if '///' in db_url:
        db_path = db_url.split('///')[1]
    else:
        db_path = 'taskstars.db'
    
    print(f"Connecting to database: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # Check if column exists
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = await cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'cached_balance' in column_names:
            print("Column 'cached_balance' already exists")
            return
        
        # Add the column
        await db.execute("""
            ALTER TABLE users 
            ADD COLUMN cached_balance INTEGER DEFAULT 0 NOT NULL
        """)
        await db.commit()
        print("✓ Added cached_balance column to users table")


if __name__ == "__main__":
    asyncio.run(migrate_add_column())
