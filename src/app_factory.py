"""
WiFi Tester Pro v6.0 - Application Factory
OS-safe application loader with graceful fallbacks
"""

import sys
import importlib
import ctypes
import os
from typing import Optional, Any, TYPE_CHECKING
from .settings import (
    IS_WINDOWS, IS_LINUX, IS_KALI,
    CURRENT_PLATFORM, Platform, APP_NAME
)

if TYPE_CHECKING:
    from .gui.main_window import MainWindow


def is_admin() -> bool:
    """
    Check if the application is running with administrator/root privileges.
    Required for certain network operations.
    """
    try:
        if IS_WINDOWS:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except:
        return False


class AppFactory:
    """
    Factory class for creating OS-specific application components.
    Implements Strategy pattern for cross-platform compatibility.
    """
    
    _driver = None
    _security_module = None
    _app_instance = None
    
    @classmethod
    def get_driver(cls):
        """
        Get the appropriate WiFi driver for the current platform.
        Returns Windows or Linux driver based on OS detection.
        """
        if cls._driver is not None:
            return cls._driver
        
        try:
            if IS_WINDOWS:
                from .drivers.win_driver import WindowsWiFiDriver
                cls._driver = WindowsWiFiDriver()
                print(f"[AppFactory] Loaded Windows WiFi Driver")
            elif IS_LINUX or IS_KALI:
                from .drivers.lin_driver import LinuxWiFiDriver
                cls._driver = LinuxWiFiDriver()
                print(f"[AppFactory] Loaded Linux WiFi Driver {'(Kali)' if IS_KALI else ''}")
            else:
                # Fallback to base driver (limited functionality)
                from .drivers.abstract import WiFiDriverBase
                cls._driver = WiFiDriverBase()
                print(f"[AppFactory] Warning: Using base driver (limited functionality)")
        except ImportError as e:
            print(f"[AppFactory] Error loading driver: {e}")
            from .drivers.abstract import WiFiDriverBase
            cls._driver = WiFiDriverBase()
        
        return cls._driver
    
    @classmethod
    def get_security_module(cls):
        """
        Get security/auditing module.
        Full features only available on Kali Linux.
        """
        if cls._security_module is not None:
            return cls._security_module
        
        try:
            if IS_KALI:
                # Full Kali security tools
                from .security import kali as security_module
                cls._security_module = security_module
                print(f"[AppFactory] Loaded Kali security module (full features)")
            else:
                # Common security features only
                from .security import common
                cls._security_module = common
                print(f"[AppFactory] Loaded common security module (limited features)")
        except ImportError as e:
            print(f"[AppFactory] Warning: Security module not available: {e}")
            cls._security_module = None
        
        return cls._security_module
    
    @classmethod
    def create_app(cls) -> 'MainWindow':
        """
        Create and return the main application window.
        Initializes all required components.
        """
        if cls._app_instance is not None:
            return cls._app_instance
        
        # Pre-initialize components
        driver = cls.get_driver()
        security = cls.get_security_module()
        
        # Import and create main window
        from .gui.main_window import MainWindow
        
        cls._app_instance = MainWindow(
            driver=driver,
            security_module=security
        )
        
        return cls._app_instance
    
    @classmethod
    def run(cls) -> int:
        """
        Create and run the application.
        Returns exit code.
        """
        try:
            app = cls.create_app()
            app.mainloop()
            return 0
        except KeyboardInterrupt:
            print(f"\n[{APP_NAME}] Interrupted by user")
            return 130
        except Exception as e:
            print(f"[{APP_NAME}] Fatal error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            cls.cleanup()
    
    @classmethod
    def cleanup(cls):
        """Clean up resources on exit"""
        try:
            if cls._driver:
                cls._driver.cleanup()
            if cls._app_instance:
                cls._app_instance.destroy()
        except:
            pass
        
        cls._driver = None
        cls._security_module = None
        cls._app_instance = None
        print(f"[AppFactory] Cleanup complete")
    
    @classmethod
    def get_platform_info(cls) -> dict:
        """Get current platform information"""
        return {
            "platform": CURRENT_PLATFORM.name,
            "is_windows": IS_WINDOWS,
            "is_linux": IS_LINUX,
            "is_kali": IS_KALI,
            "python_version": sys.version,
            "driver_loaded": cls._driver is not None,
            "security_loaded": cls._security_module is not None,
        }


# Convenience functions
def create_app() -> 'MainWindow':
    """Create application instance"""
    return AppFactory.create_app()

def run_app() -> int:
    """Run the application"""
    return AppFactory.run()

def get_driver():
    """Get WiFi driver for current platform"""
    return AppFactory.get_driver()

def get_security():
    """Get security module for current platform"""
    return AppFactory.get_security_module()


__all__ = [
    'AppFactory',
    'create_app',
    'run_app',
    'get_driver',
    'get_security',
    'is_admin',
]
