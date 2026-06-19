from contextlib import contextmanager
import sentry_sdk
from typing import Any


@contextmanager
def trace_span(operation: str, **tags: Any):
    with sentry_sdk.start_span(op=operation) as span:
        for key, value in tags.items():
            span.set_tag(key, value)
        yield
