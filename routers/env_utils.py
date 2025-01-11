import os

def load_and_clean_env_var(var_name: str) -> str:
    """
    Loads an environment variable and removes any trailing or leading
    whitespace, including hidden \r\n from Windows line endings.
    """
    raw_val = os.getenv(var_name, "")
    # Remove leading/trailing spaces + common newline issues:
    raw_val = raw_val.strip()  
    # If there's any hidden carriage returns left, remove them:
    raw_val = raw_val.replace("\r", "").replace("\n", "")
    return raw_val
