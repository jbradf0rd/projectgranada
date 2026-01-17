#!/usr/bin/env python3
"""
Granada Build Script

Usage:
    python build.py          # Build the application
    python build.py --clean  # Clean build artifacts before building
    python build.py --dev    # Run in development mode
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Get the directory containing this script
BASE_DIR = Path(__file__).parent.absolute()


def clean_build():
    """Remove build artifacts."""
    print("Cleaning build artifacts...")

    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['*.pyc', '*.pyo', '*.spec.bak']

    for dir_name in dirs_to_remove:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            print(f"  Removing {dir_path}")
            shutil.rmtree(dir_path)

    # Clean __pycache__ in subdirectories
    for pycache in BASE_DIR.rglob('__pycache__'):
        print(f"  Removing {pycache}")
        shutil.rmtree(pycache)

    # Clean .pyc files
    for pyc in BASE_DIR.rglob('*.pyc'):
        pyc.unlink()

    print("Clean complete.")


def ensure_data_dir():
    """Ensure the data directory exists."""
    data_dir = BASE_DIR / 'data'
    if not data_dir.exists():
        print("Creating data directory...")
        data_dir.mkdir(parents=True)
    return data_dir


def init_database():
    """Initialize the database if it doesn't exist."""
    data_dir = ensure_data_dir()
    db_path = data_dir / 'granada.db'

    if not db_path.exists():
        print("Initializing database...")
        # Import and run the app to create database
        sys.path.insert(0, str(BASE_DIR))
        from app.models import init_db, seed_database
        init_db()
        seed_database()
        print("Database initialized with seed data.")
    else:
        print(f"Database already exists at {db_path}")


def run_dev():
    """Run the application in development mode."""
    print("Starting Granada in development mode...")
    ensure_data_dir()
    init_database()

    os.chdir(BASE_DIR)
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'

    subprocess.run([sys.executable, 'app.py'])


def build_exe():
    """Build the Windows executable using PyInstaller."""
    print("Building Granada executable...")

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("ERROR: PyInstaller is not installed.")
        print("Install it with: pip install pyinstaller")
        sys.exit(1)

    # Ensure data directory exists
    ensure_data_dir()

    # Initialize database so it's included in the build
    init_database()

    # Run PyInstaller
    spec_file = BASE_DIR / 'granada.spec'
    if not spec_file.exists():
        print(f"ERROR: Spec file not found at {spec_file}")
        sys.exit(1)

    print(f"Using spec file: {spec_file}")
    result = subprocess.run(
        ['pyinstaller', '--clean', str(spec_file)],
        cwd=BASE_DIR
    )

    if result.returncode == 0:
        dist_dir = BASE_DIR / 'dist' / 'granada'
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)
        print(f"\nExecutable location: {dist_dir / 'granada.exe'}")

        # Calculate size
        if dist_dir.exists():
            total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            print(f"Total size: {size_mb:.1f} MB")

            if size_mb > 100:
                print("\nWARNING: Bundle size exceeds 100MB target.")
                print("Consider additional optimizations.")
    else:
        print("\nBUILD FAILED!")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Granada Build Script')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts')
    parser.add_argument('--dev', action='store_true', help='Run in development mode')
    parser.add_argument('--init-db', action='store_true', help='Initialize database only')

    args = parser.parse_args()

    if args.clean:
        clean_build()
        if not args.dev:
            build_exe()
    elif args.dev:
        run_dev()
    elif args.init_db:
        ensure_data_dir()
        init_database()
    else:
        build_exe()


if __name__ == '__main__':
    main()
