# agentops/log_collector.py

import os
import subprocess
import platform

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
    def collect_logs(self):
        logs = ""
        try:
            import win32evtlog

            for log_name in ["System", "Application", "Security"]:
                logs += f"\n=== {log_name} ===\n"
                handle = win32evtlog.OpenEventLog(None, log_name)
                flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
                total = 0
                while True:
                    events = win32evtlog.ReadEventLog(handle, flags, 0)
                    if not events:
                        break
                    for ev in events:
                        logs += f"{ev.TimeGenerated} - {ev.SourceName}: {ev.EventID} - {ev.StringInserts}\n"
                        total += 1
                        if total >= 5000:
                            break
                    if total >= 5000:
                        break
        except Exception as e:
            logs += f"Windows logs error: {e}"
        return logs
