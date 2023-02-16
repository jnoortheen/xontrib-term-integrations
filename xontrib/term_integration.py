import os

from xonsh.built_ins import XSH

# don't export any to xonsh context
__all__ = ()

env = XSH.env or {}

# load during interactive sessions only
if env.get("XONSH_INTERACTIVE", False):
    TERMINFO = os.getenv("TERMINFO", "").lower()
    TERM = os.getenv("TERM", "").lower()
    TERM_PROGRAM = os.getenv("TERM_PROGRAM", "").lower()
    # avoid terminals that don't like OSC sequences
    if not TERM == "dumb" and not TERM == "linux":
        if ("kitty" in TERMINFO) or ("kitty" in TERM):
            import xontrib_term_integrations.kitty  # noqa
        elif (
            ("wezterm" in TERMINFO)
            or ("wezterm" in TERM)
            or ("wezterm" in TERM_PROGRAM)
        ):
            import xontrib_term_integrations.wezterm  # noqa

            # todo: fails in a root shell https://github.com/wez/wezterm/issues/3114
        else:
            # fallback
            # if "iTerm" in os.getenv("TERM_PROGRAM", ""):
            import xontrib_term_integrations.iterm2  # noqa
