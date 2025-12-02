"""
WiFi Tester Pro v6.0 - Packet Injector
Packet injection for security testing (Kali Linux only)

WARNING: This module is for AUTHORIZED SECURITY TESTING ONLY.
Unauthorized use is illegal and unethical.
"""

import os
from typing import Optional, Callable
from dataclasses import dataclass

from ...settings import IS_KALI

# Only import scapy on Kali
if IS_KALI:
    try:
        from scapy.all import (
            RadioTap, Dot11, Dot11Beacon, Dot11Elt,
            Dot11ProbeReq, Dot11ProbeResp,
            sendp, sniff, conf
        )
        SCAPY_AVAILABLE = True
    except ImportError:
        SCAPY_AVAILABLE = False
else:
    SCAPY_AVAILABLE = False


@dataclass
class InjectionResult:
    """Result of packet injection"""
    success: bool
    packets_sent: int
    packets_failed: int
    message: str


class PacketInjector:
    """
    Packet injection for security testing.
    Requires monitor mode and root privileges on Kali Linux.
    
    WARNING: For authorized testing only!
    """
    
    def __init__(self, interface: Optional[str] = None):
        self._interface = interface
        self._is_available = IS_KALI and SCAPY_AVAILABLE
        
        if not self._is_available:
            print("[PacketInjector] Not available (requires Kali + Scapy)")
    
    @property
    def is_available(self) -> bool:
        """Check if injection is available"""
        return self._is_available and os.geteuid() == 0
    
    def set_interface(self, interface: str):
        """Set the interface to use for injection"""
        self._interface = interface
        if SCAPY_AVAILABLE:
            conf.iface = interface
    
    def inject_beacon(
        self,
        ssid: str,
        bssid: str,
        channel: int = 1,
        count: int = 10
    ) -> InjectionResult:
        """
        Inject beacon frames (for testing detection systems).
        
        WARNING: For authorized testing only!
        """
        if not self.is_available:
            return InjectionResult(False, 0, 0, "Injection not available")
        
        if not self._interface:
            return InjectionResult(False, 0, 0, "No interface set")
        
        try:
            # Build beacon frame
            dot11 = Dot11(
                type=0, subtype=8,
                addr1="ff:ff:ff:ff:ff:ff",
                addr2=bssid,
                addr3=bssid
            )
            
            beacon = Dot11Beacon(cap="ESS")
            essid = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))
            channel_elt = Dot11Elt(ID="DSset", info=chr(channel))
            
            frame = RadioTap() / dot11 / beacon / essid / channel_elt
            
            # Send frames
            sendp(frame, iface=self._interface, count=count, verbose=False)
            
            return InjectionResult(True, count, 0, f"Sent {count} beacon frames")
            
        except Exception as e:
            return InjectionResult(False, 0, 1, str(e))
    
    def inject_probe_request(
        self,
        ssid: str,
        source_mac: str = "00:11:22:33:44:55",
        count: int = 5
    ) -> InjectionResult:
        """
        Inject probe request frames.
        
        WARNING: For authorized testing only!
        """
        if not self.is_available:
            return InjectionResult(False, 0, 0, "Injection not available")
        
        if not self._interface:
            return InjectionResult(False, 0, 0, "No interface set")
        
        try:
            dot11 = Dot11(
                type=0, subtype=4,
                addr1="ff:ff:ff:ff:ff:ff",
                addr2=source_mac,
                addr3="ff:ff:ff:ff:ff:ff"
            )
            
            probe = Dot11ProbeReq()
            essid = Dot11Elt(ID="SSID", info=ssid, len=len(ssid))
            
            frame = RadioTap() / dot11 / probe / essid
            
            sendp(frame, iface=self._interface, count=count, verbose=False)
            
            return InjectionResult(True, count, 0, f"Sent {count} probe requests")
            
        except Exception as e:
            return InjectionResult(False, 0, 1, str(e))
    
    def test_injection(self) -> InjectionResult:
        """Test if injection is working"""
        if not self.is_available:
            return InjectionResult(False, 0, 0, "Injection not available")
        
        # Try to send a test packet
        return self.inject_probe_request(
            ssid="InjectionTest",
            count=1
        )


__all__ = ['PacketInjector', 'InjectionResult']
