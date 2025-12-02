"""
WiFi Tester Pro v6.0 - GUI Utilities
Helper functions for creating consistent UI elements
"""

import customtkinter as ctk
from typing import Optional, Callable, Tuple
from tkinter import messagebox

from ..settings import Colors, Fonts


def center_window(window: ctk.CTk, width: int, height: int):
    """Center a window on the screen"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    window.geometry(f"{width}x{height}+{x}+{y}")


def create_button(
    parent,
    text: str,
    command: Optional[Callable] = None,
    style: str = "primary",
    width: int = 120,
    height: int = 36,
    icon: str = "",
    **kwargs
) -> ctk.CTkButton:
    """
    Create a styled button.
    
    Args:
        parent: Parent widget
        text: Button text
        command: Click handler
        style: Button style - "primary", "secondary", "danger", "success", "ghost"
        width: Button width
        height: Button height
        icon: Optional icon prefix
        **kwargs: Additional CTkButton arguments
    
    Returns:
        Configured CTkButton
    """
    # Style configurations
    styles = {
        "primary": {
            "fg_color": Colors.PRIMARY,
            "hover_color": Colors.PRIMARY_HOVER,
            "text_color": Colors.TEXT_PRIMARY,
        },
        "secondary": {
            "fg_color": Colors.SURFACE_LIGHT,
            "hover_color": Colors.SURFACE_MEDIUM,
            "text_color": Colors.TEXT_PRIMARY,
        },
        "danger": {
            "fg_color": Colors.ERROR,
            "hover_color": "#C0392B",
            "text_color": Colors.TEXT_PRIMARY,
        },
        "success": {
            "fg_color": Colors.SUCCESS,
            "hover_color": "#27AE60",
            "text_color": Colors.TEXT_PRIMARY,
        },
        "warning": {
            "fg_color": Colors.WARNING,
            "hover_color": "#E67E22",
            "text_color": Colors.TEXT_PRIMARY,
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": Colors.SURFACE_LIGHT,
            "text_color": Colors.TEXT_SECONDARY,
            "border_width": 1,
            "border_color": Colors.BORDER,
        },
    }
    
    style_config = styles.get(style, styles["primary"])
    
    display_text = f"{icon} {text}" if icon else text
    
    return ctk.CTkButton(
        parent,
        text=display_text,
        command=command,
        width=width,
        height=height,
        corner_radius=8,
        font=(Fonts.FAMILY, Fonts.SIZE_MD),
        **style_config,
        **kwargs
    )


def create_label(
    parent,
    text: str,
    style: str = "normal",
    **kwargs
) -> ctk.CTkLabel:
    """
    Create a styled label.
    
    Args:
        parent: Parent widget
        text: Label text
        style: Label style - "title", "heading", "normal", "muted", "caption"
        **kwargs: Additional CTkLabel arguments
    
    Returns:
        Configured CTkLabel
    """
    styles = {
        "title": {
            "font": (Fonts.FAMILY, Fonts.SIZE_TITLE, "bold"),
            "text_color": Colors.TEXT_PRIMARY,
        },
        "heading": {
            "font": (Fonts.FAMILY, Fonts.SIZE_XL, "bold"),
            "text_color": Colors.TEXT_PRIMARY,
        },
        "subheading": {
            "font": (Fonts.FAMILY, Fonts.SIZE_LG),
            "text_color": Colors.TEXT_PRIMARY,
        },
        "normal": {
            "font": (Fonts.FAMILY, Fonts.SIZE_MD),
            "text_color": Colors.TEXT_PRIMARY,
        },
        "secondary": {
            "font": (Fonts.FAMILY, Fonts.SIZE_MD),
            "text_color": Colors.TEXT_SECONDARY,
        },
        "muted": {
            "font": (Fonts.FAMILY, Fonts.SIZE_SM),
            "text_color": Colors.TEXT_MUTED,
        },
        "caption": {
            "font": (Fonts.FAMILY, Fonts.SIZE_SM),
            "text_color": Colors.TEXT_SECONDARY,
        },
    }
    
    style_config = styles.get(style, styles["normal"])
    
    return ctk.CTkLabel(
        parent,
        text=text,
        **style_config,
        **kwargs
    )


def create_entry(
    parent,
    placeholder: str = "",
    width: int = 200,
    height: int = 40,
    show: str = "",
    **kwargs
) -> ctk.CTkEntry:
    """Create a styled entry field"""
    return ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        width=width,
        height=height,
        corner_radius=8,
        border_width=2,
        border_color=Colors.BORDER,
        fg_color=Colors.SURFACE_DARK,
        text_color=Colors.TEXT_PRIMARY,
        placeholder_text_color=Colors.TEXT_MUTED,
        font=(Fonts.FAMILY, Fonts.SIZE_MD),
        show=show,
        **kwargs
    )


def create_card(
    parent,
    title: str = "",
    **kwargs
) -> Tuple[ctk.CTkFrame, ctk.CTkFrame]:
    """
    Create a card container with optional title.
    
    Returns:
        Tuple of (card_frame, content_frame)
    """
    card = ctk.CTkFrame(
        parent,
        fg_color=Colors.SURFACE_MEDIUM,
        corner_radius=12,
        **kwargs
    )
    
    if title:
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        
        ctk.CTkLabel(
            header,
            text=title,
            font=(Fonts.FAMILY, Fonts.SIZE_LG, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w")
    
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=16, pady=(8, 16))
    
    return card, content


def create_separator(parent, orientation: str = "horizontal") -> ctk.CTkFrame:
    """Create a separator line"""
    if orientation == "horizontal":
        sep = ctk.CTkFrame(parent, height=1, fg_color=Colors.BORDER)
    else:
        sep = ctk.CTkFrame(parent, width=1, fg_color=Colors.BORDER)
    return sep


def show_message(
    title: str,
    message: str,
    msg_type: str = "info"
):
    """
    Show a message dialog.
    
    Args:
        title: Dialog title
        message: Dialog message
        msg_type: Type - "info", "warning", "error", "question"
    """
    if msg_type == "info":
        messagebox.showinfo(title, message)
    elif msg_type == "warning":
        messagebox.showwarning(title, message)
    elif msg_type == "error":
        messagebox.showerror(title, message)
    elif msg_type == "question":
        return messagebox.askyesno(title, message)


def ask_confirmation(title: str, message: str) -> bool:
    """Show a yes/no confirmation dialog"""
    return messagebox.askyesno(title, message)


def format_mac(mac: str) -> str:
    """Format MAC address consistently"""
    mac = mac.upper().replace("-", ":").replace(".", ":")
    return mac


def format_signal(signal_dbm: int) -> str:
    """Format signal strength with indicator"""
    if signal_dbm >= -50:
        indicator = "████"
    elif signal_dbm >= -60:
        indicator = "███░"
    elif signal_dbm >= -70:
        indicator = "██░░"
    elif signal_dbm >= -80:
        indicator = "█░░░"
    else:
        indicator = "░░░░"
    
    return f"{signal_dbm} dBm {indicator}"


def get_signal_color(signal_dbm: int) -> str:
    """Get color for signal strength"""
    if signal_dbm >= -50:
        return Colors.SIGNAL_EXCELLENT
    elif signal_dbm >= -60:
        return Colors.SIGNAL_GOOD
    elif signal_dbm >= -70:
        return Colors.SIGNAL_FAIR
    elif signal_dbm >= -80:
        return Colors.SIGNAL_WEAK
    return Colors.SIGNAL_POOR


def get_security_color(security: str) -> str:
    """Get color for security type"""
    security = security.upper()
    if 'WPA3' in security:
        return Colors.SEC_WPA3
    elif 'WPA2' in security:
        return Colors.SEC_WPA2
    elif 'WPA' in security:
        return Colors.SEC_WPA
    elif 'WEP' in security:
        return Colors.SEC_WEP
    return Colors.SEC_OPEN


__all__ = [
    'center_window',
    'create_button',
    'create_label',
    'create_entry',
    'create_card',
    'create_separator',
    'show_message',
    'ask_confirmation',
    'format_mac',
    'format_signal',
    'get_signal_color',
    'get_security_color',
]
