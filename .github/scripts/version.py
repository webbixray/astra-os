#!/usr/bin/env python3
"""
Version management script for Astra OS.
Supports semantic versioning with prerelease support.
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Optional, Tuple

# Files that contain version
VERSION_FILES = [
    "apps/api/pyproject.toml",
    "services/agent_orchestrator/pyproject.toml",
    "package.json",
]

# Regex patterns for version extraction
VERSION_PATTERNS = {
    "pyproject.toml": r'^version\s*=\s*["\']([^"\']+)["\']',
    "package.json": r'"version"\s*:\s*"([^"]+)"',
}

class VersionManager:
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self._current_version = None
    
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml (primary source)."""
        if self._current_version:
            return self._current_version
        
        pyproject = self.repo_root / "apps/api/pyproject.toml"
        if not pyproject.exists():
            raise FileNotFoundError(f"Primary version file not found: {pyproject}")
        
        content = pyproject.read_text()
        match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if not match:
            raise ValueError("Could not find version in pyproject.toml")
        
        self._current_version = match.group(1)
        return self._current_version
    
    def parse_version(self, version: str) -> Tuple[int, int, int, Optional[str]]:
        """Parse semantic version string."""
        # Pattern: major.minor.patch[-prerelease]
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$', version)
        if not match:
            raise ValueError(f"Invalid version format: {version}")
        
        major, minor, patch = map(int, match.groups()[:3])
        prerelease = match.group(4) if match.lastindex >= 4 else None
        return major, minor, patch, prerelease
    
    def bump_version(self, bump_type: str, prerelease: Optional[str] = None) -> str:
        """Bump version according to semantic versioning."""
        current = self.get_current_version()
        major, minor, patch, existing_prerelease = self.parse_version(current)
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch.")
        
        # Handle prerelease
        new_prerelease = None
        if prerelease is not None:
            if existing_prerelease and existing_prerelease.startswith(prerelease.split('.')[0]):
                # Extract number from prerelease (e.g., alpha.1 -> 1)
                match = re.search(r'(\d+)$', existing_prerelease)
                if match:
                    num = int(match.group(1)) + 1
                    new_prerelease = re.sub(r'(\d+)$', str(num), existing_prerelease)
                else:
                    new_prerelease = f"{prerelease}.1"
            else:
                new_prerelease = f"{prerelease}.1"
        else:
            new_prerelease = None
        
        # Build new version
        new_version = f"{major}.{minor}.{patch}"
        if new_prerelease:
            new_version += f"-{new_prerelease}"
        
        return new_version
    
    def update_version_files(self, new_version: str) -> list:
        """Update all version files."""
        updated = []
        
        for file_path in VERSION_FILES:
            full_path = self.repo_root / file_path
            if not full_path.exists():
                continue
            
            content = full_path.read_text()
            
            if file_path.endswith("pyproject.toml"):
                # Update version in pyproject.toml
                new_content = re.sub(
                    r'^version\s*=\s*["\'][^"\']+["\']',
                    f'version = "{new_version}"',
                    content,
                    flags=re.MULTILINE
                )
            elif file_path.endswith("package.json"):
                new_content = re.sub(
                    r'"version"\s*:\s*"[^"]+"',
                    f'"version": "{new_version}"',
                    content
                )
            else:
                continue
            
            if new_content != content:
                full_path.write_text(new_content)
                updated.append(file_path)
        
        return updated
    
    def release(self, bump_type: str, prerelease: Optional[str] = None, dry_run: bool = False) -> str:
        """Perform a release."""
        new_version = self.bump_version(bump_type, prerelease)
        current = self.get_current_version()
        
        print(f"Current version: {current}")
        print(f"New version:     {new_version}")
        print(f"Bump type:       {bump_type}")
        if prerelease:
            print(f"Prerelease:      {prerelease}")
        
        if dry_run:
            print("\n🧪 DRY RUN - No changes made")
            return new_version
        
        # Update version files
        updated = self.update_version_files(new_version)
        print(f"\nUpdated files: {', '.join(updated) if updated else 'none'}")
        
        # Run tests to verify
        print("\n🧪 Running quick validation...")
        # Install deps first if needed
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "apps/api[dev]", "-q"
        ], capture_output=True, text=True, timeout=120, cwd=self.repo_root)
        
        # Also install agent_orchestrator
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-e", "services/agent_orchestrator", "-q"
        ], capture_output=True, text=True, timeout=60, cwd=self.repo_root)
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", "apps/api/tests/", "-x", "-q", "--tb=line"
        ], capture_output=True, text=True, timeout=120, cwd=self.repo_root)
        if result.returncode != 0:
            print("❌ Tests failed! Rolling back...")
            self.update_version_files(current)
            raise RuntimeError("Tests failed after version bump")
        
        print("✅ Tests passed")
        
        # Commit and tag
        try:
            subprocess.run(["git", "add", "-A"], check=True)
            subprocess.run(["git", "commit", "-m", f"chore: release v{new_version}"], check=True)
            subprocess.run(["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"], check=True)
            print(f"\n✅ Release v{new_version} committed and tagged!")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Git operations failed: {e}")
            raise
        
        return new_version

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Astra OS Version Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Bump command (for CI/CD)
    bump_parser = subparsers.add_parser("bump", help="Bump version and output new version")
    bump_parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="Version bump type")
    bump_parser.add_argument("--prerelease", help="Prerelease identifier (alpha, beta, rc)")
    
    # Release command (full release with tests, commit, tag)
    release_parser = subparsers.add_parser("release", help="Create a new release")
    release_parser.add_argument("bump_type", choices=["major", "minor", "patch"], help="Version bump type")
    release_parser.add_argument("--prerelease", help="Prerelease identifier (alpha, beta, rc)")
    release_parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")
    
    # Current version command
    subparsers.add_parser("current", help="Show current version")
    
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent.parent
    vm = VersionManager(repo_root)
    
    if args.command == "current":
        print(vm.get_current_version())
    elif args.command == "bump":
        try:
            new_version = vm.bump_version(args.bump_type, args.prerelease)
            print(new_version)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "release":
        try:
            new_version = vm.release(args.bump_type, args.prerelease, args.dry_run)
            print(new_version)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()