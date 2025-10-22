"""
Error Handling and Recovery Utilities for Chess Mover Machine

Provides centralized error handling, logging, and recovery strategies.
"""

import functools
import traceback
import time
from typing import Callable, Optional, TypeVar, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(Enum):
    """Error categories for better handling."""
    HARDWARE = "hardware"          # Serial, gantry, servo errors
    NETWORK = "network"            # Supabase, API errors
    CHESS_LOGIC = "chess_logic"    # Invalid moves, board state errors
    FILE_IO = "file_io"            # File read/write errors
    VISION = "vision"              # Camera, detection errors
    USER_INPUT = "user_input"      # Invalid user inputs
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Detailed error information."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    timestamp: datetime = None
    recoverable: bool = True
    recovery_action: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def __str__(self) -> str:
        parts = [
            f"[{self.severity.value}]",
            f"[{self.category.value}]",
            f"{self.message}"
        ]

        if self.exception:
            parts.append(f"({type(self.exception).__name__}: {str(self.exception)})")

        if self.recovery_action:
            parts.append(f"Recovery: {self.recovery_action}")

        return " ".join(parts)


class ErrorHandler:
    """
    Centralized error handler with logging and recovery.

    Features:
    - Error categorization and severity levels
    - Automatic recovery suggestions
    - Error history tracking
    - Customizable logging
    """

    def __init__(self, log_fn: Callable[[str], None] = print, max_history: int = 100):
        self.log = log_fn
        self.max_history = max_history
        self.error_history: list[ErrorInfo] = []
        self.error_callbacks: dict[ErrorCategory, list[Callable[[ErrorInfo], None]]] = {}

    def handle_error(
        self,
        error: Exception,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = True,
        recovery_action: Optional[str] = None
    ) -> ErrorInfo:
        """
        Handle an error with proper logging and categorization.

        Args:
            error: The exception that occurred
            message: Human-readable error message
            category: Error category
            severity: Error severity level
            recoverable: Whether error is recoverable
            recovery_action: Suggested recovery action

        Returns:
            ErrorInfo object containing error details
        """
        error_info = ErrorInfo(
            category=category,
            severity=severity,
            message=message,
            exception=error,
            recoverable=recoverable,
            recovery_action=recovery_action
        )

        # Log error
        self.log(str(error_info))

        # Log stack trace for critical errors
        if severity == ErrorSeverity.CRITICAL:
            self.log("Stack trace:")
            self.log(traceback.format_exc())

        # Add to history
        self._add_to_history(error_info)

        # Trigger callbacks
        self._trigger_callbacks(error_info)

        return error_info

    def handle_error_simple(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recovery_action: Optional[str] = None
    ) -> ErrorInfo:
        """
        Handle an error without an exception object.

        Args:
            message: Error message
            category: Error category
            severity: Error severity level
            recovery_action: Suggested recovery action

        Returns:
            ErrorInfo object
        """
        error_info = ErrorInfo(
            category=category,
            severity=severity,
            message=message,
            recoverable=True,
            recovery_action=recovery_action
        )

        self.log(str(error_info))
        self._add_to_history(error_info)
        self._trigger_callbacks(error_info)

        return error_info

    def register_callback(self, category: ErrorCategory, callback: Callable[[ErrorInfo], None]):
        """
        Register a callback for specific error categories.

        Args:
            category: Error category to watch
            callback: Function to call when error occurs
        """
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)

    def _trigger_callbacks(self, error_info: ErrorInfo):
        """Trigger registered callbacks for error category."""
        callbacks = self.error_callbacks.get(error_info.category, [])
        for callback in callbacks:
            try:
                callback(error_info)
            except Exception as e:
                self.log(f"[ERROR] Callback failed: {e}")

    def _add_to_history(self, error_info: ErrorInfo):
        """Add error to history, maintaining max size."""
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

    def get_recent_errors(self, count: int = 10, category: Optional[ErrorCategory] = None) -> list[ErrorInfo]:
        """
        Get recent errors from history.

        Args:
            count: Number of errors to retrieve
            category: Optional category filter

        Returns:
            List of recent ErrorInfo objects
        """
        errors = self.error_history

        if category:
            errors = [e for e in errors if e.category == category]

        return errors[-count:]

    def clear_history(self):
        """Clear error history."""
        self.error_history.clear()
        self.log("[ERROR] Error history cleared")

    def get_error_summary(self) -> dict[ErrorCategory, int]:
        """
        Get summary of errors by category.

        Returns:
            Dictionary mapping categories to error counts
        """
        summary = {}
        for error in self.error_history:
            category = error.category
            summary[category] = summary.get(category, 0) + 1
        return summary


# Type variable for generic decorator
T = TypeVar('T')


def with_error_handling(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    default_return: Any = None,
    retry_count: int = 0,
    retry_delay: float = 1.0,
    recovery_message: Optional[str] = None
):
    """
    Decorator to add error handling to functions.

    Args:
        category: Error category
        severity: Error severity
        default_return: Value to return on error
        retry_count: Number of retry attempts
        retry_delay: Delay between retries (seconds)
        recovery_message: Custom recovery message

    Example:
        @with_error_handling(category=ErrorCategory.HARDWARE, retry_count=3)
        def move_gantry(x, y):
            # Function that might fail
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < retry_count:
                        # Retry
                        print(f"[RETRY] Attempt {attempt + 1}/{retry_count} failed, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        # Final failure
                        error_msg = f"Function '{func.__name__}' failed: {str(e)}"
                        if retry_count > 0:
                            error_msg += f" (after {retry_count} retries)"

                        error_handler = ErrorHandler()
                        error_handler.handle_error(
                            error=e,
                            message=error_msg,
                            category=category,
                            severity=severity,
                            recovery_action=recovery_message
                        )

                        return default_return

            return default_return

        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    error_handler: Optional[ErrorHandler] = None,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Positional arguments for function
        error_handler: ErrorHandler instance (creates new if None)
        category: Error category
        default_return: Value to return on error
        **kwargs: Keyword arguments for function

    Returns:
        Function result or default_return on error

    Example:
        result = safe_execute(risky_function, arg1, arg2,
                            category=ErrorCategory.HARDWARE,
                            default_return=False)
    """
    if error_handler is None:
        error_handler = ErrorHandler()

    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(
            error=e,
            message=f"Function '{func.__name__}' failed",
            category=category
        )
        return default_return


class RetryStrategy:
    """Configurable retry strategy for operations."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay

    def execute(
        self,
        func: Callable,
        *args,
        error_handler: Optional[ErrorHandler] = None,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        **kwargs
    ) -> tuple[bool, Any]:
        """
        Execute function with retry strategy.

        Args:
            func: Function to execute
            *args: Positional arguments
            error_handler: Optional error handler
            category: Error category
            **kwargs: Keyword arguments

        Returns:
            Tuple of (success: bool, result: Any)
        """
        if error_handler is None:
            error_handler = ErrorHandler()

        delay = self.initial_delay
        last_error = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 1:
                    error_handler.log(f"[RETRY] Success on attempt {attempt}")
                return (True, result)

            except Exception as e:
                last_error = e

                if attempt < self.max_attempts:
                    error_handler.log(
                        f"[RETRY] Attempt {attempt}/{self.max_attempts} failed: {str(e)}"
                    )
                    error_handler.log(f"[RETRY] Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    error_handler.handle_error(
                        error=e,
                        message=f"Function '{func.__name__}' failed after {self.max_attempts} attempts",
                        category=category,
                        severity=ErrorSeverity.ERROR
                    )

        return (False, None)


# Global error handler instance
global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return global_error_handler
