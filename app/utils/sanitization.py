def sanitize_message(message: str) -> str:
    """Lightweight message sanitizer for debate inputs.

    Currently returns the input unchanged; place to add HTML escaping, length
    limits, or schema validation if needed.

    Args:
        message: Raw user text.

    Returns:
        str: Sanitized text.
    """
    return message
