#!/usr/bin/env python3
"""
Script to bump the project version in pyproject.toml and aa/__init__.py.
Usage: python scripts/bump_version.py [major|minor|patch]
"""

import re
import sys
from pathlib import Path

def get_current_version(pyproject_path):
    content = pyproject_path.read_text()
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', content)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)

def bump_version(version, part):
    major, minor, patch = map(int, version.split('.'))
    if part == 'major':
        major += 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor += 1
        patch = 0
    elif part == 'patch':
        patch += 1
    else:
        raise ValueError(f"Invalid part: {part}")
    return f"{major}.{minor}.{patch}"

def update_file(path, old_version, new_version):
    content = path.read_text()
    new_content = content.replace(old_version, new_version)
    if content == new_content:
        print(f"Warning: Version {old_version} not found in {path}")
    else:
        path.write_text(new_content)
        print(f"Updated {path} from {old_version} to {new_version}")

def main():
    if len(sys.argv) > 2:
        print("Usage: python scripts/bump_version.py [major|minor|patch]")
        sys.exit(1)
    
    part = sys.argv[1] if len(sys.argv) == 2 else 'patch'
    if part not in ['major', 'minor', 'patch']:
        print(f"Invalid argument: {part}. Must be one of: major, minor, patch")
        sys.exit(1)
    
    root_dir = Path(__file__).parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    init_path = root_dir / "aa" / "__init__.py"
    
    try:
        current_version = get_current_version(pyproject_path)
        new_version = bump_version(current_version, part)
        
        print(f"Bumping version: {current_version} -> {new_version}")
        
        update_file(pyproject_path, current_version, new_version)
        update_file(init_path, current_version, new_version)
        
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
