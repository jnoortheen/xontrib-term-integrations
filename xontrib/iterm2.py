import sys
from xonsh.built_ins import XSH
from xonsh.environ import Env

ITERM2_PREEXEC = "\033]133;C;\007"


class ShellIntegration:
    def __init__(self, env: "Env"):
        self.env = env
        self.old_prompt = env["PROMPT"]

    def __call__(self, **_):
        prompt = self.old_prompt() if callable(self.old_prompt) else self.old_prompt
        prefix, suffix = [
            ansi_esc(form())
            for form in [form_iterm2_prompt_prefix, form_iterm2_prompt_suffix]
        ]
        return prefix + prompt + suffix


def ansi_esc(code: str):
    return "\001" + code + "\002"


def iterm2_esc(code):
    return f"\x1b\x5d133;{code}\007"


def form_iterm2_prompt_prefix():
    return iterm2_esc(f"A")


def form_iterm2_prompt_suffix():
    return iterm2_esc(f"B")


def write_to_out(code):
    sys.stdout.write(code)
    sys.stdout.flush()


def write_iterm2_output_prefix():
    return write_to_out(iterm2_esc(f"C"))


def write_iterm2_status(status):
    return write_to_out(iterm2_esc(f"D;{status}"))


@XSH.builtins.events.on_precommand
def iterm_precmd(**_):
    """write before starting to print out the output from the command"""
    write_iterm2_output_prefix()


# Inform iTerm2 of command success/failure here
@XSH.builtins.events.on_postcommand
def iterm_postcmd(rtn=0, **_):
    write_iterm2_status(rtn)


XSH.env["PROMPT"] = ShellIntegration(XSH.env)
