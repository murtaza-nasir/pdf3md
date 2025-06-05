#!/usr/bin/env python3
"""
Ink2MD Database Manager
Based on PDF3MD by Murtaza Nsair
Original: https://github.com/murtaza-nasir/pdf3md

Copyright (C) 2025 Ink2MD Contributors
Copyright (C) 2024 Murtaza Nsair (original PDF3MD)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import sqlite3
import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Default database path - can be overridden via environment variable or config
DEFAULT_DB_PATH = os.environ.get('PDF3MD_DB_PATH', os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')), 'history.db'))

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_db_directory()
        self._initialize_database()

    def _ensure_db_directory(self):
        """Ensures the directory for the database file exists."""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
            except OSError as e:
                logger.error(f"Error creating database directory {db_dir}: {e}")
                raise

    def _initialize_database(self):
        """Initialize the database and create tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create conversion_history table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS conversion_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_filename TEXT NOT NULL,
                        output_filename TEXT,
                        conversion_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'queued',
                        htr_provider TEXT,
                        formatting_provider TEXT,
                        error_message TEXT,
                        raw_htr_output_path TEXT,
                        final_markdown_path TEXT,
                        retry_count INTEGER DEFAULT 0,
                        file_size INTEGER,
                        page_count INTEGER,
                        conversion_id TEXT UNIQUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create user_settings table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        setting_key TEXT NOT NULL UNIQUE,
                        setting_value TEXT NOT NULL,
                        setting_type TEXT DEFAULT 'string',
                        version INTEGER DEFAULT 1,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create index on conversion_id for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_conversion_id
                    ON conversion_history(conversion_id)
                ''')
                
                # Create index on status for filtering
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_status
                    ON conversion_history(status)
                ''')
                
                # Create index on timestamp for sorting
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON conversion_history(conversion_timestamp)
                ''')
                
                # Create index on setting_key for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_setting_key
                    ON user_settings(setting_key)
                ''')
                
                conn.commit()
                logger.info(f"Database initialized successfully at {self.db_path}")
                
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_conversion_record(self, conversion_id: str, original_filename: str, 
                               file_size: int = None, page_count: int = None) -> int:
        """Create a new conversion record and return its ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO conversion_history 
                    (conversion_id, original_filename, file_size, page_count, status)
                    VALUES (?, ?, ?, ?, 'queued')
                ''', (conversion_id, original_filename, file_size, page_count))
                
                record_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Created conversion record {record_id} for {original_filename}")
                return record_id
                
        except sqlite3.Error as e:
            logger.error(f"Error creating conversion record: {e}")
            raise

    def update_conversion_status(self, conversion_id: str, status: str, 
                               error_message: str = None, **kwargs) -> bool:
        """Update the status of a conversion record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Build dynamic update query based on provided kwargs
                update_fields = ['status = ?', 'updated_at = CURRENT_TIMESTAMP']
                values = [status]
                
                if error_message is not None:
                    update_fields.append('error_message = ?')
                    values.append(error_message)
                
                # Handle additional fields
                for field, value in kwargs.items():
                    if field in ['output_filename', 'htr_provider', 'formatting_provider', 
                               'raw_htr_output_path', 'final_markdown_path', 'retry_count']:
                        update_fields.append(f'{field} = ?')
                        values.append(value)
                
                values.append(conversion_id)
                
                query = f'''
                    UPDATE conversion_history 
                    SET {', '.join(update_fields)}
                    WHERE conversion_id = ?
                '''
                
                cursor.execute(query, values)
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    logger.info(f"Updated conversion {conversion_id} status to {status}")
                    return True
                else:
                    logger.warning(f"No conversion found with ID {conversion_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error updating conversion status: {e}")
            raise

    def get_conversion_by_id(self, conversion_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversion record by its ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM conversion_history 
                    WHERE conversion_id = ?
                ''', (conversion_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving conversion {conversion_id}: {e}")
            raise

    def get_conversion_history(self, limit: int = 50, offset: int = 0, 
                             status_filter: str = None) -> List[Dict[str, Any]]:
        """Get conversion history with optional filtering and pagination."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM conversion_history 
                '''
                params = []
                
                if status_filter:
                    query += ' WHERE status = ?'
                    params.append(status_filter)
                
                query += ' ORDER BY conversion_timestamp DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving conversion history: {e}")
            raise

    def get_failed_conversions(self) -> List[Dict[str, Any]]:
        """Get all failed conversions that can be retried."""
        return self.get_conversion_history(status_filter='failed')

    def increment_retry_count(self, conversion_id: str) -> bool:
        """Increment the retry count for a conversion."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE conversion_history 
                    SET retry_count = retry_count + 1, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE conversion_id = ?
                ''', (conversion_id,))
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    logger.info(f"Incremented retry count for conversion {conversion_id}")
                    return True
                else:
                    logger.warning(f"No conversion found with ID {conversion_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error incrementing retry count: {e}")
            raise

    def delete_conversion(self, conversion_id: str) -> bool:
        """Delete a conversion record."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM conversion_history 
                    WHERE conversion_id = ?
                ''', (conversion_id,))
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    logger.info(f"Deleted conversion record {conversion_id}")
                    return True
                else:
                    logger.warning(f"No conversion found with ID {conversion_id}")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error deleting conversion: {e}")
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get conversion statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total conversions
                cursor.execute('SELECT COUNT(*) as total FROM conversion_history')
                total = cursor.fetchone()['total']
                
                # Status breakdown
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM conversion_history 
                    GROUP BY status
                ''')
                status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Recent activity (last 24 hours)
                cursor.execute('''
                    SELECT COUNT(*) as recent 
                    FROM conversion_history 
                    WHERE conversion_timestamp >= datetime('now', '-1 day')
                ''')
                recent = cursor.fetchone()['recent']
                
                return {
                    'total_conversions': total,
                    'status_breakdown': status_counts,
                    'recent_activity': recent
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving statistics: {e}")
            raise

    def create_user_setting(self, setting_key: str, setting_value: str,
                           setting_type: str = "string") -> int:
        """Create a new user setting and return its ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_settings
                    (setting_key, setting_value, setting_type)
                    VALUES (?, ?, ?)
                ''', (setting_key, setting_value, setting_type))
                
                setting_id = cursor.lastrowid
                conn.commit()
                logger.info(f"Created user setting '{setting_key}' with ID {setting_id}")
                return setting_id
                
        except sqlite3.Error as e:
            logger.error(f"Error creating user setting: {e}")
            raise

    def update_user_setting(self, setting_key: str, setting_value: str,
                           setting_type: str = "string") -> bool:
        """Update or create a user setting."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if setting exists
                cursor.execute('''
                    SELECT id FROM user_settings WHERE setting_key = ?
                ''', (setting_key,))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing setting
                    cursor.execute('''
                        UPDATE user_settings
                        SET setting_value = ?, setting_type = ?,
                            version = version + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE setting_key = ?
                    ''', (setting_value, setting_type, setting_key))
                    logger.info(f"Updated user setting '{setting_key}'")
                else:
                    # Create new setting
                    cursor.execute('''
                        INSERT INTO user_settings
                        (setting_key, setting_value, setting_type)
                        VALUES (?, ?, ?)
                    ''', (setting_key, setting_value, setting_type))
                    logger.info(f"Created new user setting '{setting_key}'")
                
                rows_affected = cursor.rowcount
                conn.commit()
                return rows_affected > 0
                
        except sqlite3.Error as e:
            logger.error(f"Error updating user setting: {e}")
            raise

    def get_user_setting(self, setting_key: str) -> Optional[Dict[str, Any]]:
        """Get a user setting by key."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM user_settings
                    WHERE setting_key = ?
                ''', (setting_key,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving user setting '{setting_key}': {e}")
            raise

    def get_all_user_settings(self) -> List[Dict[str, Any]]:
        """Get all user settings."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM user_settings
                    ORDER BY setting_key
                ''')
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving all user settings: {e}")
            raise

    def delete_user_setting(self, setting_key: str) -> bool:
        """Delete a user setting."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM user_settings
                    WHERE setting_key = ?
                ''', (setting_key,))
                
                rows_affected = cursor.rowcount
                conn.commit()
                
                if rows_affected > 0:
                    logger.info(f"Deleted user setting '{setting_key}'")
                    return True
                else:
                    logger.warning(f"No user setting found with key '{setting_key}'")
                    return False
                    
        except sqlite3.Error as e:
            logger.error(f"Error deleting user setting: {e}")
            raise

    def get_user_settings_by_prefix(self, prefix: str) -> List[Dict[str, Any]]:
        """Get all user settings with keys starting with the given prefix."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM user_settings
                    WHERE setting_key LIKE ?
                    ORDER BY setting_key
                ''', (f"{prefix}%",))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except sqlite3.Error as e:
            logger.error(f"Error retrieving user settings with prefix '{prefix}': {e}")
            raise

# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def initialize_database(db_path: str = None):
    """Initialize the global database manager."""
    global db_manager
    db_manager = DatabaseManager(db_path)
    return db_manager

# Example usage and testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Test with a temporary database
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_history.db')
    
    # Clean up any existing test database
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    try:
        # Initialize database
        db = DatabaseManager(test_db_path)
        
        # Test creating a conversion record
        conversion_id = "test-conversion-123"
        record_id = db.create_conversion_record(
            conversion_id=conversion_id,
            original_filename="test.pdf",
            file_size=1024,
            page_count=5
        )
        print(f"Created record with ID: {record_id}")
        
        # Test updating status
        db.update_conversion_status(
            conversion_id=conversion_id,
            status="processing",
            htr_provider="ollama_llava"
        )
        
        # Test retrieving record
        record = db.get_conversion_by_id(conversion_id)
        print(f"Retrieved record: {record}")
        
        # Test completing conversion
        db.update_conversion_status(
            conversion_id=conversion_id,
            status="completed",
            output_filename="test_output.md",
            final_markdown_path="/path/to/output.md"
        )
        
        # Test getting history
        history = db.get_conversion_history(limit=10)
        print(f"History: {history}")
        
        # Test statistics
        stats = db.get_statistics()
        print(f"Statistics: {stats}")
        
        print("Database tests completed successfully!")
        
    finally:
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)