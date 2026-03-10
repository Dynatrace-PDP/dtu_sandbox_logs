#!/usr/bin/env python3
"""
Log Generator Application
Generates logs based on YAML configuration with grok pattern templates
"""

import os
import sys
import signal
from pathlib import Path

from .config import Config, ConfigValidationError
from .executor import TemplateExecutor


def get_config_path() -> str:
    """
    Determine the configuration file path
    Checks for:
    1. /etc/log-generator/config.yaml (Kubernetes ConfigMap mount)
    2. /app/config/config.yaml (Default Docker path)
    3. Default bundled config
    
    Returns:
        Path to the configuration file
    """
    config_paths = [
        '/etc/log-generator/config.yaml',  # Kubernetes ConfigMap
        '/app/config/config.yaml',         # Docker default
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            return path
    
    # Return the bundled default config
    app_dir = Path(__file__).parent
    return str(app_dir / 'default_config.yaml')


def main():
    """Main entry point for the log generator"""
    try:
        config_path = get_config_path()
        print(f"Loading configuration from: {config_path}", file=sys.stderr)
        
        # Load and validate configuration
        config = Config(config_path)
        templates = config.get_templates()
        
        print(f"Loaded {len(templates)} template(s)", file=sys.stderr)
        for template in templates:
            print(f"  - {template['name']}", file=sys.stderr)
        
        # Initialize and start the executor
        executor = TemplateExecutor(templates)
        executor.start()
        
        print("Log generator started. Press Ctrl+C to stop.", file=sys.stderr)
        
        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            print("\nShutting down...", file=sys.stderr)
            executor.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Wait indefinitely
        executor.wait()
    
    except ConfigValidationError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
