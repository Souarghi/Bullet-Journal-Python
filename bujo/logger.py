import logging

def setup_logger() -> logging.Logger:
    """
    Conf et retourne le logger principal de l'app.
    :return:
    """
    logger = logging.getLogger("bujo")
    logger.setLevel(logging.DEBUG)

    # (Date - Nom - Niveau - Message)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Fichier gère tout historique
    debug_handler = logging.FileHandler("debug.log", encoding="utf-8")
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)

    # Fichier pour les erreurs
    error_handler = logging.FileHandler("error.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(debug_handler)
        logger.addHandler(error_handler)

    return logger

logger = setup_logger()
