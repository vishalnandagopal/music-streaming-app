def hasher(text: str) -> str:
    """
    Takes a UTF-8 encoded piece of text of any length, and returns the SHA-256 hash of the text as a string object, in uppercase.
    """
    from hashlib import sha256

    return sha256(bytes(text, "utf-8")).hexdigest().upper()
