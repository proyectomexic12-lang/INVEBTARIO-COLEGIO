import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler

# Definir la ruta del log (al lado del ejecutable/script)
LOG_FILE = os.path.join(os.path.dirname(__file__), 'inventario_diagnostico.log')

def setup_logger():
    # Crear un logger root
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Evitar duplicar handlers si ya se configuró
    if not logger.handlers:
        # Formato del log
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # File Handler Rotativo: máx 5 MB por archivo, guarda hasta 3 archivos viejos
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream Handler (Consola) - útil durante desarrollo
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def exception_handler(exc_type, exc_value, exc_traceback):
    """Maneja las excepciones no capturadas y las guarda en el log."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger = logging.getLogger()
    logger.error("Excepcion no capturada:", exc_info=(exc_type, exc_value, exc_traceback))

# Sobrescribir el manejador de excepciones global
sys.excepthook = exception_handler

# Inicializar logger al importar
global_logger = setup_logger()
global_logger.info("Sistema de Logging Inicializado")
