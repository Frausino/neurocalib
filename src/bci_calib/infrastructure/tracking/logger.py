# infrastructure/tracking/logger.py
"""Structured logging (Registro Estruturado de Logs) configuration for bci-calib.

Provides ``configure_logging()``, that sets up structlog with contextvars
support, silences mne/moabb verbosity, and selects ConsoleRenderer
(development) or JSONRenderer (production) via the LOG_FORMAT env var.

Design decisions
----------------
1. ``merge_contextvars`` is placed first in the processor chain so that
   the correlation_id bound by ``mlflow_tracker.start_run()`` propagates
   automatically to every log line emitted during a run. This follows the
   structlog contextvars pattern documented in [1].

2. ``cache_logger_on_first_use=True`` is essential for performance in tight
   calibration loops: after the first ``get_logger()`` call the chain is
   frozen and further processor lookups are O(1). Calling
   ``configure_logging()`` again resets the cache.

3. ``force=True`` in ``logging.basicConfig()`` prevents the common failure
   mode where a third-party library calls ``basicConfig()`` before our code,
   leaving stdlib handlers misconfigured.

References
----------
[1] structlog 24.x docs, contextvars:
    https://www.structlog.org/en/stable/contextvars.html
[2] structlog processors reference:
    https://www.structlog.org/en/stable/api.html#processors
"""

from __future__ import annotations

import logging
import os

import structlog
from structlog.contextvars import merge_contextvars

# Third-party loggers whose DEBUG/INFO output is irrelevant during calibration.
# Raised to WARNING so they appear only on genuine problems.
_NOISY_LIBS: tuple[str, ...] = ("mne", "moabb")


def configure_logging(
    log_level: str = "INFO",
    renderer: str | None = None,
) -> None:
    """Configure structlog and stdlib logging for the entire process.

    Parameters
    ----------
    log_level:
        Minimum severity to emit. Accepts any stdlib logging name:
        ``"DEBUG"``, ``"INFO"``, ``"WARNING"``, ``"ERROR"``, ``"CRITICAL"``.
        Default: ``"INFO"``.
    renderer:
        Force a specific renderer: ``"json"`` or ``"console"``. When
        ``None``, the env var ``LOG_FORMAT`` is read; if absent or not
        ``"json"``, ConsoleRenderer is used (suitable for development and
        PowerShell terminals).

    Side Effects
    ------------
    - Sets ``logging.getLogger("mne")`` and ``logging.getLogger("moabb")``
      to ``WARNING``.
    - Calls ``structlog.configure()`` globally. The call is idempotent when
      ``log_level`` and ``renderer`` are unchanged because structlog caches
      the frozen chain; changing either parameter resets the cache
      automatically via ``structlog.reset_defaults()`` before reconfiguring.
    - Calls ``logging.basicConfig()`` with ``force=True`` for stdlib interop.

    Examples
    --------
    Development (PowerShell, coloured output)::

        from infrastructure.tracking.logger import configure_logging
        configure_logging()

    Production / CI (JSON, parseable by log aggregators)::

        LOG_FORMAT=json uv run python pipeline.py
        # or programmatically:
        configure_logging(renderer="json")
    """
    # 1. Silence third-party loggers that generate calibration noise.
    for lib in _NOISY_LIBS:
        logging.getLogger(lib).setLevel(logging.WARNING)

    # 2. Resolve numeric level early; used both by structlog and stdlib.
    numeric_level: int = getattr(logging, log_level.upper(), logging.INFO)

    # 3. Determine renderer from argument > env var > default (console).
    use_json: bool = (renderer == "json") or (
        os.getenv("LOG_FORMAT", "").lower() == "json"
    )

    # 4. Build the processor chain.
    #    Order is mandatory: contextvars first, renderer last.
    processors: list[structlog.types.Processor] = [
        merge_contextvars,  # inject correlation_id etc.
        structlog.processors.add_log_level,  # add "level" key
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # ISO-8601 UTC
        structlog.processors.StackInfoRenderer(),  # stack_info= kwarg support
        structlog.processors.ExceptionRenderer(),  # exc_info= kwarg support
    ]
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # 5. Reset then reconfigure (allows safe repeated calls in tests).
    structlog.reset_defaults()
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 6. Stdlib basicConfig for any handler not routing through structlog.
    logging.basicConfig(
        format="%(message)s",
        level=numeric_level,
        force=True,
    )
