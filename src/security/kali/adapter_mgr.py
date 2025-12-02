"""
WiFi Tester Pro v6.0 - Kali Adapter Manager
Manages wireless adapters for security testing (Kali Linux only)
"""

import subprocess
import os
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

from ...settings import IS_KALI


@dataclass
class AdapterInfo:
    """Wireless adapter information for security testing"""
    name: str
    driver: str
    chipset: str
    mac_address: str
    mode: str
    supports_monitor: bool
    supports_injection: bool
    phy: str = ""
    bus: str = ""


class AdapterManager:
    """
    Manages wireless adapters for security testing.
    Only functional on Kali Linux with appropriate hardware.
    """
    
    def __init__(self):
        self._adapters: Dict[str, AdapterInfo] = {}
        self._original_macs: Dict[str, str] = {}
    
    def get_adapters(self) -> List[AdapterInfo]:
        """Get list of wireless adapters"""
        if not IS_KALI:
            print("[AdapterManager] Not running on Kali Linux")
            return []
        
        adapters = []
        
        try:
            # Use airmon-ng to list adapters
            result = subprocess.run(
                ["airmon-ng"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[3:]:  # Skip header
                    parts = line.split('\t')
                    if len(parts) >= 4:
                        phy = parts[0].strip()
                        name = parts[1].strip()
                        driver = parts[2].strip()
                        chipset = parts[3].strip()
                        
                        # Check injection support
                        supports_injection = self._check_injection(name)
                        
                        adapter = AdapterInfo(
                            name=name,
                            driver=driver,
                            chipset=chipset,
                            mac_address=self._get_mac(name),
                            mode=self._get_mode(name),
                            supports_monitor=True,
                            supports_injection=supports_injection,
                            phy=phy,
                        )
                        adapters.append(adapter)
                        self._adapters[name] = adapter
            
        except Exception as e:
            print(f"[AdapterManager] Error: {e}")
        
        return adapters
    
    def _get_mac(self, interface: str) -> str:
        """Get MAC address of interface"""
        try:
            with open(f"/sys/class/net/{interface}/address") as f:
                return f.read().strip()
        except:
            return "00:00:00:00:00:00"
    
    def _get_mode(self, interface: str) -> str:
        """Get current mode of interface"""
        try:
            result = subprocess.run(
                ["iwconfig", interface],
                capture_output=True,
                text=True,
                timeout=10
            )
            if "Mode:Monitor" in result.stdout:
                return "monitor"
            elif "Mode:Master" in result.stdout:
                return "master"
            return "managed"
        except:
            return "unknown"
    
    def _check_injection(self, interface: str) -> bool:
        """Check if interface supports packet injection"""
        try:
            result = subprocess.run(
                ["aireplay-ng", "--test", interface],
                capture_output=True,
                text=True,
                timeout=30
            )
            return "Injection is working" in result.stdout
        except:
            return False
    
    def set_monitor_mode(self, interface: str) -> Tuple[bool, str]:
        """Set interface to monitor mode"""
        if not IS_KALI:
            return False, "Not running on Kali Linux"
        
        if os.geteuid() != 0:
            return False, "Root privileges required"
        
        try:
            result = subprocess.run(
                ["airmon-ng", "start", interface],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # New interface name is usually interface + "mon"
                new_name = f"{interface}mon"
                return True, new_name
            
            return False, result.stderr
            
        except Exception as e:
            return False, str(e)
    
    def set_managed_mode(self, interface: str) -> Tuple[bool, str]:
        """Return interface to managed mode"""
        if not IS_KALI:
            return False, "Not running on Kali Linux"
        
        try:
            result = subprocess.run(
                ["airmon-ng", "stop", interface],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, "Managed mode set"
            
            return False, result.stderr
            
        except Exception as e:
            return False, str(e)
    
    def change_mac(self, interface: str, new_mac: Optional[str] = None) -> Tuple[bool, str]:
        """
        Change MAC address of interface.
        If new_mac is None, generates random MAC.
        """
        if not IS_KALI:
            return False, "Not running on Kali Linux"
        
        try:
            # Save original MAC
            if interface not in self._original_macs:
                self._original_macs[interface] = self._get_mac(interface)
            
            # Bring interface down
            subprocess.run(["ip", "link", "set", interface, "down"], timeout=10)
            
            if new_mac:
                # Set specific MAC
                subprocess.run(
                    ["macchanger", "-m", new_mac, interface],
                    timeout=10
                )
            else:
                # Random MAC
                subprocess.run(
                    ["macchanger", "-r", interface],
                    timeout=10
                )
            
            # Bring interface up
            subprocess.run(["ip", "link", "set", interface, "up"], timeout=10)
            
            new_mac_actual = self._get_mac(interface)
            return True, new_mac_actual
            
        except Exception as e:
            return False, str(e)
    
    def restore_mac(self, interface: str) -> Tuple[bool, str]:
        """Restore original MAC address"""
        if interface not in self._original_macs:
            return False, "Original MAC not saved"
        
        return self.change_mac(interface, self._original_macs[interface])
    
    def set_channel(self, interface: str, channel: int) -> bool:
        """Set interface channel"""
        try:
            result = subprocess.run(
                ["iw", "dev", interface, "set", "channel", str(channel)],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def set_tx_power(self, interface: str, power_dbm: int) -> bool:
        """Set transmit power in dBm"""
        try:
            # Power in mBm (milliwatts)
            power_mbm = power_dbm * 100
            result = subprocess.run(
                ["iw", "dev", interface, "set", "txpower", "fixed", str(power_mbm)],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False


__all__ = ['AdapterManager', 'AdapterInfo']
