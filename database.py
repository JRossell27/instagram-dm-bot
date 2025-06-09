import sqlite3
from config import Config

class Database:
    def __init__(self):
        self.db_file = Config.DATABASE_FILE
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Table to track processed comments (updated for new workflow)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE,
                user_id TEXT,
                username TEXT,
                post_id TEXT,
                comment_text TEXT,
                keyword TEXT,
                action_taken TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table to track sent DMs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_dms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add missing columns to existing table if they don't exist
        cursor.execute("PRAGMA table_info(processed_comments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'comment_text' not in columns:
            cursor.execute('ALTER TABLE processed_comments ADD COLUMN comment_text TEXT')
        
        if 'action_taken' not in columns:
            cursor.execute('ALTER TABLE processed_comments ADD COLUMN action_taken TEXT')
        
        conn.commit()
        conn.close()
    
    def is_comment_processed(self, comment_id):
        """Check if a comment has already been processed"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM processed_comments WHERE comment_id = ?', (comment_id,))
        result = cursor.fetchone()
        
        conn.close()
        return result is not None
    
    def add_processed_comment(self, comment_id, post_id, username, user_id, comment_text, keyword, action_taken):
        """Add a processed comment with detailed tracking"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processed_comments 
            (comment_id, user_id, username, post_id, comment_text, keyword, action_taken)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (comment_id, user_id, username, post_id, comment_text, keyword, action_taken))
        
        conn.commit()
        conn.close()
    
    def mark_comment_processed(self, comment_id, user_id, username, post_id, keyword):
        """Mark a comment as processed (backward compatibility)"""
        self.add_processed_comment(comment_id, post_id, username, user_id, '', keyword, 'legacy_dm_sent')
    
    def log_sent_dm(self, user_id, username, message):
        """Log a sent DM"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sent_dms (user_id, username, message)
            VALUES (?, ?, ?)
        ''', (user_id, username, message))
        
        conn.commit()
        conn.close()
    
    def get_recent_processed_comments(self, limit=50):
        """Get recent processed comments for monitoring"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, keyword, action_taken, processed_at 
            FROM processed_comments 
            ORDER BY processed_at DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_comment_stats(self):
        """Get statistics about processed comments"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Get counts by action type
        cursor.execute('''
            SELECT action_taken, COUNT(*) as count
            FROM processed_comments 
            GROUP BY action_taken
        ''')
        
        action_counts = dict(cursor.fetchall())
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM processed_comments')
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_processed': total_count,
            'action_counts': action_counts
        } 