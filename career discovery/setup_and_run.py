import os
import sys
import subprocess
import time
import logging
import pkg_resources
from datetime import datetime
import requests
import json

# Configure logging
if os.name == 'nt':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('setup.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
logger = logging.getLogger(__name__)

def check_python_version():
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher required. Current version: %s", sys.version.split()[0])
        sys.exit(1)
    logger.info("Python version %s is compatible", sys.version.split()[0])

def create_requirements_file():
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        required_packages = [
            "flask==2.3.2",
            "flask-cors==4.0.0",
            "openai-whisper==20231117",
            "torch==2.1.2",
            "requests==2.31.0",
            "google-generativeai>=0.5.0"
        ]
        with open(requirements_file, "w", encoding='utf-8') as f:
            f.write("\n".join(required_packages))
        logger.info("Created requirements.txt with dependencies")

def install_dependencies():
    logger.info("Checking and installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        for package in ['flask', 'flask-cors', 'openai-whisper', 'torch', 'requests', 'google-generativeai']:
            try:
                pkg_resources.get_distribution(package)
            except pkg_resources.DistributionNotFound:
                logger.warning("Package %s not found after installation. Attempting reinstall...", package)
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                pkg_resources.get_distribution(package)
        logger.info("All dependencies installed and verified")
    except (subprocess.CalledProcessError, pkg_resources.DistributionNotFound) as e:
        logger.error("Dependency installation failed: %s", str(e))
        logger.info(logger.info("Please install missing packages manually with: pip install flask flask-cors openai-whisper torch requests google-generativeai")
)
        sys.exit(1)

def setup_directories():
    directories = ["data", "data/audio_temp", "logs", "static"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info("Created directory: %s", directory)

def run_app():
    logger.info("Starting helloIVY Career Selector...")
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error("Application failed to start: %s", str(e))
        sys.exit(1)

def main():
    print("🎓 helloIVY Career Selector - Setup and Run Script")
    print("=" * 60)
    logger.info("Starting setup process at %s", datetime.now().isoformat())

    # Step 1: Check Python version
    check_python_version()

    # Step 2: Create requirements file
    create_requirements_file()

    # Step 3: Install dependencies
    install_dependencies()

    # Step 4: (Optional) Configure environment if you want to use .env for API key
    # configure_environment()  # Uncomment if you use .env

    # Step 5: Setup directories for data, logs, static, etc.
    setup_directories()

    # Step 6: Run the Flask application
    run_app()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Setup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error during setup: %s", str(e))
        sys.exit(1)
