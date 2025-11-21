#!/usr/bin/env python3
"""
Script to create and push a git tag for the current version.
Usage: python scripts/push_tag.py
"""

import re
import subprocess
import sys
from pathlib import Path

def get_current_version(pyproject_path):
    content = pyproject_path.read_text()
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)

def run_command(command, capture_output=False):
    try:
        if capture_output:
            result = subprocess.run(command, check=True, shell=True, capture_output=True, text=True)
            return result.stdout
        else:
            subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        sys.exit(1)

def show_git_status():
    print("\n=== Git Status ===")
    status = run_command("git status --short", capture_output=True)
    if status.strip():
        print(status)
    else:
        print("No changes detected.")
    print("==================\n")

def main():
    root_dir = Path(__file__).parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    
    try:
        version = get_current_version(pyproject_path)
        tag = f"v{version}"
        
        show_git_status()
        
        print(f"You are about to create and push tag: {tag}")
        print("Make sure you have committed all your changes.")
        
        response = input("Continue? [y/N]: ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
            
        print(f"Creating and pushing tag: {tag}")
        
        run_command(f"git tag {tag}")
        run_command(f"git push origin {tag}")
        
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
