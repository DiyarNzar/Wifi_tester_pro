"""
WiFi Tester Pro v6.0 - Terminal Widget
Console-style log viewer widget
"""

import customtkinter as ctk
from typing import Optional, List
from datetime import datetime

from ...settings import Colors, Fonts, Layout
from ...core.logger import LogEntry


class TerminalWidget(ctk.CTkFrame):
    """
    Terminal/console style widget for displaying logs and output.
    Supports colored text and auto-scrolling.
    """
    
    def __init__(
        self,
        parent,
        max_lines: int = 1000,
        show_timestamp: bool = True,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=Colors.TERMINAL_BG,
            corner_radius=8,
            **kwargs
        )
        
        self._max_lines = max_lines
        self._show_timestamp = show_timestamp
        self._line_count = 0
        self._auto_scroll = True
        
        self._create_ui()
    
    def _create_ui(self):
        """Create terminal UI"""
        # Header
        header = ctk.CTkFrame(self, fg_color=Colors.SURFACE_DARK, height=35, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="📟 Terminal",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY
        ).pack(side="left", padx=10)
        
        # Auto-scroll toggle
        self._autoscroll_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            header,
            text="Auto-scroll",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            variable=self._autoscroll_var,
            command=self._toggle_autoscroll,
            fg_color=Colors.PRIMARY,
            text_color=Colors.TEXT_SECONDARY,
            hover_color=Colors.PRIMARY_HOVER
        ).pack(side="right", padx=10)
        
        # Clear button
        ctk.CTkButton(
            header,
            text="Clear",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            width=60,
            height=25,
            fg_color="transparent",
            hover_color=Colors.SURFACE_LIGHT,
            text_color=Colors.TEXT_SECONDARY,
            command=self.clear
        ).pack(side="right", padx=5)
        
        # Text area
        self._text_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Use CTkTextbox for better performance
        self._textbox = ctk.CTkTextbox(
            self._text_frame,
            fg_color=Colors.TERMINAL_BG,
            text_color=Colors.TERMINAL_FG,
            font=(Fonts.MONO, Fonts.SIZE_SM),
            wrap="word",
            state="disabled"
        )
        self._textbox.pack(fill="both", expand=True)
        
        # Configure tags for colored output
        self._configure_tags()
    
    def _configure_tags(self):
        """Configure text tags for colored output"""
        # Note: CTkTextbox has limited tag support, using prefix coloring
        pass
    
    def _toggle_autoscroll(self):
        """Toggle auto-scroll behavior"""
        self._auto_scroll = self._autoscroll_var.get()
    
    def write(self, text: str, level: str = "INFO"):
        """
        Write text to terminal.
        
        Args:
            text: Text to write
            level: Log level for coloring (DEBUG, INFO, WARNING, ERROR)
        """
        # Get timestamp
        timestamp = ""
        if self._show_timestamp:
            timestamp = datetime.now().strftime("[%H:%M:%S] ")
        
        # Get level prefix
        level_prefixes = {
            "DEBUG": "[DBG]",
            "INFO": "[INF]",
            "WARNING": "[WRN]",
            "ERROR": "[ERR]",
            "CRITICAL": "[CRT]",
        }
        prefix = level_prefixes.get(level.upper(), "[---]")
        
        # Format line
        line = f"{timestamp}{prefix} {text}\n"
        
        # Enable writing
        self._textbox.configure(state="normal")
        
        # Add line
        self._textbox.insert("end", line)
        self._line_count += 1
        
        # Trim if too many lines
        if self._line_count > self._max_lines:
            self._textbox.delete("1.0", "2.0")
            self._line_count -= 1
        
        # Disable writing
        self._textbox.configure(state="disabled")
        
        # Auto-scroll
        if self._auto_scroll:
            self._textbox.see("end")
    
    def write_log(self, entry: LogEntry):
        """Write a LogEntry to terminal"""
        self.write(entry.message, entry.level)
    
    def writeln(self, text: str, level: str = "INFO"):
        """Write a line (alias for write)"""
        self.write(text, level)
    
    def debug(self, text: str):
        """Write debug message"""
        self.write(text, "DEBUG")
    
    def info(self, text: str):
        """Write info message"""
        self.write(text, "INFO")
    
    def warning(self, text: str):
        """Write warning message"""
        self.write(text, "WARNING")
    
    def error(self, text: str):
        """Write error message"""
        self.write(text, "ERROR")
    
    def clear(self):
        """Clear terminal content"""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.configure(state="disabled")
        self._line_count = 0
    
    def get_content(self) -> str:
        """Get all terminal content"""
        return self._textbox.get("1.0", "end")


__all__ = ['TerminalWidget']
