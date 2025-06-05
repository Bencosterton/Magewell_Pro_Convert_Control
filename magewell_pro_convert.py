import requests
import json
import hashlib
import sys
import argparse
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class MagewellSwitcher:
       
    def __init__(self, ip_address: str, username: str = "admin", password: str = "password"):

        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.base_url = f"http://{ip_address}/mwapi"
        self.session = requests.Session()
        self.authenticated = False
    
    def _hash_password(self) -> str:
        return hashlib.md5(self.password.encode()).hexdigest()
    
    def login(self) -> bool:
        try:
            params = {
                "method": "login",
                "id": self.username,
                "pass": self._hash_password()
            }
            
            response = self.session.get(self.base_url, params=params)
            data = response.json()
            
            if data.get("status") == 0:
                self.authenticated = True
                logger.info(f"Successfully logged in to {self.ip_address}")
                return True
            else:
                logger.error(f"Login failed: {data}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def _check_auth(self) -> bool:
        if not self.authenticated:
            return self.login()
        return True
    
    def get_current_channel(self) -> Optional[Dict[str, Any]]:
        if not self._check_auth():
            return None
            
        try:
            params = {"method": "get-channel"}
            response = self.session.get(self.base_url, params=params)
            data = response.json()
            
            if data.get("status") == 0:
                return data
            else:
                logger.error(f"Failed to get current channel: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting current channel: {e}")
            return None
    
    def get_ndi_sources(self) -> Optional[List[Dict[str, Any]]]:
        if not self._check_auth():
            return None
            
        try:
            params = {"method": "get-ndi-sources"}
            response = self.session.get(self.base_url, params=params)
            data = response.json()
            
            if data.get("status") == 0:
                return data.get("sources", [])
            else:
                logger.error(f"Failed to get NDI sources: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting NDI sources: {e}")
            return None
    
    def set_channel(self, source_name: str) -> bool:
        if not self._check_auth():
            return False
            
        try:
            params = {
                "method": "set-channel",
                "ndi-name": "true",
                "name": source_name
            }
            
            response = self.session.get(self.base_url, params=params)
            data = response.json()
            
            if data.get("status") == 0:
                logger.info(f"Successfully switched to source: {source_name}")
                return True
            else:
                logger.error(f"Failed to set channel: {data}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting channel: {e}")
            return False


def display_ndi_sources(sources: List[Dict[str, Any]]) -> None:
    """Display the list of NDI sources in a formatted table."""
    if not sources:
        print("No NDI sources available.")
        return
        
    print("\nAvailable NDI Sources:")
    print("-" * 80)
    print(f"{'#':3} | {'Source Name':<60} | {'IP Address':<15}")
    print("-" * 80)
    
    for idx, source in enumerate(sources, 1):
        name = source.get("ndi-name", "Unknown")
        ip = source.get("ip-addr", "Unknown")
        print(f"{idx:3} | {name:<60} | {ip:<15}")


def main():
    parser = argparse.ArgumentParser(description="Control a Magewell video switcher")
    
    parser.add_argument("--ip", required=True, help="IP address of the Magewell device")
    parser.add_argument("--username", default="Admin", help="Username for authentication")
    parser.add_argument("--password", default="Admin", help="Password for authentication")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Current channel command
    subparsers.add_parser("current", help="Show current channel")
    
    # List sources command
    subparsers.add_parser("list", help="List available NDI sources")
    
    # Set channel command
    set_parser = subparsers.add_parser("set", help="Set the current channel")
    set_parser.add_argument("source", help="NDI source name to select")
    
    # Interactive mode
    subparsers.add_parser("interactive", help="Start interactive mode")
    
    args = parser.parse_args()
    
    # Create switcher instance
    switcher = MagewellSwitcher(
        ip_address=args.ip,
        username=args.username,
        password=args.password
    )
    
    # Ensure we're authenticated
    if not switcher.login():
        print(f"Failed to authenticate with switcher at {args.ip}")
        sys.exit(1)
        
    # Process commands
    if args.command == "current":
        channel = switcher.get_current_channel()
        if channel:
            print("\nCurrent Channel:")
            print(f"Name: {channel.get('name', 'Unknown')}")
            print(f"NDI: {'Yes' if channel.get('ndi-name') else 'No'}")
        else:
            print("Failed to retrieve current channel.")
            
    elif args.command == "list":
        sources = switcher.get_ndi_sources()
        if sources:
            display_ndi_sources(sources)
        else:
            print("Failed to retrieve NDI sources.")
            
    elif args.command == "set":
        if switcher.set_channel(args.source):
            print(f"Successfully switched to: {args.source}")
        else:
            print(f"Failed to switch to: {args.source}")
            
    elif args.command == "interactive":
        run_interactive_mode(switcher)
    
    else:
        parser.print_help()


def run_interactive_mode(switcher: MagewellSwitcher) -> None:
    print("\nMagewell Switcher Interactive Mode")
    print(f"Connected to: {switcher.ip_address}")
    
    while True:
        print("\nOptions:")
        print("1. Show current channel")
        print("2. List NDI sources")
        print("3. Switch to a source")
        print("4. Exit")
        
        choice = input("\nEnter option (1-4): ").strip()
        
        if choice == "1":
            channel = switcher.get_current_channel()
            if channel:
                print("\nCurrent Channel:")
                print(f"Name: {channel.get('name', 'Unknown')}")
                print(f"NDI: {'Yes' if channel.get('ndi-name') else 'No'}")
            else:
                print("Failed to retrieve current channel.")
                
        elif choice == "2":
            sources = switcher.get_ndi_sources()
            if sources:
                display_ndi_sources(sources)
                
                # Save sources for option 3
                switcher.cached_sources = sources
            else:
                print("Failed to retrieve NDI sources.")
                
        elif choice == "3":
            # Check if we have sources cached
            if not hasattr(switcher, "cached_sources") or not switcher.cached_sources:
                print("Fetching available sources first...")
                sources = switcher.get_ndi_sources()
                if sources:
                    display_ndi_sources(sources)
                    switcher.cached_sources = sources
                else:
                    print("Failed to retrieve sources. Please try again.")
                    continue
            
            # Let user select a source
            try:
                idx = int(input("\nEnter source number to select (or 0 to cancel): "))
                if idx == 0:
                    continue
                    
                if 1 <= idx <= len(switcher.cached_sources):
                    source = switcher.cached_sources[idx-1]
                    source_name = source.get("ndi-name")
                    
                    if switcher.set_channel(source_name):
                        print(f"Successfully switched to: {source_name}")
                    else:
                        print(f"Failed to switch to: {source_name}")
                else:
                    print("Invalid source number.")
            except ValueError:
                print("Please enter a valid number.")
                
        elif choice == "4":
            print("Exiting...")
            break
            
        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
