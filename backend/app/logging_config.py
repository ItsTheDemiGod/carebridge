"""Central logging policy: only random ids, state transitions, timings, HTTP status codes and error codes are ever logged.

Enforced by a filter on every handler: exception tracebacks (their messages can contain user content) are reduced to the exception TYPE, and the
uvicorn access log loses its query string (a formulary search term is user text)."""
import logging

POLICY = "ids, states, timings, status codes and error codes only"


class PolicyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info:
            record.msg = f"{record.getMessage()} [exception type={record.exc_info[0].__name__}]"
            record.args, record.exc_info, record.exc_text, record.stack_info = None, None, None, None
        if record.name == "uvicorn.access" and isinstance(record.args, tuple) and len(record.args) >= 3:
            a = list(record.args)
            a[2] = str(a[2]).split("?", 1)[0]
            record.args = tuple(a)
        return True


def setup(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers:
        if not any(isinstance(f, PolicyFilter) for f in h.filters):
            h.addFilter(PolicyFilter())
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        for h in logging.getLogger(name).handlers:
            if not any(isinstance(f, PolicyFilter) for f in h.filters):
                h.addFilter(PolicyFilter())
    logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx logs full URLs at INFO
