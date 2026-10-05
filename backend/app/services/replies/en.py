"""Approved English automatic reply templates."""

TEMPLATES = {
    "confirm_thanks": (
        "Thank you, {{donor_name}}. Your visit is confirmed for {{appointment_date}} at "
        "{{center_name}}. Please eat well and drink plenty of water before donating."
    ),
    "reschedule_offer": (
        "No problem. Here are the next available times. Please choose one, or type a day "
        "that suits you."
    ),
    "reschedule_confirmed": (
        "Done. Your new visit is booked for {{appointment_date}} at {{center_name}}. "
        "Thank you, {{donor_name}}."
    ),
    "decline_ask_reason": (
        "We understand, {{donor_name}}. May we know the reason? This helps us contact you "
        "at a better time."
    ),
    "decline_closing": "Thank you for letting us know. We will reach out again later. Take care.",
    "needs_call": "Thank you. A coordinator from Team Indus will contact you shortly.",
    "no_slots": "Our coordinator will call you to find a suitable time.",
}
