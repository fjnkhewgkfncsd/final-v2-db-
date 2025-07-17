#!/usr/bin/env python3
"""
Database Connection Test and Quick Record Generation
Tests connection and generates sample data before running million records
"""

import psycopg2
import sys
from faker import Faker
import random
import uuid

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecommerce_db',
    'user': 'postgres',
    'password': 'hengmengly123'
}

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connection successful!")
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 PostgreSQL Version: {version}")
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
            
            # Check current record counts
            print("\n📊 Current Record Counts:")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count:,} records")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def generate_sample_data(num_records=1000):
    """Generate a small sample of data to test the process"""
    print(f"\n🧪 Generating {num_records:,} sample records for testing...")
    
    fake = Faker()
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        with conn.cursor() as cursor:
            # Generate sample categories
            print("  📋 Generating categories...")
            for i in range(min(num_records, 100)):  # Limit categories
                cursor.execute("""
                    INSERT INTO categories (category_id, name, description, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (category_id) DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    fake.catch_phrase()[:100],
                    fake.text(max_nb_chars=200),
                    random.choice([True, False]),
                    fake.date_time_between(start_date='-2y', end_date='now')
                ))
            
            # Generate sample users
            print("  👥 Generating users...")
            roles = ['customer'] * 90 + ['staff'] * 8 + ['admin'] * 2
            for i in range(num_records):
                cursor.execute("""
                    INSERT INTO users (user_id, username, email, password_hash, first_name, last_name, 
                                     phone, date_of_birth, role, is_active, created_at, last_login)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id) DO NOTHING
                """, (
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
        
        conn.commit()
        print("✅ Sample data generation completed!")
        
        # Show updated counts
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM categories")
            cat_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            print(f"  📋 Categories: {cat_count:,} records")
            print(f"  👥 Users: {user_count:,} records")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error generating sample data: {e}")
    finally:
        conn.close()

def main():
    print("🧪 Database Connection Test & Sample Data Generator")
    print("=" * 60)
    
    # Test connection
    if not test_connection():
        print("❌ Cannot proceed without database connection")
        sys.exit(1)
    
    # Generate sample data
    response = input("\n❓ Generate 1,000 sample records for testing? (yes/no): ").lower().strip()
    if response in ['yes', 'y']:
        generate_sample_data(1000)
    
    print("\n✅ Database test completed!")
    print("🚀 Ready to run the million records generator:")
    print("   python generate_million_records.py")
    print("   OR")
    print("   python generate_million_records_ultra_fast.py")

if __name__ == "__main__":
    main()
