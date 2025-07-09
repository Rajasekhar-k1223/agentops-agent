# agentops/log_collector.py

import os
import subprocess
import platform
import datetime
import json
import win32evtlog
import win32api
import win32security

class LogCollector:
    def collect_logs(self):
        raise NotImplementedError


class LinuxLogCollector(LogCollector):
    LINUX_LOG_FILES = [
        "/var/log/syslog",
        "/var/log/messages",
        "/var/log/auth.log",
        "/var/log/secure",
        "/var/log/kern.log",
        "/var/log/dmesg",
        "/var/log/cron",
        "/var/log/fail2ban.log",
        "/var/log/ufw.log",
    ]

    def collect_logs(self):
        logs = ""
        for f in self.LINUX_LOG_FILES:
            if os.path.exists(f):
                logs += self._tail_file(f)
        try:
            logs += "\n=== journalctl ===\n"
            logs += subprocess.check_output(
                ["journalctl", "-n", "5000"],
                text=True,
                stderr=subprocess.DEVNULL
            )
        except:
            logs += "\n[journalctl not available]\n"
        return logs

    def _tail_file(self, path, lines=5000):
        try:
            output = subprocess.check_output(
                ["tail", "-n", str(lines), path],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            return f"\n=== {path} ===\n{output}"
        except Exception as e:
            return f"\n=== {path} ===\nERROR: {e}\n"


class MacOSLogCollector(LogCollector):
    def collect_logs(self):
        try:
            output = subprocess.check_output(
                ["log", "show", "--last", "1m", "--info"],
                text=True,
                stderr=subprocess.STDOUT
            )
            if not output.strip():
                return "No macOS logs found in the past 1 Min."
            return output
        except subprocess.CalledProcessError as e:
            return f"macOS logs error: {e.output}"
        except Exception as e:
            return f"macOS logs error: {e}"



class WindowsLogCollector(LogCollector):
    def __init__(self):
        self._try_enable_security_privilege()

    def list_all_event_logs(self):
        logs = []
        try:
            result = subprocess.run(["wevtutil", "el"], capture_output=True, text=True, check=True)
            logs = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        except Exception as e:
            logs.append(f"Failed to list logs: {str(e)}")
        return logs

    def _try_enable_security_privilege(self):
        try:
            hToken = win32security.OpenProcessToken(
                win32api.GetCurrentProcess(),
                win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY
            )
            privilege_id = win32security.LookupPrivilegeValue(None, "SeSecurityPrivilege")
            win32security.AdjustTokenPrivileges(
                hToken,
                False,
                [(privilege_id, win32security.SE_PRIVILEGE_ENABLED)]
            )
            print("[+] SeSecurityPrivilege enabled.")
        except Exception as e:
            print(f"[-] Could not enable SeSecurityPrivilege: {e}")

    def _split_logs_by_category(self, logs):
        categories = {
            "WindowsLogs": [],
            "ApplicationAndServicesLogs": [],
            "CustomViews": []
        }
        for log in logs:
            if "Custom Views" in log:
                categories["CustomViews"].append(log)
            elif "Microsoft-Windows" in log or "\\" in log:
                categories["ApplicationAndServicesLogs"].append(log)
            else:
                categories["WindowsLogs"].append(log)
        return categories

    def collect_logs(self, minutes_back=5):
        log_entries = []
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=minutes_back)
        all_logs = self.list_all_event_logs()
        categorized_logs = self._split_logs_by_category(all_logs)

        start_time = datetime.datetime.now()
        timeout_seconds = 60

        for category, logs in categorized_logs.items():
            for log_name in logs:
                # Check if we've hit the timeout
                elapsed = (datetime.datetime.now() - start_time).total_seconds()
                if elapsed > timeout_seconds:
                    print("[!] Timeout reached. Stopping log collection.")
                    log_entries.append({
                        "category": "Timeout",
                        "message": f"Stopped log collection after {elapsed:.2f} seconds."
                    })
                    return log_entries

                #print(f"Collecting one record from {log_name} in category {category}")
                try:
                    handle = win32evtlog.OpenEventLog(None, log_name)
                except Exception as e:
                    log_entries.append({
                        "category": category,
                        "log_type": log_name,
                        "error": f"Failed to open log: {str(e)}"
                    })
                    continue

                flags = (
                    win32evtlog.EVENTLOG_BACKWARDS_READ |
                    win32evtlog.EVENTLOG_SEQUENTIAL_READ
                )

                try:
                    events = win32evtlog.ReadEventLog(handle, flags, 0)
                except Exception as e:
                    log_entries.append({
                        "category": category,
                        "log_type": log_name,
                        "error": f"Failed to read log: {str(e)}"
                    })
                    continue
                if events:
                    for ev in events:
                        event_time = ev.TimeGenerated
                        if event_time >= cutoff_time:
                            log_entry = {
                                "category": category,
                                "log_type": log_name,
                                "timestamp": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                                "event_id": ev.EventID & 0xFFFF,
                                "event_id_raw": ev.EventID,
                                "source_name": ev.SourceName,
                                "event_category": ev.EventCategory,
                                "event_type": self._get_event_type(ev.EventType),
                                "message": "; ".join(str(s) for s in ev.StringInserts) if ev.StringInserts else ""
                            }
                           # print(log_entry)
                            log_entries.append(log_entry)
                        else:
                            log_entries.append({
                                "category": category,
                                "log_type": log_name,
                                "message": "No recent events in last N minutes."
                            })
                else:
                    log_entries.append({
                        "category": category,
                        "log_type": log_name,
                        "message": "Log has no events."
                    })


                try:
                    win32evtlog.CloseEventLog(handle)
                except Exception as e:
                    log_entries.append({
                        "category": category,
                        "log_type": log_name,
                        "error": f"Close handle failed: {str(e)}"
                    })

        # Add other logs from Windows Update and Defender
        log_entries.extend(self._get_windows_update_logs(minutes_back))
        log_entries.extend(self._get_defender_logs(minutes_back))

        return log_entries

    def _get_event_type(self, event_type_id):
        event_types = {
            0x0001: "Error",
            0x0002: "Warning",
            0x0004: "Information",
            0x0008: "Success Audit",
            0x0010: "Failure Audit"
        }
        return event_types.get(event_type_id, f"Unknown ({event_type_id})")

    def _run_powershell_json(self, ps_script, log_type):
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                return [{"log_type": log_type, "error": result.stderr.strip()}]

            output = result.stdout.strip()
            if not output:
                return []

            data = json.loads(output)
            if isinstance(data, dict):
                data = [data]

            for entry in data:
                entry["log_type"] = log_type
            return data
        except Exception as e:
            return [{"log_type": log_type, "error": f"PowerShell error: {str(e)}"}]

    def _get_windows_update_logs(self, minutes_back):
        cutoff_iso = (datetime.datetime.now() - datetime.timedelta(minutes=minutes_back)).strftime("%Y-%m-%dT%H:%M:%S")
        ps_script = f"""
        Get-WinEvent -LogName "Microsoft-Windows-WindowsUpdateClient/Operational" |
        Where-Object {{ $_.TimeCreated -gt [datetime]::Parse('{cutoff_iso}') }} |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Compress
        """
        return self._run_powershell_json(ps_script, "WindowsUpdateClient")

    def _get_defender_logs(self, minutes_back):
        cutoff_iso = (datetime.datetime.now() - datetime.timedelta(minutes=minutes_back)).strftime("%Y-%m-%dT%H:%M:%S")
        ps_script = f"""
        Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" |
        Where-Object {{ $_.TimeCreated -gt [datetime]::Parse('{cutoff_iso}') }} |
        Select-Object TimeCreated, Id, LevelDisplayName, ProviderName, Message |
        ConvertTo-Json -Compress
        """
        return self._run_powershell_json(ps_script, "WindowsDefender")