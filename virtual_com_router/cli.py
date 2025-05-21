"""
Command-Line Interface for Virtual COM Port Router.

This module provides CLI commands to create, delete, and list virtual COM port
pairs and their data routing configurations. It uses com_manager to interact
with com0com for COM port creation/deletion and network_router to manage
the data flow from a COM port to a TCP socket.
"""
import argparse
import sys
import logging

logger = logging.getLogger(__name__)

# active_routers is defined in __main__ of main.py and passed around or imported.
# For direct execution (if __name__ == '__main__'), it's handled locally.
# If this cli.py is imported as a module, active_routers is expected to be managed
# by the importing module (e.g., main.py).
active_routers = {}

def main_cli(com_manager_module, network_router_module):
    """
    Manages CLI argument parsing and command execution.
    """
    global active_routers # Ensure we're using the global dict defined in this module

    create_com_port_pair = com_manager_module.create_com_port_pair
    remove_com_port = com_manager_module.remove_com_port
    DataRouter = network_router_module.DataRouter

    parser = argparse.ArgumentParser(
        description="Virtual COM Port Router CLI. Manages virtual COM ports and routes their data."
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    subparsers.required = True

    create_parser = subparsers.add_parser('create', help='Create a virtual COM port and route its data to an IP address.')
    create_parser.add_argument('user_com_port', help="Name for the user-facing virtual COM port (e.g., COM7)")
    create_parser.add_argument('internal_com_port', help="Name for the internal end of the virtual COM port pair (e.g., CNCB0)")
    create_parser.add_argument('target_ip', help="Target IP address for data routing")
    create_parser.add_argument('target_port', type=int, help="Target port number for data routing")
    create_parser.add_argument('--baudrate', type=int, default=9600, help="Baud rate for the COM port (default: 9600)")

    delete_parser = subparsers.add_parser('delete', help='Stop routing and attempt to delete a virtual COM port.')
    delete_parser.add_argument('user_com_port', help="User-facing COM port name to delete (e.g., COM7)")

    list_parser = subparsers.add_parser('list', help='List active COM port routings managed by this session.')

    args = parser.parse_args()

    if args.command == 'create':
        logger.info(f"Attempting to create virtual COM pair: {args.user_com_port} <=> {args.internal_com_port}")
        success = create_com_port_pair(args.user_com_port, args.internal_com_port)
        if success:
            logger.info(f"Virtual COM pair {args.user_com_port} <=> {args.internal_com_port} created successfully.")
            router = DataRouter(args.user_com_port, args.baudrate, args.target_ip, args.target_port)
            router.start()
            if router.is_running:
                active_routers[args.user_com_port] = router
                logger.info(f"Successfully started routing data from {args.user_com_port} to {args.target_ip}:{args.target_port}.")
                logger.info("NOTE: Routing runs in background. This CLI command will exit. Use 'list' or manage externally (e.g. main application Ctrl+C).")
            else:
                logger.error(f"Failed to start data router for {args.user_com_port}. Attempting to clean up COM pair.")
                if not remove_com_port(args.user_com_port):
                    logger.warning(f"Cleanup of COM port {args.user_com_port} failed or port was not found for removal.")
                else:
                    logger.info(f"COM port {args.user_com_port} (and its pair) removed successfully during cleanup.")
        else:
            logger.error(f"Failed to create virtual COM pair {args.user_com_port} <=> {args.internal_com_port}. Check com0com setup and logs.")

    elif args.command == 'delete':
        logger.info(f"Attempting to stop routing and delete COM port: {args.user_com_port}")
        if args.user_com_port in active_routers:
            router = active_routers.pop(args.user_com_port) # Remove from dict
            router.stop() # This method now uses logging
            logger.info(f"Stopped data routing for {args.user_com_port} from this session's active list.")
        else:
            logger.info(f"No active router found for {args.user_com_port} in this session's list. Attempting removal directly with com0com.")
        
        if remove_com_port(args.user_com_port):
            logger.info(f"com0com command to remove COM port {args.user_com_port} (or its pair) sent. Verify with com0com tools (e.g., `setupc list`).")
        else:
            logger.error(f"com0com command to remove COM port {args.user_com_port} failed. It might need an index or was not found by setupc.")

    elif args.command == 'list':
        logger.info("Listing active COM port routings managed by this session:")
        if active_routers:
            for port, router_obj in active_routers.items():
                if router_obj.is_running: # Check if it's still considered running
                    logger.info(f"  - {port} (Baud: {router_obj.baud_rate}) -> {router_obj.target_ip}:{router_obj.target_port} [ACTIVE]")
                else: # Should ideally not happen if stop/delete removes it from active_routers
                    logger.info(f"  - {port} (Baud: {router_obj.baud_rate}) -> {router_obj.target_ip}:{router_obj.target_port} [INACTIVE but in list]")
        else:
            logger.info("  No active routings managed in this session.")

if __name__ == '__main__':
    # This block is for when cli.py is run directly (e.g., python virtual_com_router/cli.py create ...)
    # It needs its own logging setup if main.py is not the entry point.
    # And its own way to get com_manager and network_router.
    
    # Setup basic logging for direct script execution
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    logger.info("cli.py executed directly.")

    # Need to import com_manager and network_router.
    # This assumes cli.py is in virtual_com_router, and sibling modules are there.
    com_manager_module = None
    network_router_module = None
    try:
        import com_manager as cm_module
        import network_router as nr_module
        com_manager_module = cm_module
        network_router_module = nr_module
        logger.debug("Imported com_manager and network_router for direct execution.")
    except ImportError as e:
        logger.critical(f"Failed to import com_manager or network_router when running cli.py directly: {e}")
        logger.critical("Ensure com_manager.py and network_router.py are in the same directory as cli.py,")
        logger.critical("or that the 'virtual_com_router' package is correctly installed/PYTHONPATH is set.")
        sys.exit(1)
            
    # Call main_cli with the imported modules
    main_cli(com_manager_module, network_router_module)

    # If routers were started, they are in `active_routers`.
    # For direct cli.py execution, we need a way to keep it alive if routers are running,
    # similar to main.py. This is a simplified version.
    if any(router.is_running for router in active_routers.values()):
        logger.info("CLI execution finished. Active routers are running in background.")
        logger.info("Press Ctrl+C to stop routers started by this CLI session.")
        try:
            while any(router.is_running for router in active_routers.values()):
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Ctrl+C detected in direct cli.py execution. Stopping all routers from this session...")
            for port, router_instance in list(active_routers.items()): # Iterate a copy
                if router_instance.is_running:
                    logger.info(f"Stopping router for {port}...")
                    router_instance.stop()
            logger.info("All routers from this cli.py session stopped.")
        finally:
            logger.info("Direct cli.py execution finished.")
    else:
        logger.info("CLI command processed. No active routers running from this session. Exiting.")
