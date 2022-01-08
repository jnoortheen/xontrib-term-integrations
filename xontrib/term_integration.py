import os

__all__ = ()
if "iTerm" in os.getenv("TERM_PROGRAM", ""):
    import xontrib_term_integrations.iterm2  # noqa
elif ("kitty" in os.getenv("TERMINFO", "")) or ("kitty" in os.getenv("TERM", "")):
    import xontrib_term_integrations.kitty  # noqa
else:
    import warnings

    warnings.warn(
        "Shell integration is not loaded. "
        "Make sure that you are running inside one of the supported shells."
    )
