from functools import wraps
from collections.abc import Callable

def handle_exceptions(stage: str):
    """Decorator to standardize error handling and logging for methods."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exception:
                error_msg = f"An error occurred during {stage} in {func.__name__}: {exception}"
                print(error_msg)
                # If the first argument is a class instance with a logger, use it
                if args and hasattr(args[0], 'logger') and args[0].logger:
                    args[0].logger.log(error_msg)
                return None

        return wrapper

    return decorator