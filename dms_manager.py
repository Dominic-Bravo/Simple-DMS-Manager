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
    # Assumes dms_manager.py is at the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Construct the command to run dms.cli
    # Use sys.executable to ensure the correct Python interpreter is used
    # -m dms.cli runs the module as a script
    cli_command = [sys.executable, '-m', 'dms.cli']

    # If no arguments are provided, default to 'index' command as per guide.md
    # "Run the program" -> "The program will process every file in the inbox"
    if len(sys.argv) == 1:
        # Default behavior: run index command with default inbox
        cli_command.extend(['index'])
    else:
        # Forward all other arguments directly
        cli_command.extend(sys.argv[1:])

    print(f"[{os.path.basename(__file__)}] Forwarding to: {' '.join(cli_command)}")
    
    try:
        # Execute the dms.cli command
        # Use check_call to raise an exception if the command returns a non-zero exit code
        subprocess.check_call(cli_command, cwd=project_root)
    except subprocess.CalledProcessError as e:
        print(f"[{os.path.basename(__file__)}] Error executing dms.cli: {e}", file=sys.stderr)
        sys.exit(e.returncode)
    except FileNotFoundError:
        print(f"[{os.path.basename(__file__)}] Error: Python interpreter or dms.cli not found.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
