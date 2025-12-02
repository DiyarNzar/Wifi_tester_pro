"""
WiFi Tester Pro v6.0 - Main Window
Primary application window with navigation and content areas
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
import sys

from ..settings import (
    APP_NAME, APP_VERSION, Colors, Fonts, Layout,
    IS_WINDOWS, IS_KALI, RUNNING_AS_ADMIN, EventType
)
from ..core import Engine, Session, Logger, session, log
from .navigation import NavigationFrame
from .utils import center_window, show_message


class MainWindow(ctk.CTk):
    """
    Main application window.
    Manages navigation, content pages, and global state.
    """
    
    def __init__(
        self,
        driver=None,
        security_module=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Store references
        self._driver = driver
        self._security = security_module
        self._engine = Engine()
        self._session = session
        self._logger = log
        
        # Page frames
        self._pages: Dict[str, ctk.CTkFrame] = {}
        self._current_page: Optional[str] = None
        
        # Configure window
        self._setup_window()
        self._setup_theme()
        self._create_layout()
        self._create_pages()
        self._bind_events()
        
        # Initialize driver
        self._initialize_driver()
        
        # Show dashboard
        self.show_page("dashboard")
        
        self._logger.info("Application initialized", "MainWindow")
    
    def _setup_window(self):
        """Configure main window properties"""
        self.title(f"{APP_NAME} v{APP_VERSION}")
        
        # Set window size
        width = Layout.WINDOW_DEFAULT_WIDTH
        height = Layout.WINDOW_DEFAULT_HEIGHT
        self.geometry(f"{width}x{height}")
        self.minsize(Layout.WINDOW_MIN_WIDTH, Layout.WINDOW_MIN_HEIGHT)
        
        # Center window
        center_window(self, width, height)
        
        # Window icon (if available)
        try:
            if IS_WINDOWS:
                self.iconbitmap("assets/app_icon.ico")
        except:
            pass
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_theme(self):
        """Configure CustomTkinter theme"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure colors
        self.configure(fg_color=Colors.BG_DARK)
    
    def _create_layout(self):
        """Create main layout structure"""
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Navigation sidebar
        self._navigation = NavigationFrame(
            self,
            on_navigate=self.show_page,
            width=Layout.SIDEBAR_WIDTH
        )
        self._navigation.grid(row=0, column=0, sticky="nsw", padx=0, pady=0)
        
        # Main content area
        self._content_frame = ctk.CTkFrame(
            self,
            fg_color=Colors.BG_MEDIUM,
            corner_radius=0
        )
        self._content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self._content_frame.grid_columnconfigure(0, weight=1)
        self._content_frame.grid_rowconfigure(0, weight=1)
        
        # Status bar
        self._create_status_bar()
    
    def _create_status_bar(self):
        """Create bottom status bar"""
        self._status_bar = ctk.CTkFrame(
            self,
            height=30,
            fg_color=Colors.SURFACE_DARK,
            corner_radius=0
        )
        self._status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Status label
        self._status_label = ctk.CTkLabel(
            self._status_bar,
            text="Ready",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY
        )
        self._status_label.pack(side="left", padx=10)
        
        # Platform info
        platform_text = "Windows" if IS_WINDOWS else ("Kali Linux" if IS_KALI else "Linux")
        admin_text = "Admin" if RUNNING_AS_ADMIN else "User"
        
        self._platform_label = ctk.CTkLabel(
            self._status_bar,
            text=f"{platform_text} | {admin_text}",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_MUTED
        )
        self._platform_label.pack(side="right", padx=10)
        
        # Interface status
        self._interface_label = ctk.CTkLabel(
            self._status_bar,
            text="No interface",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY
        )
        self._interface_label.pack(side="right", padx=10)
    
    def _create_pages(self):
        """Create all page frames"""
        from .tabs import DashboardTab, ScannerTab, AuditorTab
        
        # Dashboard
        self._pages["dashboard"] = DashboardTab(
            self._content_frame,
            driver=self._driver,
            session=self._session,
            logger=self._logger
        )
        
        # Scanner
        self._pages["scanner"] = ScannerTab(
            self._content_frame,
            driver=self._driver,
            session=self._session,
            engine=self._engine,
            logger=self._logger
        )
        
        # Auditor
        self._pages["auditor"] = AuditorTab(
            self._content_frame,
            driver=self._driver,
            security=self._security,
            session=self._session,
            logger=self._logger
        )
    
    def _bind_events(self):
        """Bind session events"""
        self._session.subscribe(EventType.INTERFACE_CHANGED, self._on_interface_changed)
        self._session.subscribe(EventType.SCAN_STARTED, self._on_scan_started)
        self._session.subscribe(EventType.SCAN_COMPLETED, self._on_scan_completed)
    
    def _initialize_driver(self):
        """Initialize the WiFi driver"""
        if self._driver:
            try:
                if self._driver.initialize():
                    interfaces = self._driver.get_interfaces()
                    self._session.interfaces = [i.name for i in interfaces]
                    
                    if interfaces:
                        self._session.interface = interfaces[0].name
                        self.set_status(f"Interface: {interfaces[0].name}")
                    else:
                        self.set_status("No WiFi interfaces found")
                else:
                    self.set_status("Driver initialization failed")
            except Exception as e:
                self._logger.error(f"Driver init error: {e}", "MainWindow")
                self.set_status("Driver error")
    
    # ==========================================================================
    # Page Navigation
    # ==========================================================================
    
    def show_page(self, page_name: str):
        """Show a specific page"""
        if page_name not in self._pages:
            self._logger.warning(f"Unknown page: {page_name}", "MainWindow")
            return
        
        # Hide current page
        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].grid_forget()
        
        # Show new page
        self._pages[page_name].grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._current_page = page_name
        self._session.current_page = page_name
        
        # Update navigation
        self._navigation.set_active(page_name)
        
        # Refresh page if it has a refresh method
        page = self._pages[page_name]
        if hasattr(page, 'on_show'):
            page.on_show()
    
    # ==========================================================================
    # Event Handlers
    # ==========================================================================
    
    def _on_interface_changed(self, event_type: EventType, data: dict):
        """Handle interface change event"""
        new_interface = data.get("new", "None")
        self._interface_label.configure(text=f"Interface: {new_interface}")
    
    def _on_scan_started(self, event_type: EventType, data: dict):
        """Handle scan started event"""
        self.set_status("Scanning...")
    
    def _on_scan_completed(self, event_type: EventType, data: dict):
        """Handle scan completed event"""
        count = data.get("count", 0)
        total = data.get("total", 0)
        self.set_status(f"Scan complete: {count} new, {total} total networks")
    
    def _on_close(self):
        """Handle window close"""
        try:
            # Save session state
            self._session.save_state()
            
            # Cleanup driver
            if self._driver:
                self._driver.cleanup()
            
            # Shutdown engine
            self._engine.shutdown(wait=False)
            
            self._logger.info("Application closed", "MainWindow")
        except Exception as e:
            print(f"Cleanup error: {e}")
        finally:
            self.quit()
            self.destroy()
    
    # ==========================================================================
    # Public Methods
    # ==========================================================================
    
    def set_status(self, message: str):
        """Update status bar message"""
        self._status_label.configure(text=message)
    
    def get_driver(self):
        """Get WiFi driver instance"""
        return self._driver
    
    def get_session(self) -> Session:
        """Get session instance"""
        return self._session
    
    def get_engine(self) -> Engine:
        """Get engine instance"""
        return self._engine


__all__ = ['MainWindow']
