"""Typed AI failures -- the other half of the fail-loud policy.

planv0.2.md section 2 and section 7: `cache -> live -> RAISE`. Nothing in this
package ever substitutes a fixture, a placeholder or a "best effort" answer
when a provider misbehaves. The UI renders a *designed* error state instead,
which is why every error here carries a `kind` that maps onto
contracts.viewmodels.ErrorPartialVM.

Three failure modes are meaningfully different to a user, so they are three
types rather than one:

  ProviderUnreachable  nothing answered, or answered with a transport error.
  Timeout              something answered too late to be useful.
  SchemaViolation      something answered, twice, with data we cannot trust.

SchemaViolation is the interesting one: it means the model returned prose or
the wrong shape even after one corrective retry (section 7, bullet 2). The raw
response is attached so a human can see exactly what came back.
"""

from __future__ import annotations

from contracts.viewmodels import ErrorPartialVM

# How much of a bad response to keep on the exception. Enough to diagnose,
# not enough to flood a log line or an error panel.
RAW_EXCERPT = 2000


class AIError(Exception):
    """Base for every failure this package raises deliberately."""

    kind: str = "provider_unreachable"
    title: str = "AI request failed"

    def __init__(self, message: str, *, fn_name: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.fn_name = fn_name

    @property
    def detail(self) -> str:
        return self.message

    def as_error_partial(self, retry_href: str | None = None) -> ErrorPartialVM:
        """Render as the frozen error contract. Never a stack trace on screen."""
        return ErrorPartialVM(
            title=self.title,
            detail=self.detail,
            retry_href=retry_href,
            kind=self.kind,
        )


class ProviderUnreachable(AIError):
    """The provider did not answer: no process, no network, no credentials.

    This is NOT a cue to fall back to another provider or to a fixture. The
    operator switches paths with an env var, by hand, or the demo runs on the
    warm cache. See planv0.2.md section 7, "Not automatic".
    """

    kind = "provider_unreachable"
    title = "AI provider unreachable"

    def __init__(
        self, provider: str, detail: str, *, fn_name: str | None = None
    ) -> None:
        super().__init__(f"provider '{provider}' unreachable: {detail}", fn_name=fn_name)
        self.provider = provider


class Timeout(AIError):
    kind = "timeout"
    title = "AI request timed out"

    def __init__(
        self,
        provider: str,
        seconds: float,
        *,
        fn_name: str | None = None,
    ) -> None:
        super().__init__(
            f"provider '{provider}' did not answer within {seconds:.0f}s",
            fn_name=fn_name,
        )
        self.provider = provider
        self.seconds = seconds


class SchemaViolation(AIError):
    """Two attempts, neither validated. Nothing is saved and nothing is shown.

    `attempts` is here so a reader can tell at a glance that the bounded retry
    actually fired -- it is 2 in normal operation.
    """

    kind = "schema_violation"
    title = "AI returned unusable data"

    def __init__(
        self,
        fn_name: str,
        schema: str,
        validation_error: str,
        raw: str,
        *,
        attempts: int = 2,
    ) -> None:
        super().__init__(
            f"{fn_name}: response did not validate against {schema} "
            f"after {attempts} attempts",
            fn_name=fn_name,
        )
        self.schema = schema
        self.validation_error = validation_error
        self.raw = raw[:RAW_EXCERPT]
        self.attempts = attempts

    @property
    def detail(self) -> str:
        return (
            f"{self.message}\n\nValidation error:\n{self.validation_error}"
            f"\n\nRaw response:\n{self.raw}"
        )
