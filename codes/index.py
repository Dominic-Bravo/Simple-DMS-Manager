import subprocess
import sys
import os

# This script acts as a backward-compatible wrapper for the new dms.cli.
# It forwards calls to the unified CLI.

def main():
    """
    Forwards arguments to the dms.cli module.
    """
    # Determine the project root dynamically
    # Assumes codes/index.py is in 'codes' directory, which is under project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Construct the command to run dms.cli
    cli_command = [sys.executable, '-m', 'dms.cli']

    # If no arguments are provided, default to 'index' command
    if len(sys.argv) == 1:
        cli_command.extend(['index'])
    else:
        # Forward all other arguments directly
        cli_command.extend(sys.argv[1:])

    print(f"[{os.path.basename(__file__)}] Forwarding to: {' '.join(cli_command)}")
    
    try:
        # Execute the dms.cli command
        subprocess.check_call(cli_command, cwd=project_root)
    except subprocess.CalledProcessError as e:
        print(f"[{os.path.basename(__file__)}] Error executing dms.cli: {e}", file=sys.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"[{os.path.basename(__file__)}] Error: Python interpreter or dms.cli not found.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
