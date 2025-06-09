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
        
        # Table to track processed comments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT UNIQUE,
                user_id TEXT,
                username TEXT,
                post_id TEXT,
                keyword TEXT,
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
    
    def mark_comment_processed(self, comment_id, user_id, username, post_id, keyword):
        """Mark a comment as processed"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO processed_comments (comment_id, user_id, username, post_id, keyword)
            VALUES (?, ?, ?, ?, ?)
        ''', (comment_id, user_id, username, post_id, keyword))
        
        conn.commit()
        conn.close()
    
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
            SELECT username, keyword, processed_at 
            FROM processed_comments 
            ORDER BY processed_at DESC 
            LIMIT ?
        ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        return results 