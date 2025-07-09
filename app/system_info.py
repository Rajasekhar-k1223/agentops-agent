# # app/system_info.py

# import platform
# import socket
# import psutil
# import subprocess
# import os
# import glob
# import winreg

# def get_basic_info():
#     """
#     Gather basic machine info:
#     - hostname
#     - OS name + version
#     - architecture
#     - CPU name
#     - memory size
#     """
#     return {
#         "hostname": socket.gethostname(),
#         "os": platform.system(),
#         "os_version": platform.version(),
#         "architecture": platform.machine(),
#         "cpu": platform.processor(),
#         "memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
#         "cpu_count": psutil.cpu_count(),
#         "cpu_percent": psutil.cpu_percent(interval=1),
#         "memory_total_MB": round(psutil.virtual_memory().total / 1024 / 1024, 2),
#         "memory_used_MB": round(psutil.virtual_memory().used / 1024 / 1024, 2),
#         "disk_usage_percent": psutil.disk_usage('/').percent,
#         "ip_address": socket.gethostbyname(socket.gethostname())
#     }

# def get_installed_packages():
#     """
#     Attempt to gather installed software depending on OS.
#     - On Linux: dpkg, rpm, or flatpak
#     - On Windows: wmic
#     - On macOS: brew list or system_profiler
#     """
#     system = platform.system().lower()
#     packages = []

#     try:
#         if system == "linux":
#             if os.path.exists("/usr/bin/dpkg"):
#                 output = subprocess.check_output(["dpkg", "-l"], text=True, stderr=subprocess.DEVNULL)
#                 packages = parse_dpkg_output(output)
#             elif os.path.exists("/usr/bin/rpm"):
#                 output = subprocess.check_output(["rpm", "-qa"], text=True, stderr=subprocess.DEVNULL)
#                 packages = output.splitlines()
#         elif system == "windows":
#             # output = subprocess.check_output(
#             #     ["wmic", "product", "get", "name","version"],
#             #     text=True,
#             #     stderr=subprocess.DEVNULL,
#             # )
#             # packages = parse_windows_wmic_output(output)
#             """
#             Retrieve installed software from Windows registry.
#             Works on all modern Windows versions.
#             """
#             uninstall_keys = [
#                 r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
#                 r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
#             ]

#             programs = []

#             for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
#                 for key_path in uninstall_keys:
#                     try:
#                         reg_key = winreg.OpenKey(root, key_path)
#                         for i in range(winreg.QueryInfoKey(reg_key)[0]):
#                             subkey_name = winreg.EnumKey(reg_key, i)
#                             subkey_path = key_path + "\\" + subkey_name
#                             try:
#                                 subkey = winreg.OpenKey(root, subkey_path)
#                                 name, _ = winreg.QueryValueEx(subkey, "DisplayName")
#                                 try:
#                                     version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
#                                 except FileNotFoundError:
#                                     version = "Unknown"
#                                 programs.append(f"{name} {version}")
#                             except FileNotFoundError:
#                                 continue
#                     except FileNotFoundError:
#                         continue

#             return programs
#         elif system == "darwin":
#             # macOS
#             if os.path.exists("/opt/homebrew/bin/brew"):
#                 output = subprocess.check_output(
#                     ["/opt/homebrew/bin/brew", "list"],
#                     text=True,
#                     stderr=subprocess.DEVNULL,
#                 )
#                 packages = output.splitlines()
#             else:
#                 output = subprocess.check_output(
#                     ["system_profiler", "SPApplicationsDataType"],
#                     text=True,
#                     stderr=subprocess.DEVNULL,
#                 )
#                 packages = parse_macos_system_profiler(output)

#     except Exception as e:
#         packages = [f"error retrieving packages: {str(e)}"]

#     return packages

# def parse_dpkg_output(output):
#     """
#     Parse output of dpkg -l
#     """
#     pkgs = []
#     for line in output.splitlines():
#         if line.startswith("ii "):
#             tokens = line.split()
#             if len(tokens) >= 3:
#                 pkgs.append(f"{tokens[1]} {tokens[2]}")
#     return pkgs

# def parse_windows_wmic_output(output):
#     """
#     Parse wmic product list output
#     """
#     pkgs = []
#     lines = output.strip().splitlines()
#     for line in lines[1:]:
#         line = line.strip()
#         if line:
#             pkgs.append(line)
#     return pkgs

# def parse_macos_system_profiler(output):
#     """
#     Parse system_profiler output to list installed apps.
#     """
#     pkgs = []
#     current_app = ""
#     for line in output.splitlines():
#         if line.startswith("        "):
#             current_app += line.strip() + " "
#         else:
#             if current_app:
#                 pkgs.append(current_app.strip())
#             current_app = line.strip()
#     if current_app:
#         pkgs.append(current_app.strip())
#     return pkgs

# def get_running_services():
#     """
#     List running processes.
#     """
#     services = []
#     try:
#         for proc in psutil.process_iter(attrs=['pid', 'name']):
#             services.append({
#                 "pid": proc.info['pid'],
#                 "name": proc.info['name'],
#             })
#     except Exception as e:
#         services.append({"error": str(e)})
#     return services

# def get_live_background_services():
#     """
#     List live background processes.
#     """
#     try:
#         return [p.info for p in psutil.process_iter(attrs=['pid', 'name']) if p.info['pid'] != 0]
#     except Exception as e:
#         return str(e)

# def get_log_contents():
#     """
#     Read logs for Linux, Windows, macOS
#     """
#     system = platform.system().lower()
#     logs = ""

#     if system == "linux":
#         logs = collect_linux_logs()
#     elif system == "windows":
#         logs = collect_windows_logs()
#     elif system == "darwin":
#         logs = collect_macos_logs()

#     return logs

# def collect_linux_logs():
#     log_files = [
#         "/var/log/syslog",
#         "/var/log/messages",
#         "/var/log/auth.log",
#         "/var/log/secure",
#         "/var/log/kern.log",
#         "/var/log/cron",
#         "/var/log/fail2ban.log",
#         "/var/log/ufw.log",
#         "/var/log/apache2/*.log",
#         "/var/log/nginx/*.log",
#         "/var/log/mysql/*.log",
#         "/var/log/mariadb/*.log",
#         "/var/log/mongodb/*.log",
#         "/var/log/php7.4-fpm.log",
#         "/var/log/mail.log",
#         "/var/log/postgresql/*.log",
#         "/var/log/docker.log",
#         "/var/log/samba/*.log",
#         "/var/log/squid/*.log",
#         "/var/log/pacemaker.log",
#         "/var/log/libvirt/*.log",
#         "/var/log/haproxy.log",
#     ]
#     logs = []
#     for path in log_files:
#         for f in glob.glob(path):
#             try:
#                 with open(f, "r", errors="ignore") as file:
#                     lines = file.readlines()[-1000:]  # only last 1000 lines
#                     logs.append(f"==> {f} <==\n" + "".join(lines))
#             except Exception as e:
#                 logs.append(f"Error reading {f}: {str(e)}")

#     return "\n".join(logs)

# def collect_windows_logs():
#     logs = []
#     try:
#         output = subprocess.check_output(
#             ["wevtutil", "qe", "System", "/c:50", "/f:text"],
#             text=True,
#             stderr=subprocess.DEVNULL
#         )
#         logs.append(output)
#     except Exception as e:
#         logs.append(f"Error reading Windows logs: {str(e)}")
#     return "\n".join(logs)

# def collect_macos_logs():
#     logs = []
#     try:
#         output = subprocess.check_output(
#             ["log", "show", "--predicate", "eventType == logEvent", "--last", "1h"],
#             text=True,
#             stderr=subprocess.DEVNULL,
#         )
#         logs.append(output)
#     except Exception as e:
#         logs.append(f"Error reading macOS logs: {str(e)}")
#     return "\n".join(logs)

# app/system_info.py

import platform
import socket
import psutil
import subprocess
import os
import glob
import sys

def get_basic_info():
    """
    Gather basic machine info.
    """
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu": platform.processor(),
        "memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total_MB": round(psutil.virtual_memory().total / 1024 / 1024, 2),
        "memory_used_MB": round(psutil.virtual_memory().used / 1024 / 1024, 2),
        "disk_usage_percent": psutil.disk_usage('/').percent,
        "ip_address": socket.gethostbyname(socket.gethostname())
    }

def get_installed_packages():
    """
    Gather installed packages across OS:
    - Linux → dpkg, rpm
    - Windows → winreg
    - macOS → brew or system_profiler
    Always returns list of dicts: [{name, version}]
    """
    system = platform.system().lower()
    packages = []

    try:
        if system == "linux":
            if os.path.exists("/usr/bin/dpkg"):
                output = subprocess.check_output(
                    ["dpkg", "-l"],
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                packages = parse_dpkg_output(output)
            elif os.path.exists("/usr/bin/rpm"):
                output = subprocess.check_output(
                    ["rpm", "-qa"],
                    text=True,
                    stderr=subprocess.DEVNULL
                )
                packages = [{"name": line, "version": None} for line in output.splitlines()]

        elif system == "windows":
            # Import winreg only if on Windows
            import winreg

            uninstall_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ]

            programs = []
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                for key_path in uninstall_keys:
                    try:
                        reg_key = winreg.OpenKey(root, key_path)
                        for i in range(winreg.QueryInfoKey(reg_key)[0]):
                            subkey_name = winreg.EnumKey(reg_key, i)
                            subkey_path = key_path + "\\" + subkey_name
                            try:
                                subkey = winreg.OpenKey(root, subkey_path)
                                name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                                try:
                                    version, _ = winreg.QueryValueEx(subkey, "DisplayVersion")
                                except FileNotFoundError:
                                    version = None
                                programs.append({
                                    "name": name,
                                    "version": version
                                })
                            except FileNotFoundError:
                                continue
                    except FileNotFoundError:
                        continue

            packages = programs

        elif system == "darwin":
            # macOS
            if os.path.exists("/opt/homebrew/bin/brew"):
                output = subprocess.check_output(
                    ["/opt/homebrew/bin/brew", "list"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                packages = [{"name": line, "version": None} for line in output.splitlines()]
            else:
                output = subprocess.check_output(
                    ["system_profiler", "SPApplicationsDataType"],
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                packages = parse_macos_system_profiler(output)

    except Exception as e:
        packages = [{"name": f"error retrieving packages: {str(e)}", "version": None}]

    return packages


def parse_dpkg_output(output):
    """
    Parse dpkg -l output.
    """
    pkgs = []
    for line in output.splitlines():
        if line.startswith("ii "):
            tokens = line.split()
            if len(tokens) >= 3:
                pkgs.append({
                    "name": tokens[1],
                    "version": tokens[2]
                })
    return pkgs


def parse_macos_system_profiler(output):
    """
    Parse macOS system_profiler output into list of dicts.
    """
    pkgs = []
    current_app = ""
    for line in output.splitlines():
        if line.startswith("        "):
            current_app += line.strip() + " "
        else:
            if current_app:
                pkgs.append({"name": current_app.strip(), "version": None})
            current_app = line.strip()
    if current_app:
        pkgs.append({"name": current_app.strip(), "version": None})
    return pkgs


def get_running_services():
    """
    List running processes.
    """
    services = []
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            services.append({
                "pid": proc.info['pid'],
                "name": proc.info['name'],
            })
    except Exception as e:
        services.append({"error": str(e)})
    return services


def get_live_background_services():
    """
    List live background processes.
    """
    try:
        return [p.info for p in psutil.process_iter(attrs=['pid', 'name']) if p.info['pid'] != 0]
    except Exception as e:
        return str(e)


def get_log_contents():
    """
    Gather logs across platforms.
    """
    system = platform.system().lower()
    logs = ""

    if system == "linux":
        logs = collect_linux_logs()
    elif system == "windows":
        logs = collect_windows_logs()
    elif system == "darwin":
        logs = collect_macos_logs()

    return logs


def collect_linux_logs():
    log_files = [
        "/var/log/syslog",
        "/var/log/messages",
        "/var/log/auth.log",
        "/var/log/secure",
        "/var/log/kern.log",
        "/var/log/cron",
        "/var/log/fail2ban.log",
        "/var/log/ufw.log",
        "/var/log/apache2/*.log",
        "/var/log/nginx/*.log",
        "/var/log/mysql/*.log",
        "/var/log/mariadb/*.log",
        "/var/log/mongodb/*.log",
        "/var/log/php7.4-fpm.log",
        "/var/log/mail.log",
        "/var/log/postgresql/*.log",
        "/var/log/docker.log",
        "/var/log/samba/*.log",
        "/var/log/squid/*.log",
        "/var/log/pacemaker.log",
        "/var/log/libvirt/*.log",
        "/var/log/haproxy.log",
    ]
    logs = []
    for path in log_files:
        for f in glob.glob(path):
            try:
                with open(f, "r", errors="ignore") as file:
                    lines = file.readlines()[-1000:]  # last 1000 lines
                    logs.append(f"==> {f} <==\n" + "".join(lines))
            except Exception as e:
                logs.append(f"Error reading {f}: {str(e)}")

    return "\n".join(logs)


def collect_windows_logs():
    logs = []
    try:
        output = subprocess.check_output(
            ["wevtutil", "qe", "System", "/c:50", "/f:text"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        logs.append(output)
    except Exception as e:
        logs.append(f"Error reading Windows logs: {str(e)}")
    return "\n".join(logs)


def collect_macos_logs():
    logs = []
    try:
        output = subprocess.check_output(
            ["log", "show", "--predicate", "eventType == logEvent", "--last", "1h"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        logs.append(output)
    except Exception as e:
        logs.append(f"Error reading macOS logs: {str(e)}")
    return "\n".join(logs)
