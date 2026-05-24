import logging
import json


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

for noisy_logger in ("httpx", "httpcore", "supabase", "gotrue", "websockets"):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_clinical_event(event_type: str, **fields) -> None:
    payload = {"event_type": event_type, **fields}
    logging.getLogger("clinical_audit").info(json.dumps(payload, default=str, sort_keys=True))
