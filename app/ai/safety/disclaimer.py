ENGLISH_DISCLAIMER = "This is informational guidance only, not legal advice. Contact Legal Aid for legal questions."
SPANISH_DISCLAIMER = "Esta orientación es solo para fines informativos, no es asesoramiento legal. Comuníquese con Ayuda Legal para preguntas legales."


def get_disclaimer(language: str = "EN") -> str:
    if language.upper() == "ES":
        return SPANISH_DISCLAIMER
    return ENGLISH_DISCLAIMER
