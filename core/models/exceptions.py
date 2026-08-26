"""
Exceptions for the model abstraction layer.

Every provider must translate its own SDK's errors into these, so nothing
above this layer (agents, orchestrator, tools) ever needs to know which
provider raised what.
"""


class ModelError(Exception):
    """Base class for all model-layer errors."""


class ModelAuthError(ModelError):
    """Bad or missing API key / credentials."""


class ModelRateLimitError(ModelError):
    """Provider is rate-limiting us. Caller may retry with backoff."""


class ModelTimeoutError(ModelError):
    """Request took too long."""


class ModelUnavailableError(ModelError):
    """Provider is down, overloaded, or otherwise not serving requests."""


class ModelInvalidRequestError(ModelError):
    """Our request was malformed (bad schema, bad params, etc.)."""
