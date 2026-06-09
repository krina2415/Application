import os
import sqlite3
import pymysql
from pymysql.cursors import DictCursor

# MySQL Connection Details
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'software_billing_db')
DB_PORT = int(os.environ.get('DB_PORT', 3306))

# SQLite File Path
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'software_billing.db')

def check_mysql_connection():
    """Checks if MySQL server is running and accessible on localhost."""
    conn = None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=1
        )
        conn.close()
        return True
    except Exception:
        return False

# Detect Database Type (MySQL or SQLite Fallback)
if check_mysql_connection():
    DB_TYPE = 'mysql'
    print("[INFO] MySQL server detected. Using MySQL database backend.")
else:
    DB_TYPE = 'sqlite'
    print("[WARNING] MySQL server is offline. Falling back to local SQLite database backend.")


class DatabaseContext:
    """Context manager to handle database connections and queries for MySQL and SQLite."""
    def __init__(self):
        self.conn = None
        self.cursor = None

    def __enter__(self):
        if DB_TYPE == 'mysql':
            self.conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                cursorclass=DictCursor,
                autocommit=True
            )
            self.cursor = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(SQLITE_PATH)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            if DB_TYPE == 'sqlite' and not exc_type:
                self.conn.commit()
            self.conn.close()

    def execute(self, sql, params=()):
        """Wrapper to execute SQL. Converts %s parameter format to ? for SQLite compatibility."""
        if DB_TYPE == 'sqlite':
            sql = sql.replace('%s', '?')
        self.cursor.execute(sql, params)
        return self.cursor


def seed_mock_data():
    """Seeds sample customer purchase records if the table is empty."""
    try:
        with DatabaseContext() as db:
            db.execute("SELECT COUNT(*) as count FROM bills")
            res = db.cursor.fetchone()
            if res:
                count = dict(res)['count']
                if count == 0:
                    print("[INFO] Seeding sample company billing data...")
                    # Record 1
                    sql = """
                        INSERT INTO bills (bill_no, customer_name, mobile_number, address, software_name, version, price, license_key, payment_status, payment_method, gst_rate, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    db.execute(sql, (
                        "BILL-20260606-1001", "Rajesh Patel", "9876543210", 
                        "A-402 Shanti Heights, SG Highway, Ahmedabad, Gujarat - 380015", 
                        "Windows 11 Professional", "Pro", 8500.00, 
                        "WIN11-PRO-XYZ", "Paid", "UPI", 18, 
                        "OEM retail activation key. Includes lifetime license."
                    ))
                    # Record 2
                    db.execute(sql, (
                        "BILL-20260606-1002", "Priyank Shah", "9988776655", 
                        "12 Raj Complex, Alkapuri, Vadodara, Gujarat - 390007", 
                        "Adobe Photoshop CC", "2026.1", 15400.00, 
                        "ADOBE-PS-202", "Pending", "Bank Transfer", 18, 
                        "Corporate Adobe Cloud subscription. Valid for 1 year."
                    ))
                    print("[SUCCESS] Mock company data seeded successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to seed mock data: {e}")


def init_db():
    """Initializes database schema in MySQL or SQLite depending on active backend."""
    conn = None
    try:
        if DB_TYPE == 'mysql':
            # Create Database in MySQL
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
                autocommit=True
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
            conn.close()
            
            # Create table in MySQL
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                port=DB_PORT,
                cursorclass=DictCursor,
                autocommit=True
            )
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bills (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        bill_no VARCHAR(50) NOT NULL UNIQUE,
                        customer_name VARCHAR(100) NOT NULL,
                        mobile_number VARCHAR(15) NOT NULL,
                        address TEXT NOT NULL,
                        software_name VARCHAR(100) NOT NULL,
                        version VARCHAR(20) NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        license_key VARCHAR(100) NOT NULL,
                        bill_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_customer_name (customer_name),
                        INDEX idx_mobile_number (mobile_number)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """)
                
                # Migrations: Add new corporate columns if they do not exist
                for col, col_type in [
                    ('payment_status', 'VARCHAR(20) DEFAULT "Paid"'),
                    ('payment_method', 'VARCHAR(50) DEFAULT "UPI"'),
                    ('gst_rate', 'INT DEFAULT 18'),
                    ('notes', 'TEXT')
                ]:
                    try:
                        cursor.execute(f"ALTER TABLE bills ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass # Ignore if column already exists
            conn.close()
            print("[SUCCESS] MySQL Database initialized and migrated successfully!")
        else:
            # Create table in SQLite
            conn = sqlite3.connect(SQLITE_PATH)
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS bills (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bill_no TEXT NOT NULL UNIQUE,
                        customer_name TEXT NOT NULL,
                        mobile_number TEXT NOT NULL,
                        address TEXT NOT NULL,
                        software_name TEXT NOT NULL,
                        version TEXT NOT NULL,
                        price REAL NOT NULL,
                        license_key TEXT NOT NULL,
                        bill_date DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Migrations: Add new corporate columns if they do not exist
                for col, col_type in [
                    ('payment_status', 'TEXT DEFAULT "Paid"'),
                    ('payment_method', 'TEXT DEFAULT "UPI"'),
                    ('gst_rate', 'INTEGER DEFAULT 18'),
                    ('notes', 'TEXT DEFAULT ""')
                ]:
                    try:
                        conn.execute(f"ALTER TABLE bills ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass # Ignore if column already exists
            conn.close()
            print("[SUCCESS] SQLite Database initialized and migrated successfully!")
        
        # Seed mock data if tables are empty
        seed_mock_data()
        
        return True, "Database initialized successfully"
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        raise e

def add_bill(bill_no, customer_name, mobile_number, address, software_name, version, price, license_key, payment_status='Paid', payment_method='UPI', gst_rate=18, notes=''):
    """Inserts a new bill record into the active database."""
    try:
        with DatabaseContext() as db:
            sql = """
                INSERT INTO bills (bill_no, customer_name, mobile_number, address, software_name, version, price, license_key, payment_status, payment_method, gst_rate, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            db.execute(sql, (bill_no, customer_name, mobile_number, address, software_name, version, price, license_key, payment_status, payment_method, gst_rate, notes))
            return True, db.cursor.lastrowid
    except Exception as e:
        print(f"Error adding bill: {e}")
        raise e

def get_all_bills():
    """Retrieves all billing records from the database ordered by newest first."""
    try:
        with DatabaseContext() as db:
            db.execute("SELECT * FROM bills ORDER BY bill_date DESC")
            rows = db.cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching bills: {e}")
        raise e

def get_bill_by_id(bill_id):
    """Retrieves a single bill detail by database ID."""
    try:
        with DatabaseContext() as db:
            db.execute("SELECT * FROM bills WHERE id = %s", (bill_id,))
            row = db.cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        print(f"Error fetching bill {bill_id}: {e}")
        raise e

def delete_bill_by_id(bill_id):
    """Deletes an invoice by its ID (for company record corrections)."""
    try:
        with DatabaseContext() as db:
            db.execute("DELETE FROM bills WHERE id = %s", (bill_id,))
            return True
    except Exception as e:
        print(f"Error deleting bill {bill_id}: {e}")
        raise e

def search_bills(query):
    """Searches billing records matching customer name or mobile number."""
    try:
        with DatabaseContext() as db:
            sql = """
                SELECT * FROM bills 
                WHERE customer_name LIKE %s OR mobile_number LIKE %s 
                ORDER BY bill_date DESC
            """
            search_param = f"%{query}%"
            db.execute(sql, (search_param, search_param))
            rows = db.cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error searching bills: {e}")
        raise e

def get_dashboard_stats():
    """Generates statistics for the active database."""
    stats = {
        'total_revenue': 0.00,
        'total_sales_count': 0,
        'unique_customers': 0,
        'popular_software': []
    }
    try:
        with DatabaseContext() as db:
            # 1. Total Revenue and Sales Count
            db.execute("SELECT COUNT(*) as count, SUM(price) as revenue FROM bills")
            res = db.cursor.fetchone()
            if res:
                res_dict = dict(res)
                stats['total_sales_count'] = res_dict['count']
                stats['total_revenue'] = float(res_dict['revenue']) if res_dict['revenue'] else 0.00
            
            # 2. Unique Customer Count
            db.execute("SELECT COUNT(DISTINCT mobile_number) as cust_count FROM bills")
            cust_res = db.cursor.fetchone()
            if cust_res:
                cust_dict = dict(cust_res)
                stats['unique_customers'] = cust_dict['cust_count']
                
            # 3. Popular Softwares list
            db.execute("""
                SELECT software_name, COUNT(*) as copies_sold, SUM(price) as total_sales
                FROM bills
                GROUP BY software_name
                ORDER BY copies_sold DESC, total_sales DESC
                LIMIT 3
            """)
            rows = db.cursor.fetchall()
            stats['popular_software'] = [dict(row) for row in rows]
            
    except Exception as e:
        print(f"Error calculating dashboard stats: {e}")
    return stats

def get_active_db_engine():
    return DB_TYPE

if __name__ == '__main__':
    # Initialize the active database
    init_db()
