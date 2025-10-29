#!/usr/bin/env python3
"""
Healthcare Case Management System
Entry point for the Streamlit application
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv  # Add this import

# Add the src directory to Python path
src_path = Path(__file__).parent / 'src'
sys.path.append(str(src_path))

def main():
    """Main entry point"""
    try:
        # Load environment variables from .env file
        load_dotenv('env.example')  # Add this line
        
        # Check if required environment variables are set
        required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print("❌ Missing required environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\nPlease set these variables in your .env file")
            print("Or run: export AWS_ACCESS_KEY_ID=your_key && export AWS_SECRET_ACCESS_KEY=your_secret")
            return
        
        print("🚀 Starting Healthcare Case Management System...")
        print("📊 Opening Streamlit dashboard...")
        
        # Import and run Streamlit app
        from src.app import main as streamlit_main
        streamlit_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

if __name__ == "__main__":
    main()
