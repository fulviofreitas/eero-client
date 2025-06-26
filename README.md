# Eero Client

A modern Python client for interacting with Eero networks. This package provides both a programmatic API and a command-line interface for managing your Eero network devices.

## Features

- Complete Eero API coverage
- Async support for better performance
- Structured data models using Pydantic
- Rich CLI with colorful, formatted output
- Comprehensive error handling
- Caching system for improved performance
- Modern Python packaging

## Installation

```bash
pip install eero-client
```

## Command-Line Usage

After installation, you can use the `eero` command to interact with your Eero network:

```bash
# Login to your Eero account
eero login

# Show all networks
eero networks

# Show details for a specific network
eero network [--network-id NETWORK_ID]

# List all Eero devices
eero eeros [--network-id NETWORK_ID]

# Show details for a specific Eero
eero eero EERO_ID [--network-id NETWORK_ID]

# List all connected devices
eero devices [--network-id NETWORK_ID]

# Show details for a specific device
eero device DEVICE_ID [--network-id NETWORK_ID]

# List all profiles
eero profiles [--network-id NETWORK_ID]

# Show details for a specific profile
eero profile PROFILE_ID [--network-id NETWORK_ID]

# Reboot an Eero device
eero reboot EERO_ID [--network-id NETWORK_ID]

# Run a speed test
eero speedtest [--network-id NETWORK_ID]

# Enable or disable guest network
eero guest-network --enable --name "Guest Network" --password "guest-password" [--network-id NETWORK_ID]
eero guest-network --disable [--network-id NETWORK_ID]

# Set nickname for a device
eero rename-device DEVICE_ID "New Nickname" [--network-id NETWORK_ID]

# Block or unblock a device
eero block-device DEVICE_ID --block [--network-id NETWORK_ID]
eero block-device DEVICE_ID --unblock [--network-id NETWORK_ID]

# Pause or unpause a profile
eero pause-profile PROFILE_ID --pause [--network-id NETWORK_ID]
eero pause-profile PROFILE_ID --unpause [--network-id NETWORK_ID]

# Set preferred network for future commands
eero set-network NETWORK_ID

# Show help
eero --help
```

## Python API Usage

```python
import asyncio
from eero import EeroClient

async def main():
    # Create client with automatic cookie storage
    async with EeroClient(cookie_file="~/.eero-cookies.json") as client:
        # Login (if not already authenticated)
        if not client.is_authenticated:
            await client.login("your-email@example.com")
            code = input("Enter verification code: ")
            await client.verify(code)
        
        # Get all networks
        networks = await client.get_networks()
        for network in networks:
            print(f"Network: {network.name} ({network.status})")
        
        # Get all Eero devices
        eeros = await client.get_eeros()
        for eero in eeros:
            print(f"Eero: {eero.name} ({eero.model})")
        
        # Get all connected devices
        devices = await client.get_devices()
        for device in devices:
            print(f"Device: {device.name} ({device.ip_address})")

asyncio.run(main())
```

## Advanced API Usage

```python
import asyncio
from eero import EeroClient

async def main():
    async with EeroClient() as client:
        # Authenticate
        await client.login("your-email@example.com")
        code = input("Enter verification code: ")
        await client.verify(code)
        
        # Get a specific network
        network = await client.get_network("network-id")
        print(f"Network: {network.name}")
        
        # Enable guest network
        result = await client.set_guest_network(
            enabled=True,
            name="My Guest Network",
            password="guest-password"
        )
        print(f"Guest network enabled: {result}")
        
        # Block a device
        result = await client.block_device("device-id", blocked=True)
        print(f"Device blocked: {result}")
        
        # Run a speed test
        speed_test = await client.run_speed_test()
        print(f"Download: {speed_test.get('down', {}).get('value', 0)} Mbps")
        print(f"Upload: {speed_test.get('up', {}).get('value', 0)} Mbps")
        
        # Reboot an Eero
        result = await client.reboot_eero("eero-id")
        print(f"Reboot initiated: {result}")

asyncio.run(main())
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
