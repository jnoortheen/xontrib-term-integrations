import sys

from xonsh.built_ins import XSH
from xonsh.environ import Env
from .utils import Codes


class ShellIntegration:
    def __init__(self, env: "Env"):
        self.env = env
        self.old_prompt = env["PROMPT"]

    def __call__(self, **_):
        prompt = self.old_prompt() if callable(self.old_prompt) else self.old_prompt
        prefix, suffix = [
            ansi_esc(form())
            for form in [form_term_prompt_prefix, form_term_prompt_suffix]
        ]
        return prefix + prompt + suffix


def ansi_esc(code: str):
    return "\001" + code + "\002"


def term_mark(code):
    return f"{Codes.OSC}133;{code}{Codes.ST}"


def term_osc_cmd(code):
    return f"{Codes.OSC}1337;{code}{Codes.ST}"


def form_term_prompt_prefix():
    return term_mark(f"A")


def form_term_prompt_suffix():
    return term_mark(f"B")


def write_to_out(code):
    sys.stdout.write(code)
    sys.stdout.flush()


def write_iterm2_output_prefix():
    return write_to_out(term_mark(f"C"))


def write_iterm2_status(status):
    return write_to_out(term_mark(f"D;{status}"))


@XSH.builtins.events.on_precommand
def iterm_precmd(**_):
    """write before starting to print out the output from the command"""
    write_iterm2_output_prefix()


# Inform iTerm2 of command success/failure here
@XSH.builtins.events.on_postcommand
def iterm_postcmd(rtn=0, **_):
    write_iterm2_status(rtn)


@XSH.builtins.events.on_chdir
def onchdir(olddir, newdir, **_):
    # OSC 1337 ; CurrentDir=[current directory] ST
    write_to_out(term_osc_cmd(f"CurrentDir={newdir}"))


@XSH.builtins.events.on_post_init
def onpostinit(**__):
    # OSC 1337 ; ShellIntegrationVersion=[Pn] ; [Ps] ST
    write_to_out(term_osc_cmd(f"ShellIntegrationVersion=15;shell=xonsh"))

    env = XSH.env or {}
    user = env.get("USER")
    host = env.get("HOSTNAME")
    if user and host:
        write_to_out(term_osc_cmd(f"RemoteHost={user}@{host}"))


XSH.env["PROMPT"] = ShellIntegration(XSH.env)
