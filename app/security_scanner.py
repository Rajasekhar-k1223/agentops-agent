import subprocess
import platform
import shutil

def run_command(command: str):
    try:
        return subprocess.check_output(command, shell=True, text=True)
    except subprocess.CalledProcessError as e:
        return f"Command error: {e.output}"
    except Exception as e:
        return str(e)

def run_clamav_scan():
    if not shutil.which("clamscan"):
        return "ClamAV not found."
    return run_command("clamscan -r / --bell -i")

def run_lynis_audit():
    if not shutil.which("lynis"):
        return "Lynis not found."
    return run_command("lynis audit system --quick")

def run_windows_defender_scan():
    # Windows Defender command line
    command = r'powershell "Start-MpScan -ScanType QuickScan"'
    return run_command(command)

def run_windows_security_status():
    # Show AV status via PowerShell
    command = r'powershell "Get-MpComputerStatus | Select-Object AMServiceEnabled, AntispywareEnabled, AntivirusEnabled"'
    return run_command(command)

def run_macos_security_audit():
    audit_info = run_command("system_profiler SPFirewallDataType")
    xprotect_status = run_command("defaults read /System/Library/CoreServices/XProtect.bundle/Contents/Info.plist")
    return f"{audit_info}\n\nXProtect Info:\n{xprotect_status}"

def scan_viruses_and_vulnerabilities():
    os_type = platform.system()
    output = f"Detected OS: {os_type}\n"

    if os_type == "Linux":
        output += "\n--- ClamAV Scan ---\n"
        output += run_clamav_scan()
        output += "\n--- Lynis Audit ---\n"
        output += run_lynis_audit()

    elif os_type == "Darwin":  # macOS
        output += "\n--- macOS Security Audit ---\n"
        output += run_macos_security_audit()

    elif os_type == "Windows":
        output += "\n--- Windows Defender Scan ---\n"
        output += run_windows_defender_scan()
        output += "\n--- Defender Status ---\n"
        output += run_windows_security_status()

    else:
        output += "❌ Unsupported OS for security scanning."

    return output
