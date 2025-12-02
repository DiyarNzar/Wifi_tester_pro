"""
WiFi Tester Pro v6.0 - Abstract WiFi Driver
Base class defining the Strategy pattern interface for platform-specific drivers
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto

from ..settings import NetworkInfo


class DriverCapability(Enum):
    """Driver capability flags"""
    SCAN = auto()
    MONITOR_MODE = auto()
    PACKET_INJECTION = auto()
    CHANNEL_HOP = auto()
    DEAUTH = auto()
    WPS_PIN = auto()
    HANDSHAKE_CAPTURE = auto()


@dataclass
class InterfaceInfo:
    """WiFi interface information"""
    name: str
    mac_address: str
    driver: str = ""
    chipset: str = ""
    mode: str = "managed"  # managed, monitor, master
    channel: int = 0
    frequency: float = 0.0
    tx_power: int = 0
    is_up: bool = True
    is_wireless: bool = True
    supports_monitor: bool = False
    supports_injection: bool = False


class WiFiDriverBase(ABC):
    """
    Abstract base class for WiFi drivers.
    Implements Strategy pattern - each platform provides concrete implementation.
    """
    
    def __init__(self):
        self._current_interface: Optional[str] = None
        self._interfaces: Dict[str, InterfaceInfo] = {}
        self._capabilities: set = {DriverCapability.SCAN}
        self._is_initialized = False
    
    # ==========================================================================
    # Properties
    # ==========================================================================
    
    @property
    def current_interface(self) -> Optional[str]:
        """Get current active interface"""
        return self._current_interface
    
    @current_interface.setter
    def current_interface(self, interface: str):
        """Set current active interface"""
        self._current_interface = interface
    
    @property
    def capabilities(self) -> set:
        """Get driver capabilities"""
        return self._capabilities
    
    @property
    def is_initialized(self) -> bool:
        """Check if driver is initialized"""
        return self._is_initialized
    
    # ==========================================================================
    # Abstract Methods (must be implemented by subclasses)
    # ==========================================================================
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the driver.
        Returns True if successful.
        """
        pass
    
    @abstractmethod
    def get_interfaces(self) -> List[InterfaceInfo]:
        """
        Get list of available WiFi interfaces.
        Returns list of InterfaceInfo objects.
        """
        pass
    
    @abstractmethod
    def scan_networks(
        self,
        interface: Optional[str] = None,
        timeout: float = 10.0
    ) -> List[NetworkInfo]:
        """
        Scan for WiFi networks.
        
        Args:
            interface: Interface to use (defaults to current)
            timeout: Scan timeout in seconds
        
        Returns:
            List of discovered networks
        """
        pass
    
    @abstractmethod
    def get_current_connection(self) -> Optional[NetworkInfo]:
        """
        Get information about current WiFi connection.
        Returns None if not connected.
        """
        pass
    
    # ==========================================================================
    # Optional Methods (override in subclass if supported)
    # ==========================================================================
    
    def enable_monitor_mode(self, interface: Optional[str] = None) -> Tuple[bool, str]:
        """
        Enable monitor mode on interface.
        
        Returns:
            Tuple of (success, new_interface_name_or_error)
        """
        return False, "Monitor mode not supported on this platform"
    
    def disable_monitor_mode(self, interface: Optional[str] = None) -> Tuple[bool, str]:
        """
        Disable monitor mode and return to managed mode.
        
        Returns:
            Tuple of (success, message)
        """
        return False, "Monitor mode not supported on this platform"
    
    def set_channel(self, channel: int, interface: Optional[str] = None) -> bool:
        """Set interface channel (requires monitor mode)"""
        return False
    
    def get_channel(self, interface: Optional[str] = None) -> int:
        """Get current interface channel"""
        return 0
    
    def set_tx_power(self, power: int, interface: Optional[str] = None) -> bool:
        """Set transmit power in dBm"""
        return False
    
    def get_interface_info(self, interface: str) -> Optional[InterfaceInfo]:
        """Get detailed interface information"""
        return self._interfaces.get(interface)
    
    def is_monitor_mode(self, interface: Optional[str] = None) -> bool:
        """Check if interface is in monitor mode"""
        iface = interface or self._current_interface
        if iface and iface in self._interfaces:
            return self._interfaces[iface].mode == "monitor"
        return False
    
    # ==========================================================================
    # Utility Methods
    # ==========================================================================
    
    def has_capability(self, capability: DriverCapability) -> bool:
        """Check if driver has a specific capability"""
        return capability in self._capabilities
    
    def refresh_interfaces(self) -> List[InterfaceInfo]:
        """Refresh and return interface list"""
        return self.get_interfaces()
    
    def select_interface(self, interface: str) -> bool:
        """Select an interface as current"""
        interfaces = self.get_interfaces()
        interface_names = [i.name for i in interfaces]
        
        if interface in interface_names:
            self._current_interface = interface
            return True
        return False
    
    def get_interface_names(self) -> List[str]:
        """Get list of interface names"""
        return [i.name for i in self.get_interfaces()]
    
    def cleanup(self):
        """Cleanup resources on exit"""
        # Disable monitor mode if enabled
        if self._current_interface and self.is_monitor_mode():
            self.disable_monitor_mode()
        self._is_initialized = False
    
    # ==========================================================================
    # Default implementations (can be overridden)
    # ==========================================================================
    
    def get_signal_quality(self, signal_dbm: int) -> str:
        """Convert dBm to quality string"""
        if signal_dbm >= -50:
            return "excellent"
        elif signal_dbm >= -60:
            return "good"
        elif signal_dbm >= -70:
            return "fair"
        elif signal_dbm >= -80:
            return "weak"
        return "poor"
    
    def dbm_to_percent(self, signal_dbm: int) -> int:
        """Convert dBm to percentage (0-100)"""
        if signal_dbm >= -50:
            return 100
        elif signal_dbm <= -100:
            return 0
        return 2 * (signal_dbm + 100)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(interface={self._current_interface})"
    
    def __repr__(self) -> str:
        return self.__str__()


__all__ = [
    'WiFiDriverBase',
    'DriverCapability',
    'InterfaceInfo',
]
