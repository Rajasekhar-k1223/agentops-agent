import subprocess
import logging

def run_command(command: str) -> str:
    logging.info(f"Running command: {command}")
    try:
        result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    except Exception as e:
        result = f"Error: {str(e)}"
        logging.error(result)
    return result
