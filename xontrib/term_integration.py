import os

from xonsh.built_ins import XSH

# don't export any to xonsh context
__all__ = ()

env = XSH.env or {}

# load during interactive sessions only
if env.get("XONSH_INTERACTIVE", False):
    if ("kitty" in os.getenv("TERMINFO", "")) or ("kitty" in os.getenv("TERM", "")):
        import xontrib_term_integrations.kitty  # noqa
    else:
        # fallback
        # if "iTerm" in os.getenv("TERM_PROGRAM", ""):
        import xontrib_term_integrations.iterm2  # noqa
