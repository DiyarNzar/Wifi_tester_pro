#!/usr/bin/env python3
"""
WiFi Tester Pro v6.0 - Entry Point
==================================
Production-ready WiFi Network Security Auditor
Cross-platform: Windows & Kali Linux

Usage:
    python main.py              # Normal mode
    sudo python main.py         # Kali Linux (required for security features)

Author: WiFi Tester Team
Version: 6.0.0
"""

import sys
import os
from pathlib import Path

# Add src to Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))


def print_banner():
    """Print application banner."""
    banner = r"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   █░█░█ █ █▀▀ █   ▀█▀ █▀▀ █▀ ▀█▀ █▀▀ █▀█   █▀█ █▀█ █▀█     ║
    ║   ▀▄▀▄▀ █ █▀░ █    █  ██▄ ▄█  █  ██▄ █▀▄   █▀▀ █▀▄ █▄█     ║
    ║                                                              ║
    ║              WiFi Tester Pro v6.0.0                          ║
    ║        Professional Network Security Auditor                 ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Ensure Python 3.10+ is being used."""
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    try:
        import customtkinter
    except ImportError:
        missing.append("customtkinter")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    try:
        import psutil
    except ImportError:
        missing.append("psutil")
    
    if missing:
        print("❌ Missing dependencies:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n📦 Install with: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main entry point."""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Print system info
    import platform
    print(f"\n📋 System Information:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Architecture: {platform.machine()}")
    
    # Check admin/root privileges
    from src.app_factory import is_admin
    admin_status = "✅ Yes" if is_admin() else "⚠️ No (some features limited)"
    print(f"   Privileges: {admin_status}")
    
    print("\n" + "=" * 60)
    print("🚀 Starting WiFi Tester Pro...")
    print("=" * 60 + "\n")
    
    try:
        # Import and create application via factory
        from src.app_factory import create_app
        from src.core.logger import Logger
        
        # Initialize logger
        logger = Logger()
        logger.info("Application starting...")
        
        # Create and run the application
        app = create_app()
        logger.info("GUI initialized successfully")
        
        # Start the main loop
        app.mainloop()
        
        logger.info("Application closed normally")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("   Make sure all dependencies are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
