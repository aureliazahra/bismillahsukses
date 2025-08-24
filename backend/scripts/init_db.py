#!/usr/bin/env python3
"""
Database initialization script for missing_persons table
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import engine, Base
from models.missing_person import MissingPerson

def init_database():
    """Initialize the database and create tables"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        print("\nTables created:")
        print("- missing_persons")
        
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Initializing database...")
    success = init_database()
    
    if success:
        print("\n🎉 Database initialization completed successfully!")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)
