#!/usr/bin/env python3
"""
High-Performance Million Records Generator with Multiprocessing
Ultra-fast data generation using parallel processing and optimized SQL
"""

import psycopg2
import psycopg2.extras
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta
import sys
import time
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import os
import queue

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecommerce_db',
    'user': 'postgres',
    'password': 'hengmengly123'
}

# Configuration
TARGET_RECORDS = 1_000_000
BATCH_SIZE = 50_000  # Larger batches for better performance
NUM_WORKERS = min(8, mp.cpu_count())  # Optimize for available CPUs

class HighPerformanceGenerator:
    def __init__(self):
        self.conn = None
        self.setup_connection()
    
    def setup_connection(self):
        """Setup database connection with performance optimizations"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            
            # Performance optimizations
            with self.conn.cursor() as cursor:
                cursor.execute("SET synchronous_commit = OFF")
                cursor.execute("SET checkpoint_segments = 32")
                cursor.execute("SET wal_buffers = 16MB")
                cursor.execute("SET shared_buffers = '256MB'")
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET maintenance_work_mem = '256MB'")
            
            self.conn.commit()
            print("✅ High-performance database connection established")
            
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)
    
    def disable_constraints(self):
        """Temporarily disable constraints for faster insertion"""
        print("🔧 Disabling constraints for faster insertion...")
        try:
            with self.conn.cursor() as cursor:
                # Disable triggers and constraints
                cursor.execute("SET session_replication_role = replica")
                cursor.execute("ALTER TABLE products DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE orders DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE order_items DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE payments DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE shipments DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE cart_items DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE notifications DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE favorites DISABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE product_sizes DISABLE TRIGGER ALL")
            
            self.conn.commit()
            print("✅ Constraints disabled")
            
        except Exception as e:
            print(f"⚠️ Could not disable all constraints: {e}")
    
    def enable_constraints(self):
        """Re-enable constraints after insertion"""
        print("🔧 Re-enabling constraints...")
        try:
            with self.conn.cursor() as cursor:
                # Re-enable triggers and constraints
                cursor.execute("SET session_replication_role = DEFAULT")
                cursor.execute("ALTER TABLE products ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE orders ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE order_items ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE payments ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE shipments ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE cart_items ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE notifications ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE favorites ENABLE TRIGGER ALL")
                cursor.execute("ALTER TABLE product_sizes ENABLE TRIGGER ALL")
            
            self.conn.commit()
            print("✅ Constraints re-enabled")
            
        except Exception as e:
            print(f"⚠️ Could not re-enable all constraints: {e}")
    
    def drop_indexes(self):
        """Drop indexes temporarily for faster insertion"""
        print("🗂️ Dropping indexes for faster insertion...")
        try:
            with self.conn.cursor() as cursor:
                # Get all indexes except primary keys
                cursor.execute("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename IN (
                        'categories', 'users', 'products', 'product_sizes', 'cart', 'cart_items',
                        'orders', 'order_items', 'payments', 'shipments', 'notifications', 'favorites'
                    ) AND indexname NOT LIKE '%_pkey'
                """)
                
                indexes = cursor.fetchall()
                for (index_name,) in indexes:
                    cursor.execute(f"DROP INDEX IF EXISTS {index_name}")
                
            self.conn.commit()
            print(f"✅ Dropped {len(indexes)} indexes")
            
        except Exception as e:
            print(f"⚠️ Could not drop indexes: {e}")
    
    def recreate_indexes(self):
        """Recreate indexes after data insertion"""
        print("🗂️ Recreating indexes...")
        try:
            with self.conn.cursor() as cursor:
                # Recreate essential indexes
                index_queries = [
                    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
                    "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
                    "CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status)",
                    "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)",
                    "CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id)",
                    "CREATE INDEX IF NOT EXISTS idx_payments_order ON payments(order_id)",
                    "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status)",
                    "CREATE INDEX IF NOT EXISTS idx_cart_user ON cart(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_cart_items_cart ON cart_items(cart_id)",
                    "CREATE INDEX IF NOT EXISTS idx_cart_items_product ON cart_items(product_id)",
                    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
                    "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
                    "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
                    "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id)",
                    "CREATE INDEX IF NOT EXISTS idx_favorites_product ON favorites(product_id)",
                    "CREATE INDEX IF NOT EXISTS idx_shipments_order ON shipments(order_id)",
                    "CREATE INDEX IF NOT EXISTS idx_product_sizes_product ON product_sizes(product_id)"
                ]
                
                for query in index_queries:
                    cursor.execute(query)
                    print(f"  ✓ {query.split('idx_')[1].split(' ON')[0]}")
                
            self.conn.commit()
            print("✅ Indexes recreated")
            
        except Exception as e:
            print(f"⚠️ Error recreating indexes: {e}")

def generate_worker_data(table_name, num_records, worker_id):
    """Worker function to generate data in parallel"""
    fake = Faker()
    fake.seed_instance(worker_id * 1000)  # Ensure unique data per worker
    
    data = []
    
    if table_name == 'categories':
        for _ in range(num_records):
            data.append((
                str(uuid.uuid4()),
                fake.catch_phrase()[:100],
                fake.text(max_nb_chars=200),
                random.choice([True, False]),
                fake.date_time_between(start_date='-2y', end_date='now')
            ))
    
    elif table_name == 'users':
        roles = ['customer'] * 970 + ['staff'] * 25 + ['admin'] * 5
        for _ in range(num_records):
            data.append((
                str(uuid.uuid4()),
                fake.user_name()[:50],
                fake.email(),
                fake.password(length=60),
                fake.first_name()[:50],
                fake.last_name()[:50],
                fake.phone_number()[:20],
                fake.date_of_birth(minimum_age=18, maximum_age=80),
                random.choice(roles),
                random.choice([True, False]),
                fake.date_time_between(start_date='-2y', end_date='now'),
                fake.date_time_between(start_date='-30d', end_date='now') if random.random() > 0.3 else None
            ))
    
    return data

def ultra_fast_insert(table_name, columns, total_records):
    """Ultra-fast insertion using COPY command"""
    print(f"🚀 Ultra-fast generating {total_records:,} records for {table_name}")
    
    start_time = time.time()
    
    # Generate data in parallel
    records_per_worker = total_records // NUM_WORKERS
    
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for worker_id in range(NUM_WORKERS):
            records_for_worker = records_per_worker
            if worker_id == NUM_WORKERS - 1:  # Last worker gets remainder
                records_for_worker += total_records % NUM_WORKERS
            
            future = executor.submit(generate_worker_data, table_name, records_for_worker, worker_id)
            futures.append(future)
        
        # Collect all generated data
        all_data = []
        for future in futures:
            worker_data = future.result()
            all_data.extend(worker_data)
    
    # Insert using COPY for maximum speed
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        
        with conn.cursor() as cursor:
            # Create temporary table
            temp_table = f"temp_{table_name}_{int(time.time())}"
            
            # Get column definitions
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                ORDER BY ordinal_position
            """)
            
            table_columns = cursor.fetchall()
            column_defs = []
            
            for col_name, data_type, is_nullable, default in table_columns:
                col_def = f"{col_name} {data_type}"
                if is_nullable == 'NO':
                    col_def += " NOT NULL"
                if default:
                    col_def += f" DEFAULT {default}"
                column_defs.append(col_def)
            
            # Create temp table
            create_temp_sql = f"""
                CREATE TEMPORARY TABLE {temp_table} (
                    {', '.join(column_defs)}
                )
            """
            cursor.execute(create_temp_sql)
            
            # Use COPY for ultra-fast insertion
            import io
            data_io = io.StringIO()
            
            for record in all_data:
                # Convert record to tab-separated string
                formatted_record = []
                for value in record:
                    if value is None:
                        formatted_record.append('\\N')
                    elif isinstance(value, datetime):
                        formatted_record.append(value.isoformat())
                    elif isinstance(value, bool):
                        formatted_record.append('t' if value else 'f')
                    else:
                        formatted_record.append(str(value).replace('\t', ' ').replace('\n', ' '))
                
                data_io.write('\t'.join(formatted_record) + '\n')
            
            data_io.seek(0)
            
            # COPY data into temp table
            cursor.copy_from(data_io, temp_table, columns=columns, sep='\t')
            
            # Insert from temp table to actual table
            columns_str = ', '.join(columns)
            cursor.execute(f"""
                INSERT INTO {table_name} ({columns_str})
                SELECT {columns_str} FROM {temp_table}
            """)
            
            conn.commit()
            
        conn.close()
        
        elapsed = time.time() - start_time
        rate = total_records / elapsed if elapsed > 0 else 0
        print(f"✅ {table_name}: {total_records:,} records in {elapsed:.1f}s ({rate:.0f} records/sec)")
        
    except Exception as e:
        print(f"❌ Error in ultra-fast insert for {table_name}: {e}")

def run_ultra_fast_generation():
    """Run the ultra-fast generation process"""
    print("🚀 ULTRA-FAST Million Records Generator")
    print("⚡ Using multiprocessing and COPY commands for maximum speed")
    print("=" * 70)
    
    generator = HighPerformanceGenerator()
    
    try:
        # Performance optimizations
        generator.disable_constraints()
        generator.drop_indexes()
        
        start_time = time.time()
        
        # Generate data for each table
        tables_config = [
            ('categories', ['category_id', 'name', 'description', 'is_active', 'created_at']),
            ('users', ['user_id', 'username', 'email', 'password_hash', 'first_name', 'last_name', 
                      'phone', 'date_of_birth', 'role', 'is_active', 'created_at', 'last_login'])
        ]
        
        for table_name, columns in tables_config:
            ultra_fast_insert(table_name, columns, TARGET_RECORDS)
        
        elapsed = time.time() - start_time
        print(f"\n⚡ Ultra-fast generation completed in {elapsed:.1f} seconds!")
        
    finally:
        # Restore database state
        generator.recreate_indexes()
        generator.enable_constraints()
        generator.close()

if __name__ == "__main__":
    print("⚠️  WARNING: This is the ULTRA-FAST version!")
    print("💾 Will generate 1,000,000 records per table using parallel processing")
    print("⏱️  Estimated time: 30-90 minutes (much faster than standard version)")
    
    response = input("\n❓ Do you want to run the ultra-fast generator? (yes/no): ").lower().strip()
    if response in ['yes', 'y']:
        run_ultra_fast_generation()
    else:
        print("❌ Operation cancelled")
