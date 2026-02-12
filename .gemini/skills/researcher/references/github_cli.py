import sys
import subprocess

def github_cli(command: str):
    """Run GitHub CLI (gh) commands to get repository data."""
    try:
        # Prepend 'gh' if not present
        full_command = f"gh {command}" if not command.startswith("gh ") else command
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout or result.stderr or "No output"
        return output[:5000]
    except subprocess.TimeoutExpired:
        return f"Command timed out: {full_command}"
    except Exception as e:
        return f"Error running {full_command}: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python github_cli.py <command>")
        sys.exit(1)
    
    command = " ".join(sys.argv[1:])
    print(github_cli(command))
