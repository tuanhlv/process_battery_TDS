from contextlib import contextmanager

@contextmanager
def handle_api_errors():
    """Context manager to catch and cleanly log QuickBase API network and HTTP errors."""
    try:
        yield
    except requests.exceptions.HTTPError as e:
        # Catches 4xx and 5xx errors (e.g., Bad Request, Unauthorized, Server Error)
        print(f"[ERROR] QuickBase API rejected the request. HTTP {e.response.status_code}: {e.response.text}")
    except requests.exceptions.ConnectionError:
        # Catches DNS failures, refused connections, etc.
        print("[ERROR] Connection failed. Could not reach QuickBase. Check your network.")
    except requests.exceptions.Timeout:
        # Catches requests that hang indefinitely
        print("[ERROR] The QuickBase API request timed out.")
    except requests.exceptions.RequestException as e:
        # Catch-all for any other requests-related issues
        print(f"[ERROR] An unexpected network error occurred: {e}")