"""
WiFi Tester Pro v6.0 - Session Manager
Global application state management (Singleton pattern)
"""

import json
import time
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from pathlib import Path
from threading import Lock

from ..settings import (
    CONFIG_PATH, CURRENT_PLATFORM, Platform,
    NetworkInfo, EventType, IS_KALI, RUNNING_AS_ADMIN
)


@dataclass
class SessionState:
    """Serializable session state"""
    # Interface
    current_interface: Optional[str] = None
    available_interfaces: List[str] = field(default_factory=list)
    monitor_mode: bool = False
    
    # Scanning
    is_scanning: bool = False
    scan_count: int = 0
    last_scan_time: Optional[float] = None
    
    # Networks
    networks: Dict[str, Dict] = field(default_factory=dict)
    selected_network: Optional[str] = None  # BSSID
    
    # Auditing
    is_auditing: bool = False
    audit_target: Optional[str] = None
    
    # UI state
    current_page: str = "dashboard"
    theme: str = "dark"
    
    # Session info
    session_id: str = ""
    started_at: float = field(default_factory=time.time)
    platform: str = ""
    is_admin: bool = False
    is_kali: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SessionState':
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class Session:
    """
    Global session manager (Singleton).
    Tracks application state and provides pub/sub for state changes.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._state = SessionState(
            session_id=f"session_{int(time.time())}",
            platform=CURRENT_PLATFORM.name,
            is_admin=RUNNING_AS_ADMIN,
            is_kali=IS_KALI,
        )
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._state_file = CONFIG_PATH / "session_state.json"
        
        print(f"[Session] Initialized: {self._state.session_id}")
    
    # ==========================================================================
    # Properties (convenient access to state)
    # ==========================================================================
    
    @property
    def interface(self) -> Optional[str]:
        """Current WiFi interface"""
        return self._state.current_interface
    
    @interface.setter
    def interface(self, value: Optional[str]):
        old_value = self._state.current_interface
        self._state.current_interface = value
        if old_value != value:
            self._emit(EventType.INTERFACE_CHANGED, {
                "old": old_value,
                "new": value
            })
    
    @property
    def current_interface(self) -> Optional[str]:
        """Alias for interface"""
        return self._state.current_interface
    
    @current_interface.setter
    def current_interface(self, value: Optional[str]):
        self.interface = value
    
    @property
    def interfaces(self) -> List[str]:
        """Available WiFi interfaces"""
        return self._state.available_interfaces
    
    @interfaces.setter
    def interfaces(self, value: List[str]):
        self._state.available_interfaces = value
    
    @property
    def monitor_mode(self) -> bool:
        """Monitor mode status"""
        return self._state.monitor_mode
    
    @monitor_mode.setter
    def monitor_mode(self, value: bool):
        old_value = self._state.monitor_mode
        self._state.monitor_mode = value
        if old_value != value:
            event = EventType.MONITOR_MODE_ENABLED if value else EventType.MONITOR_MODE_DISABLED
            self._emit(event, {"interface": self.interface})
    
    @property
    def is_scanning(self) -> bool:
        """Scanning status"""
        return self._state.is_scanning
    
    @is_scanning.setter
    def is_scanning(self, value: bool):
        old_value = self._state.is_scanning
        self._state.is_scanning = value
        if value and not old_value:
            self._emit(EventType.SCAN_STARTED, {})
    
    @property
    def networks(self) -> Dict[str, Dict]:
        """Discovered networks (BSSID -> NetworkInfo dict)"""
        return self._state.networks
    
    @property
    def selected_network(self) -> Optional[str]:
        """Selected network BSSID"""
        return self._state.selected_network
    
    @selected_network.setter
    def selected_network(self, bssid: Optional[str]):
        self._state.selected_network = bssid
    
    @property
    def current_page(self) -> str:
        """Current UI page"""
        return self._state.current_page
    
    @current_page.setter
    def current_page(self, value: str):
        old_value = self._state.current_page
        self._state.current_page = value
        if old_value != value:
            self._emit(EventType.PAGE_CHANGED, {
                "old": old_value,
                "new": value
            })
    
    @property
    def is_admin(self) -> bool:
        """Admin/root status"""
        return self._state.is_admin
    
    @property
    def is_kali(self) -> bool:
        """Running on Kali Linux"""
        return self._state.is_kali
    
    @property
    def platform(self) -> str:
        """Current platform name"""
        return self._state.platform
    
    # ==========================================================================
    # Network Management
    # ==========================================================================
    
    def add_network(self, network: NetworkInfo):
        """Add or update a network"""
        bssid = network.bssid
        is_new = bssid not in self._state.networks
        
        self._state.networks[bssid] = asdict(network)
        
        if is_new:
            self._emit(EventType.NETWORK_FOUND, {"network": network})
        else:
            self._emit(EventType.NETWORK_UPDATED, {"network": network})
    
    def remove_network(self, bssid: str):
        """Remove a network"""
        if bssid in self._state.networks:
            network = self._state.networks.pop(bssid)
            self._emit(EventType.NETWORK_LOST, {"bssid": bssid, "network": network})
    
    def clear_networks(self):
        """Clear all networks"""
        self._state.networks.clear()
        self._state.selected_network = None
    
    def get_network(self, bssid: str) -> Optional[Dict]:
        """Get network by BSSID"""
        return self._state.networks.get(bssid)
    
    def get_networks_list(self) -> List[Dict]:
        """Get all networks as list"""
        return list(self._state.networks.values())
    
    def update_scan_results(self, networks: List[NetworkInfo]):
        """Update with scan results"""
        self._state.scan_count += 1
        self._state.last_scan_time = time.time()
        
        for network in networks:
            self.add_network(network)
        
        self._emit(EventType.SCAN_COMPLETED, {
            "count": len(networks),
            "total": len(self._state.networks)
        })
    
    # ==========================================================================
    # Event System (Pub/Sub)
    # ==========================================================================
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def _emit(self, event_type: EventType, data: dict):
        """Emit an event to all subscribers"""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event_type, data)
                except Exception as e:
                    print(f"[Session] Event callback error: {e}")
    
    def emit(self, event_type: EventType, data: dict = None):
        """Public emit method"""
        self._emit(event_type, data or {})
    
    # ==========================================================================
    # State Persistence
    # ==========================================================================
    
    def save_state(self):
        """Save session state to file"""
        try:
            state_dict = self._state.to_dict()
            # Remove non-serializable data
            state_dict.pop('networks', None)
            
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2)
            print(f"[Session] State saved")
        except Exception as e:
            print(f"[Session] Failed to save state: {e}")
    
    def load_state(self) -> bool:
        """Load session state from file"""
        try:
            if self._state_file.exists():
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Only restore UI preferences, not runtime state
                self._state.theme = data.get('theme', 'dark')
                self._state.current_page = data.get('current_page', 'dashboard')
                print(f"[Session] State loaded")
                return True
        except Exception as e:
            print(f"[Session] Failed to load state: {e}")
        return False
    
    # ==========================================================================
    # Utility
    # ==========================================================================
    
    def reset(self):
        """Reset session to initial state"""
        self._state = SessionState(
            session_id=f"session_{int(time.time())}",
            platform=CURRENT_PLATFORM.name,
            is_admin=RUNNING_AS_ADMIN,
            is_kali=IS_KALI,
        )
        print(f"[Session] Reset: {self._state.session_id}")
    
    def get_state(self) -> SessionState:
        """Get current state object"""
        return self._state
    
    def get_info(self) -> dict:
        """Get session info summary"""
        return {
            "session_id": self._state.session_id,
            "platform": self._state.platform,
            "is_admin": self._state.is_admin,
            "is_kali": self._state.is_kali,
            "interface": self._state.current_interface,
            "monitor_mode": self._state.monitor_mode,
            "network_count": len(self._state.networks),
            "scan_count": self._state.scan_count,
            "uptime": time.time() - self._state.started_at,
        }


# Global session instance
session = Session()


def get_session() -> Session:
    """Get global session instance"""
    return session


__all__ = [
    'Session',
    'SessionState',
    'session',
    'get_session',
]
