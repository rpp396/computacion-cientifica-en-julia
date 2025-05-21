"""
Main entry point for the Virtual COM Port Router application.

This script initializes and runs the command-line interface (CLI)
provided by `cli.py`. After the CLI processes user commands, if any
data routers have been started (e.g., via the 'create' command), this
script will keep the main application thread alive. This allows the
background daemon threads (managed by `DataRouter` instances) to continue
routing data.

Users can press Ctrl+C in the terminal where this script is running to
initiate a graceful shutdown of all active data routers before the
application exits.

It handles imports in a way that supports both execution as part of a package
(e.g., `python -m virtual_com_router.main`) and direct script execution
(e.g., `python main.py` from within the `virtual_com_router` directory),
assuming sibling modules (`cli.py`, `com_manager.py`, `network_router.py`)
are present.
"""
import sys
import time
import logging

# Attempt to import modules using relative imports (if run as part of a package)
try:
    from .cli import main_cli, active_routers
    from . import com_manager
    from . import network_router
    # No print here, logger not configured yet at module level
except ImportError:
    # Fallback to direct imports (if run as a script from within the directory)
    try:
        from cli import main_cli, active_routers
        import com_manager
        import network_router
        # No print here, logger not configured yet at module level
    except ImportError as e_fallback:
        # Use basic print for this critical early failure as logger might not be set up.
        print(f"Fatal Error: Could not import necessary modules (cli, com_manager, network_router).\nDetails: {e_fallback}")
        print("Please ensure that main.py, cli.py, com_manager.py, and network_router.py are all in the same directory (virtual_com_router),")
        print("and you are running the script from that directory, OR")
        print("ensure the 'virtual_com_router' package is correctly installed or its parent directory is in PYTHONPATH if running as a module.")
        sys.exit(1)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,  # Default level, change to DEBUG for more verbosity
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s',
        handlers=[
            logging.StreamHandler() # Log to console
        ]
    )
    # Example: You can set a higher level for noisy libraries if necessary
    # logging.getLogger("pyserial").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__) # Using __name__ for standard practice

    # Log which import path was successful
    if 'virtual_com_router.cli' in sys.modules or '.cli' in sys.modules: # Check if relative import likely succeeded
        logger.debug("Successfully used relative imports for modules.")
    else:
        logger.debug("Successfully used direct imports for modules (common for script execution).")


    logger.debug("Calling main_cli...")
    main_cli(com_manager_module=com_manager, network_router_module=network_router)
    logger.debug(f"main_cli finished. active_routers count: {len(active_routers)}")

    if active_routers:
        logger.info("\n--------------------------------------------------------------------")
        logger.info("Virtual COM Port Router - Main Application Status")
        logger.info("The CLI command has been processed. Active routes may be running in background.")
        
        current_active_routes = {k: v for k, v in active_routers.items() if v.is_running}
        if current_active_routes:
            logger.info("The following routes are currently active:")
            for port, router_obj in current_active_routes.items():
                logger.info(f"  - {port} (Baud: {router_obj.baud_rate}) -> {router_obj.target_ip}:{router_obj.target_port}")
            logger.info("\nPress Ctrl+C in this terminal to stop all active routes and exit the application.")
        else:
            logger.info("No routes are currently active or reporting as running.")
        
        logger.info("--------------------------------------------------------------------")

        try:
            while True:
                if not any(r.is_running for r in active_routers.values()):
                    logger.info("All routers have reported as stopped. Exiting main application.")
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\nCtrl+C detected in main application. Initiating shutdown of all active routers...")
            
            routers_to_stop = list(active_routers.items()) 
            
            for port, router_instance in routers_to_stop:
                if router_instance.is_running:
                    logger.info(f"Attempting to stop router for {port}...")
                    router_instance.stop() 
                
            logger.info("All active routers managed by this session have been requested to stop.")
        finally:
            logger.info("Main application shutdown sequence complete.")
    else:
        logger.info("CLI command processed. No active routers are running or were started by this session. Exiting main application.")

    logger.debug("End of main.py.")
