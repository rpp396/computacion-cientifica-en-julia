"""
Manages the creation and removal of virtual COM port pairs using com0com.

This module relies on `setupc.exe` (part of com0com) being available in the
system's PATH environment variable. Com0com is an open-source virtual serial
port driver and can be downloaded from http://com0com.sourceforge.net/.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)

def create_com_port_pair(user_port_name: str, internal_port_name: str) -> bool:
    """
    Creates a virtual COM port pair using com0com's setupc.exe.

    Args:
        user_port_name: The desired name for the user-facing COM port (e.g., "COM7").
        internal_port_name: The desired name for the internal/application-facing
                             COM port (e.g., "CNCA0", "CNCB0").

    Returns:
        True if the port pair was created successfully, False otherwise.
    """
    command = [
        "setupc.exe",
        "install",
        f"PortName={user_port_name},EmuBR=yes",
        f"PortName={internal_port_name},EmuBR=yes"
    ]
    logger.debug(f"Executing command: {' '.join(command)}")
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        logger.debug(f"Command stdout for create_com_port_pair ({user_port_name}<->{internal_port_name}):\n{process.stdout.strip()}")
        if process.stderr:
            logger.debug(f"Command stderr for create_com_port_pair ({user_port_name}<->{internal_port_name}):\n{process.stderr.strip()}")
        
        if process.returncode == 0:
            logger.info(f"Successfully created COM port pair: {user_port_name} <=> {internal_port_name}")
            return True
        else:
            logger.error(f"Failed to create COM port pair {user_port_name} <=> {internal_port_name}. Return code: {process.returncode}")
            logger.error(f"com0com stderr (if any): {process.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.critical("com0com setupc.exe not found. Ensure com0com is installed and setupc.exe is in the system PATH.")
        return False
    except subprocess.SubprocessError as e: # More specific than generic Exception
        logger.error(f"Error executing com0com command {' '.join(command)}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while trying to create COM port pair: {e}")
        return False

def remove_com_port(port_name_or_index: str) -> bool:
    """
    Removes a virtual COM port or pair using com0com's setupc.exe.

    Args:
        port_name_or_index: The name of one of the COM ports in a pair
                             (e.g., "COM7") or the index of the port pair
                             (e.g., "0").

    Returns:
        True if the port/pair was removed successfully, False otherwise.
    """
    command = ["setupc.exe", "remove", port_name_or_index]
    logger.debug(f"Executing command: {' '.join(command)}")
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=False)
        logger.debug(f"Command stdout for remove_com_port ({port_name_or_index}):\n{process.stdout.strip()}")
        if process.stderr:
            logger.debug(f"Command stderr for remove_com_port ({port_name_or_index}):\n{process.stderr.strip()}")

        if process.returncode == 0:
            logger.info(f"Successfully sent command to remove COM port/pair: {port_name_or_index}")
            return True
        else:
            logger.error(f"Failed to remove COM port/pair {port_name_or_index}. Return code: {process.returncode}")
            logger.error(f"com0com stderr (if any): {process.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.critical("com0com setupc.exe not found. Ensure com0com is installed and setupc.exe is in the system PATH.")
        return False
    except subprocess.SubprocessError as e: # More specific than generic Exception
        logger.error(f"Error executing com0com command {' '.join(command)}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while trying to remove COM port/pair: {e}")
        return False

if __name__ == '__main__':
    # Setup basic logging for direct script execution
    logging.basicConfig(
        level=logging.DEBUG, # Set to DEBUG to see all logs from this module
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger.info("com_manager.py executed directly for testing.")

    user_port = "COM77" # Using a high number to avoid common ports
    internal_port = "CNCB77"

    logger.info(f"Attempting to create port pair: {user_port} <-> {internal_port}")
    if create_com_port_pair(user_port, internal_port):
        logger.info(f"Successfully created {user_port} and {internal_port} for testing.")

        input(f"Press Enter to attempt to remove port {user_port} (this might remove the pair if successful)...")
        if remove_com_port(user_port):
             logger.info(f"Attempt to remove {user_port} (or its pair) succeeded during testing.")
        else:
             logger.error(f"Attempt to remove {user_port} (or its pair) failed during testing. Try removing by index if known.")
    else:
        logger.error(f"Failed to create {user_port} and {internal_port} during testing. "
                     "Is com0com installed and setupc.exe in PATH?")
        logger.info("You can download com0com from http://com0com.sourceforge.net/")
        logger.info("After installation, ensure the installation directory (e.g., C:\\Program Files (x86)\\com0com) is added to your system's PATH.")
    
    logger.info("com_manager.py direct execution test finished.")
