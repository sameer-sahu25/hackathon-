from typing import Literal, Optional

TEMPLATES = {
    "EN": {
        "reminder_7day": "Hi {name}! Your court date is in {days_label}. Don't forget! Call 211 for free help. Court: {court_address}",
        "reminder_3day": "Hi {name}! Your court date is in {days_label}. Get ready! Call 211 or your lawyer ASAP. Court: {court_address}",
        "reminder_24hr": "URGENT {name}: Court is TOMORROW! Be on time! Call 211 NOW if you need help. Court: {court_address}",
        "reminder_morning_of": "URGENT {name}: Court is TODAY! Don't miss it! Call 211 right away if you need help. Court: {court_address}"
    },
    "ES": {
        "reminder_7day": "¡Hola {name}! Tu fecha de corte es en {days_label}. ¡No te olvides! Llama al 211 para ayuda gratis. Corte: {court_address}",
        "reminder_3day": "¡Hola {name}! Tu fecha de corte es en {days_label}. ¡Prepárate! Llama al 211 o a tu abogado lo antes posible. Corte: {court_address}",
        "reminder_24hr": "¡URGENTE {name}! La corte es MAÑANA! ¡Llega a tiempo! Llama al 211 AHORA si necesitas ayuda. Corte: {court_address}",
        "reminder_morning_of": "¡URGENTE {name}! La corte es HOY! ¡No te la pierdas! Llama al 211 inmediatamente si necesitas ayuda. Corte: {court_address}"
    }
}


def build_deadline_reminder(
    name: str,
    days_label: str,
    court_address: str,
    language: Literal["EN", "ES"] = "EN"
) -> str:
    template_key = "reminder_morning_of"
    if "day" in days_label.lower() or "days" in days_label.lower():
        if "7" in days_label:
            template_key = "reminder_7day"
        elif "3" in days_label:
            template_key = "reminder_3day"
    elif "tomorrow" in days_label.lower() or "24" in days_label:
        template_key = "reminder_24hr"
    
    return TEMPLATES[language][template_key].format(
        name=name, days_label=days_label, court_address=court_address
    )
