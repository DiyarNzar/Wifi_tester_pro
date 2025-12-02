"""
WiFi Tester Pro v6.0 - Common Security Module
Cross-platform security analysis and vulnerability assessment
"""

import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum, auto

from ..settings import NetworkInfo, SecurityLevel


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels"""
    INFO = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()
    
    @property
    def color(self) -> str:
        """Get color code for severity"""
        colors = {
            VulnerabilitySeverity.INFO: "#3498DB",
            VulnerabilitySeverity.LOW: "#2ECC71",
            VulnerabilitySeverity.MEDIUM: "#F39C12",
            VulnerabilitySeverity.HIGH: "#E67E22",
            VulnerabilitySeverity.CRITICAL: "#E74C3C",
        }
        return colors.get(self, "#FFFFFF")


@dataclass
class Vulnerability:
    """Represents a security vulnerability"""
    id: str
    name: str
    description: str
    severity: VulnerabilitySeverity
    category: str = "General"
    cve: str = ""
    recommendation: str = ""
    references: List[str] = field(default_factory=list)
    affected_network: Optional[str] = None  # BSSID
    detected_at: float = field(default_factory=time.time)


@dataclass
class VulnerabilityReport:
    """Security scan report"""
    target_bssid: str
    target_ssid: str
    scan_started: float = field(default_factory=time.time)
    scan_completed: Optional[float] = None
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    security_score: int = 100  # 0-100
    
    @property
    def critical_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.HIGH])
    
    @property
    def medium_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.MEDIUM])
    
    @property
    def low_count(self) -> int:
        return len([v for v in self.vulnerabilities if v.severity == VulnerabilitySeverity.LOW])
    
    def add_vulnerability(self, vuln: Vulnerability):
        """Add vulnerability and update score"""
        self.vulnerabilities.append(vuln)
        
        # Update security score based on severity
        severity_penalty = {
            VulnerabilitySeverity.CRITICAL: 25,
            VulnerabilitySeverity.HIGH: 15,
            VulnerabilitySeverity.MEDIUM: 10,
            VulnerabilitySeverity.LOW: 5,
            VulnerabilitySeverity.INFO: 0,
        }
        
        penalty = severity_penalty.get(vuln.severity, 0)
        self.security_score = max(0, self.security_score - penalty)


class SecurityScanner:
    """
    Cross-platform WiFi security scanner.
    Performs passive security analysis without requiring special tools.
    """
    
    def __init__(self):
        self._is_scanning = False
        self._last_report: Optional[VulnerabilityReport] = None
    
    def analyze_network(self, network: NetworkInfo) -> VulnerabilityReport:
        """
        Analyze a network for security vulnerabilities.
        Cross-platform passive analysis.
        
        Args:
            network: NetworkInfo object to analyze
        
        Returns:
            VulnerabilityReport with findings
        """
        self._is_scanning = True
        
        report = VulnerabilityReport(
            target_bssid=network.bssid,
            target_ssid=network.ssid,
        )
        
        try:
            # Check encryption type
            self._check_encryption(network, report)
            
            # Check for WPS
            self._check_wps(network, report)
            
            # Check signal strength issues
            self._check_signal(network, report)
            
            # Check for hidden SSID
            self._check_hidden_ssid(network, report)
            
            # Check channel congestion
            self._check_channel(network, report)
            
            # Generate recommendations
            self._generate_recommendations(report)
            
            report.scan_completed = time.time()
            self._last_report = report
            
        finally:
            self._is_scanning = False
        
        return report
    
    def _check_encryption(self, network: NetworkInfo, report: VulnerabilityReport):
        """Check encryption security"""
        security = network.security.upper()
        
        # Open network
        if 'OPEN' in security or security == '' or security == 'NONE':
            report.add_vulnerability(Vulnerability(
                id="OPEN_NETWORK",
                name="Open Network (No Encryption)",
                description="Network has no encryption. All traffic is visible to anyone nearby.",
                severity=VulnerabilitySeverity.CRITICAL,
                category="Encryption",
                recommendation="Enable WPA2 or WPA3 encryption immediately.",
            ))
        
        # WEP encryption
        elif 'WEP' in security:
            report.add_vulnerability(Vulnerability(
                id="WEP_ENCRYPTION",
                name="WEP Encryption (Deprecated)",
                description="WEP encryption is severely broken and can be cracked in minutes.",
                severity=VulnerabilitySeverity.CRITICAL,
                category="Encryption",
                cve="CVE-2001-0131",
                recommendation="Upgrade to WPA2 or WPA3 encryption.",
            ))
        
        # WPA (version 1)
        elif 'WPA' in security and 'WPA2' not in security and 'WPA3' not in security:
            report.add_vulnerability(Vulnerability(
                id="WPA_ENCRYPTION",
                name="WPA Encryption (Outdated)",
                description="WPA1 has known vulnerabilities and should be upgraded.",
                severity=VulnerabilitySeverity.HIGH,
                category="Encryption",
                recommendation="Upgrade to WPA2 or WPA3 encryption.",
            ))
        
        # WPA2 with TKIP
        elif 'WPA2' in security and 'TKIP' in security:
            report.add_vulnerability(Vulnerability(
                id="WPA2_TKIP",
                name="WPA2 with TKIP (Weak)",
                description="TKIP cipher has known weaknesses. AES/CCMP is recommended.",
                severity=VulnerabilitySeverity.MEDIUM,
                category="Encryption",
                recommendation="Configure WPA2 to use AES/CCMP cipher only.",
            ))
        
        # WPA2 (good but check for PMKID)
        elif 'WPA2' in security:
            report.add_vulnerability(Vulnerability(
                id="WPA2_PMKID",
                name="WPA2 PMKID Attack Possible",
                description="WPA2 networks may be vulnerable to offline PMKID attacks.",
                severity=VulnerabilitySeverity.LOW,
                category="Encryption",
                cve="CVE-2018-14847",
                recommendation="Use strong, complex passwords and consider WPA3.",
            ))
        
        # WPA3 is good
        elif 'WPA3' in security:
            report.add_vulnerability(Vulnerability(
                id="WPA3_GOOD",
                name="WPA3 Encryption (Strong)",
                description="WPA3 provides strong encryption with SAE key exchange.",
                severity=VulnerabilitySeverity.INFO,
                category="Encryption",
                recommendation="Maintain WPA3 configuration.",
            ))
    
    def _check_wps(self, network: NetworkInfo, report: VulnerabilityReport):
        """Check WPS security"""
        if network.wps:
            report.add_vulnerability(Vulnerability(
                id="WPS_ENABLED",
                name="WPS Enabled",
                description="WPS PIN can be brute-forced, allowing network access.",
                severity=VulnerabilitySeverity.HIGH,
                category="Authentication",
                cve="CVE-2011-5053",
                recommendation="Disable WPS in router settings.",
            ))
    
    def _check_signal(self, network: NetworkInfo, report: VulnerabilityReport):
        """Check signal strength issues"""
        if network.signal >= -30:
            report.add_vulnerability(Vulnerability(
                id="SIGNAL_TOO_STRONG",
                name="Excessive Signal Strength",
                description="Strong signal extends beyond intended area, increasing attack surface.",
                severity=VulnerabilitySeverity.LOW,
                category="Physical Security",
                recommendation="Reduce transmit power to limit coverage area.",
            ))
    
    def _check_hidden_ssid(self, network: NetworkInfo, report: VulnerabilityReport):
        """Check hidden SSID security theater"""
        if network.hidden:
            report.add_vulnerability(Vulnerability(
                id="HIDDEN_SSID",
                name="Hidden SSID (False Security)",
                description="Hidden SSIDs provide no real security and are easily discovered.",
                severity=VulnerabilitySeverity.INFO,
                category="Misconfiguration",
                recommendation="Hidden SSIDs don't improve security. Focus on strong encryption.",
            ))
    
    def _check_channel(self, network: NetworkInfo, report: VulnerabilityReport):
        """Check channel configuration"""
        # 2.4 GHz overlapping channels
        if network.channel in [2, 3, 4, 5, 6, 7, 8, 9, 10]:
            if network.channel not in [1, 6, 11]:
                report.add_vulnerability(Vulnerability(
                    id="CHANNEL_OVERLAP",
                    name="Overlapping Channel",
                    description=f"Channel {network.channel} overlaps with adjacent channels.",
                    severity=VulnerabilitySeverity.INFO,
                    category="Configuration",
                    recommendation="Use non-overlapping channels: 1, 6, or 11 for 2.4GHz.",
                ))
    
    def _generate_recommendations(self, report: VulnerabilityReport):
        """Generate overall recommendations"""
        recommendations = []
        
        if report.critical_count > 0:
            recommendations.append("URGENT: Address critical vulnerabilities immediately.")
        
        if report.high_count > 0:
            recommendations.append("Address high-severity issues as soon as possible.")
        
        if report.security_score < 50:
            recommendations.append("Network security is poor. Major improvements needed.")
        elif report.security_score < 75:
            recommendations.append("Network security is fair. Some improvements recommended.")
        else:
            recommendations.append("Network security is good. Monitor for changes.")
        
        # Always recommend
        recommendations.append("Regularly update router firmware.")
        recommendations.append("Use strong, unique passwords.")
        recommendations.append("Enable network logging if available.")
        
        report.recommendations = recommendations
    
    def get_last_report(self) -> Optional[VulnerabilityReport]:
        """Get the last scan report"""
        return self._last_report
    
    @property
    def is_scanning(self) -> bool:
        """Check if scan is in progress"""
        return self._is_scanning


__all__ = [
    'SecurityScanner',
    'VulnerabilityReport',
    'Vulnerability',
    'VulnerabilitySeverity',
]
