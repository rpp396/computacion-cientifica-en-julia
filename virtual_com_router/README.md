# Virtual COM Port Router

## Overview

The Virtual COM Port Router is a Python application designed for Windows. It creates virtual serial COM port pairs using the `com0com` null-modem emulator and routes data from one of these user-specified virtual COM ports to a designated network IP address and port. This is useful for bridging serial communication from legacy or test applications to network services or data collectors.

## Features

-   **Virtual COM Port Management**: Dynamically creates and attempts to remove virtual COM port pairs.
-   **Data Routing**: Captures data from a virtual COM port and forwards it to a specified TCP/IP network endpoint.
-   **Command-Line Interface (CLI)**: Provides an easy-to-use CLI for creating, deleting, and listing active routing sessions.
-   **Logging**: Integrated logging provides status updates, error reports, and debug information for troubleshooting.

## Prerequisites

-   **Python**: Version 3.7 or newer.
-   **pyserial**: Python package for serial port communication.
    -   Installation: `pip install pyserial`
-   **com0com (Null-modem emulator)**:
    -   This is a third-party tool for Windows that must be installed separately.
    -   Download from: [com0com Official Website](http://com0com.sourceforge.net/)
    -   **Crucially**, the `setupc.exe` utility (which is part of the `com0com` installation) must be accessible via your system's PATH environment variable.

## Setup

1.  **Clone the Repository** (or download the source code):
    ```bash
    git clone <your_repository_url_here>
    ```
2.  **Navigate to the Directory**:
    ```bash
    cd virtual_com_router
    ```
3.  **Install Dependencies**:
    ```bash
    pip install pyserial
    ```
4.  **Install com0com**:
    -   Download and install `com0com` from [its website](http://com0com.sourceforge.net/).
    -   **Reminder**: Ensure that the directory containing `setupc.exe` (e.g., `C:\Program Files (x86)\com0com`) is added to your system's PATH environment variable.

## Usage

### Running the Application

The application is controlled via `main.py` from within the `virtual_com_router` directory:

```bash
python main.py <command> [options...]
```

Alternatively, if you are in the parent directory of `virtual_com_router`, you can run it as a module (though direct execution from its directory is simpler for this project structure):

```bash
python -m virtual_com_router.main <command> [options...]
```

### Commands

#### `create`

Creates a new virtual COM port pair and starts routing data from the `USER_COM_PORT` to the specified network target.

**Syntax**:
```bash
python main.py create <USER_COM_PORT> <INTERNAL_COM_PORT> <TARGET_IP> <TARGET_PORT> [--baudrate BAUD_RATE]
```

**Arguments**:
-   `<USER_COM_PORT>`: The name for the user-facing virtual COM port (e.g., `COM7`). Your application will connect to this port to send data.
-   `<INTERNAL_COM_PORT>`: The name for the other end of the virtual COM port pair, managed by `com0com` (e.g., `CNCB0`, `COM_INTERNAL`). This port is linked to `<USER_COM_PORT>`.
-   `<TARGET_IP>`: The IP address to which data received on `<USER_COM_PORT>` will be routed.
-   `<TARGET_PORT>`: The port number on the `<TARGET_IP>` where the data will be sent.
-   `[--baudrate BAUD_RATE]`: (Optional) The baud rate for the serial communication on `<USER_COM_PORT>`. Defaults to `9600`.

**Example**:
```bash
python main.py create COM10 CNCB10 192.168.1.100 5000 --baudrate 115200
```
This command creates a pair `COM10 <=> CNCB10`. Data sent to `COM10` will be routed to `192.168.1.100:5000` at a baud rate of 115200.

#### `delete`

Stops any active data routing for the specified `USER_COM_PORT` (if managed by the current application session) and then attempts to remove the virtual COM port pair using `com0com`.

**Syntax**:
```bash
python main.py delete <USER_COM_PORT>
```

**Example**:
```bash
python main.py delete COM10
```

**Note**: This command attempts to remove the port using `com0com`'s `setupc.exe` utility. `com0com` often identifies port pairs by an internal index. While this command uses the port name, successful removal depends on `com0com`'s interpretation and mapping. Always verify with `com0com`'s own tools (like `setupg.exe` or `setupc.exe list`) if you are unsure about the status of virtual ports.

#### `list`

Lists the active data routing sessions that are currently being managed by this instance of the application. It shows which COM ports are being routed to which network destinations.

**Syntax**:
```bash
python main.py list
```

### Application Behavior

-   When a `create` command is successfully executed, the data routing for that COM port starts in background threads.
-   The main application (`main.py`) will remain active in the terminal, displaying a list of active routes.
-   To stop all active data routers and terminate the application gracefully, press `Ctrl+C` in the terminal where `main.py` is running.

## How it Works (Briefly)

1.  **COM Port Management**: The application interfaces with `com0com`'s command-line utility, `setupc.exe`, to send commands for creating and removing virtual COM port pairs.
2.  **Data Reading**: It uses the `pyserial` library to open and read data from the user-specified virtual COM port (e.g., `COM10` in the example).
3.  **Data Forwarding**: Python's built-in `socket` library is used to establish a TCP connection to the target IP address and port, and then to send the data read from the COM port over this network connection.
4.  **Concurrency**: Each active COM port routing session runs in its own dedicated thread, allowing multiple ports to be routed simultaneously.

## Troubleshooting & Notes

-   **`setupc.exe` Path**: The most common issue is `com0com`'s `setupc.exe` not being found. Ensure it's installed and its directory is in your system's PATH. You can test this by opening a new Command Prompt or PowerShell window and typing `setupc.exe`. If it's not recognized, the PATH is not set up correctly.
-   **Session Management**: The application's `list` command and `Ctrl+C` shutdown only manage router instances active within its current session. If you restart the application, it won't automatically know about ports created in a previous session.
-   **Port Persistence**: Virtual COM ports created by `com0com` are system-wide resources. Even if this application is closed or crashes, the ports created by `com0com` may persist until explicitly removed. You can use this application's `delete` command or `com0com`'s own GUI (`setupg.exe`) or CLI (`setupc.exe remove <index>`) tools to manage these persistent ports.
-   **Port In Use**: Ensure the COM ports you are trying to use (e.g., `COM10`) are not already in use by another application.

## Logging

-   The application uses Python's built-in `logging` module for outputting status information, warnings, and errors.
-   Logs are printed to the console by default and include:
    -   Timestamp
    -   Log level (e.g., INFO, DEBUG, ERROR)
    -   Logger name (often the module name)
    -   Function name
    -   The log message
-   The default log level is `INFO`. For more detailed output, such as the exact commands being sent to `com0com` or byte-level data being routed (very verbose), you can change the logging level to `DEBUG`. This is typically done by modifying the `logging.basicConfig` level in `virtual_com_router/main.py` (and potentially in the `if __name__ == '__main__':` blocks of other modules if testing them individually).
    ```python
    # In main.py, change:
    # logging.basicConfig(level=logging.INFO, ...)
    # to:
    # logging.basicConfig(level=logging.DEBUG, ...)
    ```

This should provide a comprehensive guide for users.

## Testing Strategy (Conceptual)

While this project does not currently include an automated test suite, here's an outline of how one might approach testing its components:

### Unit Testing

**`network_router.py` (DataRouter Class)**

*   **Mocking Dependencies**:
    *   The `serial.Serial` object from `pyserial` can be mocked using `unittest.mock.patch`. The mock should simulate methods like `read()`, `write()`, `open()`, `close()`, `in_waiting`, and `is_open`.
    *   The `socket.socket` object can also be mocked. The mock should simulate `connect()`, `sendall()`, `recv()`, and `close()`.
*   **Test Cases**:
    *   Verify successful initialization and connection to both serial and socket.
    *   Simulate data arriving on the mock serial port and assert that it's correctly passed to `sendall()` on the mock socket.
    *   Test error conditions:
        *   Failure to open serial port.
        *   Failure to connect socket.
        *   Errors during serial read or socket send.
    *   Ensure the routing thread starts and stops gracefully (`start()` and `stop()` methods).
    *   Check behavior with different data patterns and sizes.

**`com_manager.py`**

*   **Mocking `subprocess.run`**:
    *   Use `unittest.mock.patch('subprocess.run')` to intercept calls to `com0com`'s `setupc.exe`.
    *   Configure the mock to return a `subprocess.CompletedProcess` instance with various `returncode`, `stdout`, and `stderr` values to simulate:
        *   Successful port creation/deletion.
        *   `com0com` command failure.
        *   `setupc.exe` not found (`FileNotFoundError` should also be testable by setting `side_effect=FileNotFoundError` on the mock).
*   **Test Cases**:
    *   Verify that `create_com_port_pair` and `remove_com_port` construct the correct command arrays for `subprocess.run`.
    *   Check that the functions correctly interpret the `returncode` from the mocked `subprocess.run`.

**`cli.py`**

*   **Mocking `argparse` and backend functions**:
    *   Test argument parsing by providing various command-line strings.
    *   Mock the functions from `com_manager` and `network_router.DataRouter` that `cli.py` calls.
    *   Verify that the correct functions are called with the expected arguments based on parsed CLI input.
    *   Check that `active_routers` is managed correctly (for `create`, `delete`, `list` in-session).

### Integration Testing

*   **Environment**: Requires a Windows environment with `com0com` installed and `setupc.exe` in the PATH.
*   **Scenario**:
    1.  Programmatically create a virtual COM port pair (e.g., COM7 <=> CNCB0) using `com_manager.create_com_port_pair()`.
    2.  Start a `DataRouter` instance to listen on `COM7` and route data to a simple local TCP echo server (which you'd also need to run for the test, listening on, e.g., `127.0.0.1:12345`).
    3.  In the test script, open `CNCB0` using `pyserial`.
    4.  Write known data to `CNCB0`.
    5.  Verify that the local TCP echo server receives this data and that the `DataRouter` correctly forwards it.
    6.  Use `com_manager.remove_com_port()` to clean up the virtual COM port pair.
*   **Challenges**:
    *   Dependency on external `com0com` installation.
    *   Managing system-level resources (COM ports).
    *   Can be slower and more complex to set up, especially in automated CI/CD pipelines.

### Manual Testing

*   Follow the steps outlined in the "Usage" section of this README.
*   Use a serial terminal program (like PuTTY, Tera Term, or a simple `pyserial`-based script) to send data to one end of the `com0com` virtual pair.
*   Use a network tool (like `netcat`, `ncat`, or a simple Python socket listener script) to verify that data is received at the target IP and port.
