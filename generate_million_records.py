#!/usr/bin/env python3
"""
Million Records Data Generator for E-Commerce Database
Generates 1,000,000 records for each table in the database
"""

import psycopg2
import psycopg2.extras
from faker import Faker
import random
import uuid
from datetime import datetime, timedelta
import sys
import time
from concurrent.futures import ThreadPoolExecutor
import math

# Initialize Faker
fake = Faker()

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecommerce_db',
    'user': 'postgres',
    'password': 'hengmengly123'
}

# Target records per table
TARGET_RECORDS = 1_000_000
BATCH_SIZE = 10_000  # Insert in batches for better performance

class DataGenerator:
    def __init__(self):
        self.conn = None
        self.setup_connection()
        
    def setup_connection(self):
        """Setup database connection"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            print("✅ Database connection established")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            sys.exit(1)
    
    def execute_query(self, query, params=None):
        """Execute a query with error handling"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall() if cursor.description else None
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Query error: {e}")
            return None
    
    def batch_insert(self, table_name, columns, data_generator, total_records):
        """Insert data in batches for better performance"""
        print(f"🚀 Starting to generate {total_records:,} records for {table_name}")
        
        start_time = time.time()
        total_inserted = 0
        
        # Create insert query
        placeholders = ','.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
        
        try:
            with self.conn.cursor() as cursor:
                batch_data = []
                
                for i in range(total_records):
                    # Generate single record
                    record = data_generator()
                    batch_data.append(record)
                    
                    # Insert batch when full
                    if len(batch_data) >= BATCH_SIZE:
                        psycopg2.extras.execute_batch(cursor, insert_query, batch_data)
                        self.conn.commit()
                        
                        total_inserted += len(batch_data)
                        batch_data = []
                        
                        # Progress update
                        progress = (total_inserted / total_records) * 100
                        elapsed = time.time() - start_time
                        rate = total_inserted / elapsed if elapsed > 0 else 0
                        
                        print(f"📊 {table_name}: {total_inserted:,}/{total_records:,} ({progress:.1f}%) - {rate:.0f} records/sec")
                
                # Insert remaining records
                if batch_data:
                    psycopg2.extras.execute_batch(cursor, insert_query, batch_data)
                    self.conn.commit()
                    total_inserted += len(batch_data)
        
            elapsed = time.time() - start_time
            print(f"✅ {table_name} completed: {total_inserted:,} records in {elapsed:.1f}s ({total_inserted/elapsed:.0f} records/sec)")
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ Error inserting into {table_name}: {e}")
    
    def generate_categories(self):
        """Generate category record"""
        return (
            str(uuid.uuid4()),  # category_id
            fake.catch_phrase()[:100],  # name
            fake.text(max_nb_chars=200),  # description
            random.choice([True, False]),  # is_active
            fake.date_time_between(start_date='-2y', end_date='now')  # created_at
        )
    
    def generate_users(self):
        """Generate user record"""
        roles = ['customer'] * 970 + ['staff'] * 25 + ['admin'] * 5  # Realistic distribution
        
        return (
            str(uuid.uuid4()),  # user_id
            fake.user_name()[:50],  # username
            fake.email(),  # email
            fake.password(length=60),  # password_hash (fake hash)
            fake.first_name()[:50],  # first_name
            fake.last_name()[:50],  # last_name
            fake.phone_number()[:20],  # phone
            fake.date_of_birth(minimum_age=18, maximum_age=80),  # date_of_birth
            random.choice(roles),  # role
            random.choice([True, False]),  # is_active
            fake.date_time_between(start_date='-2y', end_date='now'),  # created_at
            fake.date_time_between(start_date='-30d', end_date='now') if random.random() > 0.3 else None  # last_login
        )
    
    def generate_products(self):
        """Generate product record (requires categories to exist)"""
        return (
            str(uuid.uuid4()),  # product_id
            fake.catch_phrase()[:100],  # name
            fake.text(max_nb_chars=500),  # description
            fake.ean13(),  # sku
            round(random.uniform(10.99, 999.99), 2),  # base_price
            random.randint(0, 1000),  # stock_quantity
            round(random.uniform(0.1, 50.0), 2),  # weight
            f"{random.randint(10,100)}x{random.randint(10,100)}x{random.randint(5,50)}cm",  # dimensions
            random.choice([True, False]),  # is_active
            fake.date_time_between(start_date='-2y', end_date='now')  # created_at
        )
    
    def generate_product_sizes(self):
        """Generate product size record (requires products to exist)"""
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '28', '30', '32', '34', '36', '38', '40']
        
        return (
            str(uuid.uuid4()),  # size_id
            random.choice(sizes),  # size_name
            round(random.uniform(0.0, 50.0), 2),  # additional_price
            random.randint(0, 100)  # stock_quantity
        )
    
    def generate_orders(self):
        """Generate order record (requires users to exist)"""
        statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        weights = [10, 20, 30, 35, 5]  # Realistic distribution
        
        subtotal = round(random.uniform(20.0, 500.0), 2)
        tax = round(subtotal * 0.08, 2)  # 8% tax
        shipping = round(random.uniform(0.0, 25.0), 2)
        total = subtotal + tax + shipping
        
        return (
            str(uuid.uuid4()),  # order_id
            subtotal,  # subtotal_amount
            tax,  # tax_amount
            shipping,  # shipping_amount
            total,  # final_amount
            random.choices(statuses, weights=weights)[0],  # order_status
            fake.address()[:200],  # shipping_address
            fake.address()[:200],  # billing_address
            fake.date_time_between(start_date='-1y', end_date='now')  # created_at
        )
    
    def generate_order_items(self):
        """Generate order item record (requires orders and products)"""
        quantity = random.randint(1, 5)
        unit_price = round(random.uniform(10.0, 200.0), 2)
        total_price = round(quantity * unit_price, 2)
        
        return (
            str(uuid.uuid4()),  # item_id
            quantity,  # quantity
            unit_price,  # unit_price
            total_price  # total_price
        )
    
    def generate_payments(self):
        """Generate payment record (requires orders to exist)"""
        methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer', 'cash']
        statuses = ['pending', 'completed', 'failed', 'refunded']
        status_weights = [5, 80, 10, 5]  # Realistic distribution
        
        return (
            str(uuid.uuid4()),  # payment_id
            round(random.uniform(20.0, 500.0), 2),  # amount
            random.choice(methods),  # payment_method
            random.choices(statuses, weights=status_weights)[0],  # payment_status
            fake.uuid4() if random.random() > 0.5 else None,  # transaction_id
            fake.date_time_between(start_date='-1y', end_date='now')  # created_at
        )
    
    def generate_cart(self):
        """Generate cart record (requires users to exist)"""
        return (
            str(uuid.uuid4()),  # cart_id
            fake.date_time_between(start_date='-30d', end_date='now')  # created_at
        )
    
    def generate_cart_items(self):
        """Generate cart item record (requires carts and products)"""
        return (
            str(uuid.uuid4()),  # item_id
            random.randint(1, 10),  # quantity
            fake.date_time_between(start_date='-30d', end_date='now')  # added_at
        )
    
    def generate_shipments(self):
        """Generate shipment record (requires orders to exist)"""
        carriers = ['FedEx', 'UPS', 'DHL', 'USPS', 'Amazon']
        statuses = ['pending', 'shipped', 'in_transit', 'delivered', 'returned']
        
        return (
            str(uuid.uuid4()),  # shipment_id
            random.choice(carriers),  # carrier
            fake.uuid4(),  # tracking_number
            random.choice(statuses),  # shipment_status
            fake.date_time_between(start_date='-1y', end_date='now'),  # shipped_date
            fake.date_time_between(start_date='-1y', end_date='now') if random.random() > 0.3 else None  # delivered_date
        )
    
    def generate_notifications(self):
        """Generate notification record (requires users to exist)"""
        types = ['order_update', 'promotion', 'system', 'payment', 'shipping']
        
        return (
            str(uuid.uuid4()),  # notification_id
            random.choice(types),  # notification_type
            fake.sentence()[:100],  # title
            fake.text(max_nb_chars=300),  # message
            random.choice([True, False]),  # is_read
            fake.date_time_between(start_date='-90d', end_date='now')  # created_at
        )
    
    def generate_favorites(self):
        """Generate favorite record (requires users and products)"""
        return (
            str(uuid.uuid4()),  # favorite_id
            fake.date_time_between(start_date='-1y', end_date='now')  # created_at
        )
    
    def get_random_ids(self, table, id_column, count=1):
        """Get random IDs from a table for foreign key references"""
        query = f"SELECT {id_column} FROM {table} ORDER BY RANDOM() LIMIT %s"
        result = self.execute_query(query, (count,))
        return [row[0] for row in result] if result else []
    
    def get_table_count(self, table):
        """Get current record count for a table"""
        result = self.execute_query(f"SELECT COUNT(*) FROM {table}")
        return result[0][0] if result else 0
    
    def generate_all_data(self):
        """Generate data for all tables in correct order"""
        print("🎯 Starting Million Records Data Generation")
        print("=" * 60)
        
        # 1. Generate Categories (no dependencies)
        current_count = self.get_table_count('categories')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"📋 Categories: Need {needed:,} more records (current: {current_count:,})")
            self.batch_insert(
                'categories',
                ['category_id', 'name', 'description', 'is_active', 'created_at'],
                self.generate_categories,
                needed
            )
        
        # 2. Generate Users (no dependencies)
        current_count = self.get_table_count('users')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"👥 Users: Need {needed:,} more records (current: {current_count:,})")
            self.batch_insert(
                'users',
                ['user_id', 'username', 'email', 'password_hash', 'first_name', 'last_name', 
                 'phone', 'date_of_birth', 'role', 'is_active', 'created_at', 'last_login'],
                self.generate_users,
                needed
            )
        
        # 3. Generate Products (requires categories)
        current_count = self.get_table_count('products')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"🛍️ Products: Need {needed:,} more records (current: {current_count:,})")
            
            # Get category IDs for foreign key
            category_ids = self.get_random_ids('categories', 'category_id', 1000)
            
            def generate_products_with_category():
                data = self.generate_products()
                # Insert random category_id as second element
                return data[:1] + (random.choice(category_ids),) + data[1:]
            
            self.batch_insert(
                'products',
                ['product_id', 'category_id', 'name', 'description', 'sku', 'base_price', 
                 'stock_quantity', 'weight', 'dimensions', 'is_active', 'created_at'],
                generate_products_with_category,
                needed
            )
        
        # 4. Generate Product Sizes (requires products)
        current_count = self.get_table_count('product_sizes')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"📏 Product Sizes: Need {needed:,} more records (current: {current_count:,})")
            
            product_ids = self.get_random_ids('products', 'product_id', 10000)
            
            def generate_sizes_with_product():
                data = self.generate_product_sizes()
                return data[:1] + (random.choice(product_ids),) + data[1:]
            
            self.batch_insert(
                'product_sizes',
                ['size_id', 'product_id', 'size_name', 'additional_price', 'stock_quantity'],
                generate_sizes_with_product,
                needed
            )
        
        # 5. Generate Carts (requires users)
        current_count = self.get_table_count('cart')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"🛒 Carts: Need {needed:,} more records (current: {current_count:,})")
            
            user_ids = self.get_random_ids('users', 'user_id', 10000)
            
            def generate_cart_with_user():
                data = self.generate_cart()
                return data[:1] + (random.choice(user_ids),) + data[1:]
            
            self.batch_insert(
                'cart',
                ['cart_id', 'user_id', 'created_at'],
                generate_cart_with_user,
                needed
            )
        
        # 6. Generate Cart Items (requires carts and products)
        current_count = self.get_table_count('cart_items')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"🛒 Cart Items: Need {needed:,} more records (current: {current_count:,})")
            
            cart_ids = self.get_random_ids('cart', 'cart_id', 10000)
            product_ids = self.get_random_ids('products', 'product_id', 10000)
            
            def generate_cart_items_with_refs():
                data = self.generate_cart_items()
                return data[:1] + (random.choice(cart_ids), random.choice(product_ids)) + data[1:]
            
            self.batch_insert(
                'cart_items',
                ['item_id', 'cart_id', 'product_id', 'quantity', 'added_at'],
                generate_cart_items_with_refs,
                needed
            )
        
        # 7. Generate Orders (requires users)
        current_count = self.get_table_count('orders')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"📦 Orders: Need {needed:,} more records (current: {current_count:,})")
            
            user_ids = self.get_random_ids('users', 'user_id', 10000)
            
            def generate_orders_with_user():
                data = self.generate_orders()
                return data[:1] + (random.choice(user_ids),) + data[1:]
            
            self.batch_insert(
                'orders',
                ['order_id', 'user_id', 'subtotal_amount', 'tax_amount', 'shipping_amount', 
                 'final_amount', 'order_status', 'shipping_address', 'billing_address', 'created_at'],
                generate_orders_with_user,
                needed
            )
        
        # 8. Generate Order Items (requires orders and products)
        current_count = self.get_table_count('order_items')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"📦 Order Items: Need {needed:,} more records (current: {current_count:,})")
            
            order_ids = self.get_random_ids('orders', 'order_id', 10000)
            product_ids = self.get_random_ids('products', 'product_id', 10000)
            
            def generate_order_items_with_refs():
                data = self.generate_order_items()
                return data[:1] + (random.choice(order_ids), random.choice(product_ids)) + data[1:]
            
            self.batch_insert(
                'order_items',
                ['item_id', 'order_id', 'product_id', 'quantity', 'unit_price', 'total_price'],
                generate_order_items_with_refs,
                needed
            )
        
        # 9. Generate Payments (requires orders)
        current_count = self.get_table_count('payments')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"💳 Payments: Need {needed:,} more records (current: {current_count:,})")
            
            order_ids = self.get_random_ids('orders', 'order_id', 10000)
            
            def generate_payments_with_order():
                data = self.generate_payments()
                return data[:1] + (random.choice(order_ids),) + data[1:]
            
            self.batch_insert(
                'payments',
                ['payment_id', 'order_id', 'amount', 'payment_method', 'payment_status', 
                 'transaction_id', 'created_at'],
                generate_payments_with_order,
                needed
            )
        
        # 10. Generate Shipments (requires orders)
        current_count = self.get_table_count('shipments')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"🚚 Shipments: Need {needed:,} more records (current: {current_count:,})")
            
            order_ids = self.get_random_ids('orders', 'order_id', 10000)
            
            def generate_shipments_with_order():
                data = self.generate_shipments()
                return data[:1] + (random.choice(order_ids),) + data[1:]
            
            self.batch_insert(
                'shipments',
                ['shipment_id', 'order_id', 'carrier', 'tracking_number', 'shipment_status', 
                 'shipped_date', 'delivered_date'],
                generate_shipments_with_order,
                needed
            )
        
        # 11. Generate Notifications (requires users)
        current_count = self.get_table_count('notifications')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"🔔 Notifications: Need {needed:,} more records (current: {current_count:,})")
            
            user_ids = self.get_random_ids('users', 'user_id', 10000)
            
            def generate_notifications_with_user():
                data = self.generate_notifications()
                return data[:1] + (random.choice(user_ids),) + data[1:]
            
            self.batch_insert(
                'notifications',
                ['notification_id', 'user_id', 'notification_type', 'title', 'message', 
                 'is_read', 'created_at'],
                generate_notifications_with_user,
                needed
            )
        
        # 12. Generate Favorites (requires users and products)
        current_count = self.get_table_count('favorites')
        if current_count < TARGET_RECORDS:
            needed = TARGET_RECORDS - current_count
            print(f"❤️ Favorites: Need {needed:,} more records (current: {current_count:,})")
            
            user_ids = self.get_random_ids('users', 'user_id', 10000)
            product_ids = self.get_random_ids('products', 'product_id', 10000)
            
            def generate_favorites_with_refs():
                data = self.generate_favorites()
                return data[:1] + (random.choice(user_ids), random.choice(product_ids)) + data[1:]
            
            self.batch_insert(
                'favorites',
                ['favorite_id', 'user_id', 'product_id', 'created_at'],
                generate_favorites_with_refs,
                needed
            )
        
        print("=" * 60)
        print("🎉 Million Records Data Generation Complete!")
        self.print_final_stats()
    
    def print_final_stats(self):
        """Print final table statistics"""
        tables = [
            'categories', 'users', 'products', 'product_sizes', 'cart', 'cart_items',
            'orders', 'order_items', 'payments', 'shipments', 'notifications', 'favorites'
        ]
        
        print("\n📊 Final Table Statistics:")
        print("-" * 40)
        total_records = 0
        
        for table in tables:
            count = self.get_table_count(table)
            total_records += count
            print(f"{table:<15}: {count:>10,} records")
        
        print("-" * 40)
        print(f"{'TOTAL':<15}: {total_records:>10,} records")
        
        # Calculate database size
        size_result = self.execute_query("SELECT pg_size_pretty(pg_database_size(current_database()))")
        if size_result:
            print(f"Database Size: {size_result[0][0]}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("📴 Database connection closed")

def main():
    """Main execution function"""
    print("🎯 E-Commerce Database Million Records Generator")
    print("⚠️  WARNING: This will generate 1,000,000 records per table!")
    print("💾 Estimated final database size: ~50-100 GB")
    print("⏱️  Estimated time: 2-6 hours depending on hardware")
    
    # Confirm execution
    response = input("\n❓ Do you want to proceed? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Operation cancelled by user")
        return
    
    start_time = time.time()
    generator = DataGenerator()
    
    try:
        generator.generate_all_data()
        
    except KeyboardInterrupt:
        print("\n⚠️ Operation interrupted by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        generator.close()
        
        elapsed = time.time() - start_time
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        seconds = int(elapsed % 60)
        
        print(f"\n⏱️ Total execution time: {hours:02d}:{minutes:02d}:{seconds:02d}")

if __name__ == "__main__":
    main()
