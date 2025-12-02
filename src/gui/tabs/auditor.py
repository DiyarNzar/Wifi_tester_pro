"""
WiFi Tester Pro v6.0 - Auditor Tab
Security auditing and vulnerability assessment page
"""

import customtkinter as ctk
from typing import Optional
import time

from ...settings import Colors, Fonts, Layout, NetworkInfo, IS_KALI
from ...security.common import SecurityScanner, VulnerabilityReport, VulnerabilitySeverity
from ..utils import create_button, create_label, create_card


class VulnerabilityRow(ctk.CTkFrame):
    """Row displaying a single vulnerability"""
    
    def __init__(self, parent, vuln, **kwargs):
        super().__init__(
            parent,
            fg_color=Colors.SURFACE_DARK,
            corner_radius=8,
            **kwargs
        )
        
        self._vuln = vuln
        self._create_ui()
    
    def _create_ui(self):
        """Create vulnerability row UI"""
        # Severity indicator
        severity_colors = {
            VulnerabilitySeverity.CRITICAL: Colors.ERROR,
            VulnerabilitySeverity.HIGH: "#E67E22",
            VulnerabilitySeverity.MEDIUM: Colors.WARNING,
            VulnerabilitySeverity.LOW: Colors.SUCCESS,
            VulnerabilitySeverity.INFO: Colors.INFO,
        }
        
        color = severity_colors.get(self._vuln.severity, Colors.TEXT_MUTED)
        
        indicator = ctk.CTkFrame(
            self,
            width=6,
            fg_color=color,
            corner_radius=3
        )
        indicator.pack(side="left", fill="y", padx=(0, 10))
        
        # Content
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=10)
        
        # Header row
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x")
        
        ctk.CTkLabel(
            header,
            text=self._vuln.name,
            font=(Fonts.FAMILY, Fonts.SIZE_MD, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")
        
        severity_text = self._vuln.severity.name
        ctk.CTkLabel(
            header,
            text=severity_text,
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=color
        ).pack(side="right", padx=10)
        
        # Description
        ctk.CTkLabel(
            content,
            text=self._vuln.description,
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY,
            wraplength=500,
            anchor="w",
            justify="left"
        ).pack(fill="x", pady=(5, 0))
        
        # Recommendation
        if self._vuln.recommendation:
            rec_frame = ctk.CTkFrame(content, fg_color=Colors.SURFACE_MEDIUM, corner_radius=6)
            rec_frame.pack(fill="x", pady=(8, 0))
            
            ctk.CTkLabel(
                rec_frame,
                text=f"💡 {self._vuln.recommendation}",
                font=(Fonts.FAMILY, Fonts.SIZE_SM),
                text_color=Colors.TEXT_PRIMARY,
                wraplength=480,
                anchor="w",
                justify="left"
            ).pack(padx=10, pady=8)


class AuditorTab(ctk.CTkFrame):
    """
    Security auditor page.
    Analyzes networks for vulnerabilities.
    """
    
    def __init__(
        self,
        parent,
        driver=None,
        security=None,
        session=None,
        logger=None,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self._driver = driver
        self._security = security
        self._session = session
        self._logger = logger
        
        self._scanner = SecurityScanner()
        self._current_report: Optional[VulnerabilityReport] = None
        
        self._create_ui()
    
    def _create_ui(self):
        """Create auditor UI"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Content area
        self._create_content()
    
    def _create_header(self):
        """Create page header"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        create_label(header, text="Security Auditor", style="heading").pack(side="left")
        
        # Controls
        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.pack(side="right")
        
        # Network selector
        ctk.CTkLabel(
            controls,
            text="Target:",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY
        ).pack(side="left", padx=(0, 5))
        
        # Get networks from session
        networks = []
        if self._session:
            networks = [f"{n.get('ssid', 'Unknown')} ({n.get('bssid', '')})" 
                       for n in self._session.get_networks_list()]
        
        self._target_var = ctk.StringVar(value="Select a network")
        self._target_menu = ctk.CTkOptionMenu(
            controls,
            values=networks if networks else ["Scan networks first"],
            variable=self._target_var,
            width=250,
            fg_color=Colors.SURFACE_LIGHT,
            button_color=Colors.SURFACE_MEDIUM,
            button_hover_color=Colors.PRIMARY,
            dropdown_fg_color=Colors.SURFACE_DARK
        )
        self._target_menu.pack(side="left", padx=10)
        
        # Audit button
        self._audit_button = create_button(
            controls,
            text="Start Audit",
            icon="🔒",
            style="warning",
            width=130,
            command=self._start_audit
        )
        self._audit_button.pack(side="left", padx=5)
    
    def _create_content(self):
        """Create main content area"""
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)
        
        # Left: Vulnerabilities list
        self._create_vuln_list(content)
        
        # Right: Summary panel
        self._create_summary_panel(content)
    
    def _create_vuln_list(self, parent):
        """Create vulnerabilities list"""
        card = ctk.CTkFrame(parent, fg_color=Colors.SURFACE_MEDIUM, corner_radius=12)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        
        ctk.CTkLabel(
            header,
            text="Vulnerabilities",
            font=(Fonts.FAMILY, Fonts.SIZE_LG, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(side="left")
        
        # Scrollable list
        self._vuln_scroll = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent"
        )
        self._vuln_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Placeholder
        self._vuln_placeholder = ctk.CTkLabel(
            self._vuln_scroll,
            text="Select a network and click 'Start Audit'\nto analyze for vulnerabilities",
            font=(Fonts.FAMILY, Fonts.SIZE_MD),
            text_color=Colors.TEXT_MUTED
        )
        self._vuln_placeholder.pack(pady=100)
    
    def _create_summary_panel(self, parent):
        """Create audit summary panel"""
        card = ctk.CTkFrame(parent, fg_color=Colors.SURFACE_MEDIUM, corner_radius=12)
        card.grid(row=0, column=1, sticky="nsew")
        
        # Header
        ctk.CTkLabel(
            card,
            text="Audit Summary",
            font=(Fonts.FAMILY, Fonts.SIZE_LG, "bold"),
            text_color=Colors.TEXT_PRIMARY
        ).pack(anchor="w", padx=16, pady=(16, 8))
        
        # Score display
        self._score_frame = ctk.CTkFrame(card, fg_color=Colors.SURFACE_DARK, corner_radius=12)
        self._score_frame.pack(fill="x", padx=16, pady=10)
        
        self._score_label = ctk.CTkLabel(
            self._score_frame,
            text="--",
            font=(Fonts.FAMILY, 48, "bold"),
            text_color=Colors.TEXT_MUTED
        )
        self._score_label.pack(pady=20)
        
        ctk.CTkLabel(
            self._score_frame,
            text="Security Score",
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY
        ).pack(pady=(0, 15))
        
        # Stats
        stats_frame = ctk.CTkFrame(card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=16, pady=10)
        
        self._stat_critical = self._create_stat_item(stats_frame, "Critical", "0", Colors.ERROR)
        self._stat_high = self._create_stat_item(stats_frame, "High", "0", "#E67E22")
        self._stat_medium = self._create_stat_item(stats_frame, "Medium", "0", Colors.WARNING)
        self._stat_low = self._create_stat_item(stats_frame, "Low", "0", Colors.SUCCESS)
        
        # Kali notice
        if not IS_KALI:
            notice = ctk.CTkFrame(card, fg_color=Colors.SURFACE_DARK, corner_radius=8)
            notice.pack(fill="x", padx=16, pady=10)
            
            ctk.CTkLabel(
                notice,
                text="ℹ️ Running in basic mode.\nFull security features require Kali Linux.",
                font=(Fonts.FAMILY, Fonts.SIZE_SM),
                text_color=Colors.TEXT_SECONDARY,
                justify="center"
            ).pack(pady=15)
    
    def _create_stat_item(self, parent, label: str, value: str, color: str):
        """Create a stat item row"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=3)
        
        # Indicator
        ctk.CTkFrame(frame, width=12, height=12, fg_color=color, corner_radius=6).pack(side="left")
        
        # Label
        ctk.CTkLabel(
            frame,
            text=label,
            font=(Fonts.FAMILY, Fonts.SIZE_SM),
            text_color=Colors.TEXT_SECONDARY
        ).pack(side="left", padx=10)
        
        # Value
        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=(Fonts.FAMILY, Fonts.SIZE_MD, "bold"),
            text_color=Colors.TEXT_PRIMARY
        )
        value_label.pack(side="right")
        
        return value_label
    
    # ==========================================================================
    # Actions
    # ==========================================================================
    
    def _start_audit(self):
        """Start security audit"""
        target = self._target_var.get()
        
        if "Select" in target or "Scan" in target:
            from ..utils import show_message
            show_message("Audit", "Please select a network to audit", "warning")
            return
        
        # Extract BSSID from selection
        try:
            bssid = target.split("(")[1].rstrip(")")
        except:
            self._logger.error("Invalid target selection", "Auditor")
            return
        
        # Get network info
        network_data = self._session.get_network(bssid) if self._session else None
        
        if not network_data:
            from ..utils import show_message
            show_message("Audit", "Network not found. Try scanning again.", "error")
            return
        
        # Convert to NetworkInfo
        network = NetworkInfo(**network_data)
        
        self._logger.info(f"Starting audit: {network.ssid}", "Auditor")
        
        # Clear previous results
        for widget in self._vuln_scroll.winfo_children():
            widget.destroy()
        
        # Show scanning status
        ctk.CTkLabel(
            self._vuln_scroll,
            text="Analyzing...",
            font=(Fonts.FAMILY, Fonts.SIZE_MD),
            text_color=Colors.TEXT_MUTED
        ).pack(pady=50)
        
        # Perform audit
        self.after(100, lambda: self._perform_audit(network))
    
    def _perform_audit(self, network: NetworkInfo):
        """Perform the security audit"""
        try:
            report = self._scanner.analyze_network(network)
            self._current_report = report
            self._display_results(report)
            
            self._logger.info(
                f"Audit complete: Score {report.security_score}, "
                f"{len(report.vulnerabilities)} issues found",
                "Auditor"
            )
        except Exception as e:
            self._logger.error(f"Audit error: {e}", "Auditor")
            for widget in self._vuln_scroll.winfo_children():
                widget.destroy()
            
            ctk.CTkLabel(
                self._vuln_scroll,
                text=f"Audit failed: {e}",
                font=(Fonts.FAMILY, Fonts.SIZE_MD),
                text_color=Colors.ERROR
            ).pack(pady=50)
    
    def _display_results(self, report: VulnerabilityReport):
        """Display audit results"""
        # Clear placeholder
        for widget in self._vuln_scroll.winfo_children():
            widget.destroy()
        
        # Display vulnerabilities
        if report.vulnerabilities:
            for vuln in report.vulnerabilities:
                VulnerabilityRow(self._vuln_scroll, vuln).pack(fill="x", pady=3)
        else:
            ctk.CTkLabel(
                self._vuln_scroll,
                text="No vulnerabilities found",
                font=(Fonts.FAMILY, Fonts.SIZE_MD),
                text_color=Colors.SUCCESS
            ).pack(pady=50)
        
        # Update summary
        score = report.security_score
        if score >= 80:
            score_color = Colors.SUCCESS
        elif score >= 50:
            score_color = Colors.WARNING
        else:
            score_color = Colors.ERROR
        
        self._score_label.configure(text=str(score), text_color=score_color)
        
        # Update stats
        self._stat_critical.configure(text=str(report.critical_count))
        self._stat_high.configure(text=str(report.high_count))
        self._stat_medium.configure(text=str(report.medium_count))
        self._stat_low.configure(text=str(report.low_count))
    
    def on_show(self):
        """Called when page is shown"""
        # Refresh network list
        if self._session:
            networks = [f"{n.get('ssid', 'Unknown')} ({n.get('bssid', '')})" 
                       for n in self._session.get_networks_list()]
            
            if networks:
                self._target_menu.configure(values=networks)
            else:
                self._target_menu.configure(values=["Scan networks first"])
                self._target_var.set("Scan networks first")


__all__ = ['AuditorTab']
