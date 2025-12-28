import sys
import os
import shutil
import logging
import datetime
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QLockFile, QTimer
from PySide6.QtGui import QPixmap

# Optional: Try to import psutil for accurate RAM checks
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from ui.main_window import MainWindow
from database_manager import DatabaseManager

# --- CONFIGURATION ---
APP_NAME = "MicroGenome Analyzer"
APP_VERSION = "1.0.0"
ORG_NAME = "Bioinformatics Solutions"
MIN_RAM_GB = 4
MIN_DISK_SPACE_GB = 3

def setup_logging(base_dir):
    """
    Sets up a persistent log file for debugging user issues.
    """
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"microgenome_{datetime.date.today()}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"📝 Logging started for {APP_NAME} v{APP_VERSION}")

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler to catch crashes and log them.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Show error to user
    error_msg = f"An unexpected error occurred:\n{exc_value}\n\nPlease check the logs."
    # We create a dummy app instance if one doesn't exist to show the message box
    if QApplication.instance():
        QMessageBox.critical(None, "Critical Error", error_msg)
    else:
        print("CRITICAL:", error_msg)

def check_system_requirements(base_dir):
    """
    Verifies system meets Blueprint specifications [cite: 20-22].
    - RAM: 4GB minimum
    - Storage: 3GB free
    """
    logging.info("Checking system requirements...")
    
    # 1. Check Disk Space
    try:
        total, used, free = shutil.disk_usage(base_dir)
        free_gb = free / (1024 ** 3)
        if free_gb < MIN_DISK_SPACE_GB:
            logging.error(f"Insufficient disk space: {free_gb:.2f}GB")
            return False, f"Insufficient disk space.\nFree: {free_gb:.1f}GB\nRequired: {MIN_DISK_SPACE_GB}GB"
    except Exception as e:
        logging.warning(f"Disk check failed: {e}")

    # 2. Check RAM (if psutil is installed)
    if PSUTIL_AVAILABLE:
        try:
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            if ram_gb < MIN_RAM_GB:
                logging.warning(f"Low RAM detected: {ram_gb:.1f}GB")
                # We warn but allow launch
        except Exception as e:
            logging.warning(f"RAM check failed: {e}")
            
    return True, "OK"

def setup_environment():
    """Ensures tools and databases are accessible."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths
    tools_path = os.path.join(base_dir, "tools")
    
    # Add tools to system PATH
    if os.path.exists(tools_path):
        os.environ["PATH"] += os.pathsep + tools_path
        logging.info(f"Tools path added: {tools_path}")
    else:
        logging.warning(f"Tools directory missing at {tools_path}")
    
    return base_dir

def check_updates_stub():
    """Placeholder for future auto-update logic[cite: 251]."""
    logging.info("Checking for updates... (Feature stub)")
    # Future implementation: requests.get(GITHUB_API_URL)

def main():
    # 1. Setup Exception Handling
    sys.excepthook = handle_exception

    # 2. Initialize App
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)

    # 3. Environment & Logging
    base_dir = setup_environment()
    setup_logging(base_dir)

    # 4. Single Instance Lock
    # Prevents database corruption from multiple instances
    lock_file = QLockFile(os.path.join(base_dir, "microgenome.lock"))
    if not lock_file.tryLock(100):
        QMessageBox.warning(None, "Already Running", 
                          f"{APP_NAME} is already open.")
        return

    # 5. Splash Screen
    # Uses a placeholder if image is missing to prevent crash
    splash_path = os.path.join(base_dir, "ui", "assets", "splash.png")
    if os.path.exists(splash_path):
        splash_pix = QPixmap(splash_path)
        splash = QSplashScreen(splash_pix)
        splash.show()
        app.processEvents()
        splash.showMessage(f"Initializing {APP_NAME}...", Qt.AlignBottom | Qt.white)
    else:
        splash = None

    # 6. System Checks
    is_compatible, msg = check_system_requirements(base_dir)
    if not is_compatible:
        if splash: splash.close()
        QMessageBox.critical(None, "System Requirements Error", msg)
        return

    # 7. Database Initialization
    logging.info("Initializing database manager...")
    db_path = os.path.join(base_dir, "microgenome.db")
    db_manager = None
    
    try:
        db_manager = DatabaseManager(db_path)
        # Log startup event
        db_manager.log_event('INFO', 'system', f'App started v{APP_VERSION}')
    except Exception as e:
        logging.error(f"Database init failed: {e}")
        if splash: splash.close()
        QMessageBox.warning(None, "Database Error", 
                          "Could not connect to database.\nRunning in offline mode.")

    # 8. Load Theme
    style_path = os.path.join(base_dir, "ui", "styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())

    # 9. Launch Main Window
    logging.info("Launching Main Window")
    window = MainWindow(db_manager)
    window.show()
    
    if splash:
        splash.finish(window)

    # 10. Run Application
    check_updates_stub()
    exit_code = app.exec()
    
    # Cleanup
    if db_manager:
        try:
            db_manager.close()
        except:
            pass
    logging.info("Application shutdown")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()