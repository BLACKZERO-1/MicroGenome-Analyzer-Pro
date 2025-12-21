import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui.main_window import MainWindow

def setup_environment():
    """
    Ensures the application knows where its internal tools and 
    databases are located, as per the directory structure[cite: 25, 26].
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths for bundled tools and databases [cite: 58, 68]
    tools_path = os.path.join(base_dir, "tools")
    db_path = os.path.join(base_dir, "databases")
    
    # Add tools to system PATH so the backend logic can call them [cite: 164, 165]
    os.environ["PATH"] += os.pathsep + tools_path
    
    return base_dir

def main():
    # Enable High-DPI scaling for high-resolution displays [cite: 214]
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    # Set Project Metadata [cite: 1, 2]
    app.setApplicationName("MicroGenome Analyzer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Bioinformatics Solutions")

    # Initialize Environment
    base_dir = setup_environment()

    # Load Professional Dark Theme [cite: 214]
    style_path = os.path.join(base_dir, "ui", "styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            app.setStyleSheet(f.read())

    # Launch the Analysis Hub [cite: 280, 285]
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()