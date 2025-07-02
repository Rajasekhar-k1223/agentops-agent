# app/error_detector.py

import re

class ErrorDetector:
    def __init__(self):
        """
        Initialize the error detector with regex patterns
        for various error types and severities.
        """
        self.patterns = [
            # Generic errors
            (r"\b(error|failed|fail|exception|critical|fatal|panic)\b", "error"),
            
            # Warnings
            (r"\b(warning|warn)\b", "warning"),

            # Authentication / security failures
            (r"authentication failure", "security"),
            (r"invalid user", "security"),
            (r"failed password", "security"),
            (r"sudo: .*authentication", "security"),
            (r"permission denied", "security"),

            # Linux kernel issues
            (r"segfault", "critical"),
            (r"kernel panic", "critical"),
            (r"out of memory", "critical"),

            # Windows-specific issues
            (r"faulting application", "error"),
            (r"blue screen", "critical"),
            (r"bugcheck", "critical"),

            # macOS specific issues
            (r"kernel trap", "critical"),
            (r"panic\(cpu", "critical"),

            # Docker / Kubernetes
            (r"container exited with", "error"),
            (r"crashloopbackoff", "error"),

            # Web servers
            (r"500 internal server error", "error"),
            (r"502 bad gateway", "error"),
            (r"503 service unavailable", "error"),

            # Database errors (examples)
            (r"ORA-\d+", "error"),        # Oracle DB errors
            (r"mysql.*error", "error"),
            (r"postgres.*ERROR", "error"),
        ]

    def extract_errors(self, logs, source="unknown"):
        """
        Scan the provided log text for suspicious or error lines.

        Returns a list of:
            {
                "source": ...,
                "message": ...,
                "severity": ...
            }
        """
        errors = []
        lines = logs.splitlines()

        for line in lines:
            result = self._check_line(line)
            if result:
                errors.append({
                    "source": source,
                    "message": line.strip(),
                    "severity": result
                })

        return errors

    def _check_line(self, line):
        """
        Check if a log line matches known error patterns.
        Returns severity if matched, otherwise None.
        """
        text = line.lower()

        for pattern, severity in self.patterns:
            if re.search(pattern, text):
                return severity

        return None
