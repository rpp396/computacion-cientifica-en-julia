"""
Provides a DataRouter class to route data from a serial COM port to a TCP socket.

This module is intended to be used for applications that need to bridge
communication between a device connected via a serial port (physical or virtual)
and a network service listening on a TCP socket.
"""

import serial  # Requires pyserial: pip install pyserial
import socket
import threading
import time
import logging

logger = logging.getLogger(__name__)

class DataRouter:
    """
    Routes data from a specified serial COM port to a target IP address and port.
    """

    def __init__(self, com_port: str, baud_rate: int, target_ip: str, target_port: int):
        """
        Initializes the DataRouter.

        Args:
            com_port: The COM port to read data from (e.g., "COM7").
            baud_rate: The baud rate for the COM port communication (e.g., 9600).
            target_ip: The IP address of the target server (e.g., "127.0.0.1").
            target_port: The port number of the target server (e.g., 12345).
        """
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.target_ip = target_ip
        self.target_port = target_port

        self.serial_conn = None
        self.socket_conn = None
        self.is_running = False
        self.thread = None
        logger.debug(f"DataRouter initialized for {self.com_port} -> {self.target_ip}:{self.target_port}")

    def _connect(self) -> bool:
        """
        Establishes connections to the serial port and the target socket.

        Returns:
            True if both connections are successful, False otherwise.
        """
        try:
            logger.info(f"Attempting to open serial port {self.com_port} at {self.baud_rate} baud.")
            self.serial_conn = serial.Serial(self.com_port, self.baud_rate, timeout=1)
            logger.info(f"Successfully opened serial port {self.com_port}.")
        except serial.SerialException as e:
            logger.error(f"Failed to open serial port {self.com_port}: {e}")
            self.serial_conn = None 
            return False

        try:
            logger.info(f"Attempting to connect to socket {self.target_ip}:{self.target_port}.")
            self.socket_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_conn.connect((self.target_ip, self.target_port))
            logger.info(f"Successfully connected to socket {self.target_ip}:{self.target_port}.")
        except socket.error as e:
            logger.error(f"Failed to connect to socket {self.target_ip}:{self.target_port}: {e}")
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.socket_conn = None 
            return False
        
        return True

    def _route_data(self):
        """
        The target function for the routing thread. Reads data from the serial
        port and sends it to the socket connection in a loop.
        """
        logger.info(f"Data routing thread started for {self.com_port} -> {self.target_ip}:{self.target_port}")
        while self.is_running:
            try:
                if self.serial_conn and self.serial_conn.is_open and self.socket_conn:
                    bytes_to_read = self.serial_conn.in_waiting or 1
                    data = self.serial_conn.read(bytes_to_read)
                    if data:
                        self.socket_conn.sendall(data)
                        logger.debug(f"Routed from {self.com_port}: {data!r}")
                else:
                    logger.warning("Serial or socket connection not available in routing loop. Stopping routing.")
                    self.is_running = False 
                    break 
            except serial.SerialException as e:
                logger.error(f"Serial error during routing on {self.com_port}: {e}")
                self.is_running = False
            except socket.error as e:
                logger.error(f"Socket error during routing from {self.com_port} to {self.target_ip}:{self.target_port}: {e}")
                self.is_running = False
            except Exception as e:
                logger.exception(f"Unexpected error in routing loop for {self.com_port}") # logger.exception includes stack trace
                self.is_running = False
            
            time.sleep(0.01)

        logger.info(f"Data routing thread stopped for {self.com_port}.")

    def start(self):
        """
        Starts the data routing process.
        """
        if self.is_running:
            logger.info(f"Routing for {self.com_port} is already active.")
            return

        logger.info(f"Starting data routing for {self.com_port}...")
        if not self._connect():
            logger.error(f"Failed to initialize connections for {self.com_port}. Routing not started.")
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            if self.socket_conn:
                self.socket_conn.close()
            self.serial_conn = None
            self.socket_conn = None
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._route_data, daemon=True)
        self.thread.name = f"DataRouterThread-{self.com_port}" # Give thread a meaningful name
        self.thread.start()
        logger.info(f"Successfully started routing data from {self.com_port} to {self.target_ip}:{self.target_port}")

    def stop(self):
        """
        Stops the data routing process.
        """
        logger.info(f"Stopping data routing for {self.com_port}...")
        self.is_running = False

        if self.thread and self.thread.is_alive():
            logger.info(f"Waiting for routing thread ({self.thread.name}) to finish...")
            self.thread.join(timeout=2)
            if self.thread.is_alive():
                logger.warning(f"Routing thread ({self.thread.name}) did not stop in time.")
        
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
                logger.info(f"Closed COM port {self.com_port}.")
            except Exception as e:
                logger.error(f"Error closing COM port {self.com_port}: {e}")
        
        if self.socket_conn:
            try:
                self.socket_conn.close()
                logger.info(f"Closed socket connection to {self.target_ip}:{self.target_port}.")
            except Exception as e:
                logger.error(f"Error closing socket connection for {self.com_port}: {e}")
        
        self.serial_conn = None
        self.socket_conn = None
        logger.info(f"Data routing for {self.com_port} definitively stopped.")

if __name__ == '__main__':
    # Setup basic logging for direct script execution
    logging.basicConfig(
        level=logging.DEBUG, # Set to DEBUG to see all logs from this module
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger.info("network_router.py executed directly for testing.")

    TEST_COM_PORT = "COM77"  # Choose a high number or one from your virtual pair
    BAUD_RATE = 9600
    TARGET_IP = "127.0.0.1"
    TARGET_PORT = 12345 # Example port, ensure a server is listening or it will fail to connect

    logger.info(f"Attempting to route data from {TEST_COM_PORT} to {TARGET_IP}:{TARGET_PORT}")
    logger.info(f"Ensure {TEST_COM_PORT} exists (e.g., created by com0com) and is free.")
    logger.info(f"A simple socket server listening on {TARGET_IP}:{TARGET_PORT} can receive the data.")
    logger.info("To test, you might need a com0com pair like COM77 <=> CNCB77, and a serial terminal sending to COM77.")
    
    router = DataRouter(TEST_COM_PORT, BAUD_RATE, TARGET_IP, TARGET_PORT)
    router.start()

    if router.is_running:
        try:
            logger.info("Routing active. Press Enter or Ctrl+C to stop and exit.")
            input() # Wait for user to press Enter
        except KeyboardInterrupt:
            logger.info("\nCtrl+C detected. Stopping router...")
        finally:
            router.stop()
    else:
        logger.error("Router failed to start. Check COM port availability and target server.")
    
    logger.info("network_router.py direct execution test finished.")
