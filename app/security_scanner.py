# app/security_scanner.py

import subprocess
import platform
import os

class SecurityScanner:
    def scan(self):
        findings = []

        system = platform.system().lower()

        if system == "linux":
            findings.extend(self._linux_scan())
        elif system == "windows":
            findings.extend(self._windows_scan())
        elif system == "darwin":
            findings.extend(self._macos_scan())
        else:
            findings.append({"type": "info", "details": "Security scanning not implemented for this OS."})

        return findings

    def _linux_scan(self):
        results = []

        # ClamAV scan
        if self._command_exists("clamscan"):
            try:
                output = subprocess.check_output(
                    ["clamscan", "-r", "--infected", "/"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=300
                )
                if "FOUND" in output:
                    results.append({
                        "type": "virus",
                        "details": output
                    })
            except subprocess.TimeoutExpired:
                results.append({
                    "type": "scanner_error",
                    "details": "ClamAV scan timed out"
                })
            except Exception as e:
                results.append({
                    "type": "scanner_error",
                    "details": str(e)
                })
        else:
            results.append({"type": "info", "details": "ClamAV not installed."})

        # chkrootkit
        if self._command_exists("chkrootkit"):
            try:
                output = subprocess.check_output(
                    ["chkrootkit"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=120
                )
                if "INFECTED" in output or "WARNING" in output:
                    results.append({
                        "type": "rootkit",
                        "details": output
                    })
            except Exception as e:
                results.append({
                    "type": "scanner_error",
                    "details": f"chkrootkit error: {e}"
                })
        else:
            results.append({"type": "info", "details": "chkrootkit not installed."})

        # Lynis
        if self._command_exists("lynis"):
            try:
                output = subprocess.check_output(
                    ["lynis", "audit", "system"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=300
                )
                results.append({
                    "type": "audit",
                    "details": output
                })
            except Exception as e:
                results.append({
                    "type": "scanner_error",
                    "details": f"Lynis error: {e}"
                })
        else:
            results.append({"type": "info", "details": "Lynis not installed."})

        return results

    def _windows_scan(self):
        results = []
        try:
            # Check Windows Defender status
            cmd = [
                "powershell",
                "-Command",
                "Get-MpThreatDetection"
            ]
            output = subprocess.check_output(
                cmd,
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=120
            )
            if output.strip():
                results.append({
                    "type": "virus",
                    "details": output
                })
            else:
                results.append({
                    "type": "info",
                    "details": "Windows Defender found no threats."
                })

        except subprocess.CalledProcessError as e:
            results.append({
                "type": "scanner_error",
                "details": f"Windows scan failed: {e}"
            })
        except FileNotFoundError:
            results.append({
                "type": "info",
                "details": "Windows Defender not available or PowerShell missing."
            })

        return results

    def _macos_scan(self):
        results = []

        # ClamAV
        if self._command_exists("clamscan"):
            try:
                output = subprocess.check_output(
                    ["clamscan", "-r", "--infected", "/"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                    timeout=300
                )
                if "FOUND" in output:
                    results.append({
                        "type": "virus",
                        "details": output
                    })
            except subprocess.TimeoutExpired:
                results.append({
                    "type": "scanner_error",
                    "details": "ClamAV scan timed out"
                })
            except Exception as e:
                results.append({
                    "type": "scanner_error",
                    "details": str(e)
                })
        else:
            results.append({"type": "info", "details": "ClamAV not installed."})

        # Check Gatekeeper status
        try:
            spctl_status = subprocess.check_output(
                ["spctl", "--status"],
                text=True,
                stderr=subprocess.DEVNULL
            )
            results.append({
                "type": "gatekeeper",
                "details": spctl_status.strip()
            })
        except Exception as e:
            results.append({
                "type": "scanner_error",
                "details": f"Gatekeeper check error: {e}"
            })

        # Check System Integrity Protection (SIP) status
        if self._command_exists("csrutil"):
            try:
                csrutil_status = subprocess.check_output(
                    ["csrutil", "status"],
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                results.append({
                    "type": "sip",
                    "details": csrutil_status.strip()
                })
            except Exception as e:
                results.append({
                    "type": "scanner_error",
                    "details": f"SIP check error: {e}"
                })

        return results

    def _command_exists(self, command):
        """Check if a command exists in PATH."""
        return subprocess.call(
            ["which", command],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ) == 0
