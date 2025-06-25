import platform
import os
import socket
import psutil
import subprocess
import logging

def get_basic_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "cpu": platform.processor(),
        "ram_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2)
    }

def get_installed_packages():
    try:
        if platform.system() == "Linux":
            result = subprocess.check_output("dpkg -l", shell=True, text=True)
        elif platform.system() == "Windows":
            result = subprocess.check_output("powershell -Command \"Get-WmiObject -Class Win32_Product | Select-Object Name\"", shell=True, text=True)
        else:
            result = subprocess.check_output("pip list", shell=True, text=True)
        return result
    except Exception as e:
        logging.error(f"Failed to get installed packages: {e}")
        return str(e)

def get_running_services():
    try:
        os_type = platform.system()

        if os_type == "Linux":
            result = subprocess.check_output(
                "systemctl list-units --type=service --state=running",
                shell=True, text=True
            )

        elif os_type == "Windows":
            result = subprocess.check_output(
                "sc query type= service state= all",
                shell=True, text=True
            )

        elif os_type == "Darwin":  # macOS
            result = subprocess.check_output(
                "launchctl list",
                shell=True, text=True
            )

        else:
            result = f"Service listing not supported on OS: {os_type}"

        return result

    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed with return code {e.returncode}: {e.output}")
        return f"Command error: {e.output}"

    except Exception as e:
        logging.error(f"Failed to get running services: {e}")
        return str(e)


def get_log_contents(log_path="agent.log", max_lines=100):
    try:
        with open(log_path, "r") as file:
            lines = file.readlines()[-max_lines:]
        return "".join(lines)
    except Exception as e:
        logging.error(f"Failed to read log file: {e}")
        return str(e)
def get_live_background_services():
    services = []

    try:
        if platform.system() == "Windows":
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                if proc.info['status'] == psutil.STATUS_RUNNING:
                    services.append(proc.info)
        else:
            # For Linux/macOS
            for proc in psutil.process_iter(['pid', 'name']):
                services.append(proc.info)

        return services
    except Exception as e:
        return f"Error retrieving services: {e}"