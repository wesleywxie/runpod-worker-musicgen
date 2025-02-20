from urllib.parse import urlparse


def is_valid_url(s: str) -> bool:
    """
    Check if a string is a valid URL.

    Args:
        s (str): The string to check.

    Returns:
        bool: True if the string is a valid URL, False otherwise.
    """
    if not s:
        return False
    try:
        result = urlparse(s)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
