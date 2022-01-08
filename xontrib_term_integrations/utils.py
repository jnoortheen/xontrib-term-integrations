import sys

from xonsh.environ import Env


class Codes:
    # https://iterm2.com/documentation-escape-codes.html equivalents
    ESC = "\x1b"
    ST = "\x07"
    OSC = ESC + "]"  # \x5d
    CSI = ESC + "["


class ShellIntegrationPrompt:
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
    return term_mark("A")


def form_term_prompt_suffix():
    return term_mark("B")


def write_term_mark(code):
    return write_to_out(term_mark(code))


def write_osc_cmd(code):
    return write_to_out(term_osc_cmd(code))


def write_osc_output_prefix():
    return write_term_mark("C")


def write_osc_cmd_status(status):
    return write_term_mark(f"D;{status}")


def write_to_out(code: str):
    sys.stdout.write(code)
    sys.stdout.flush()


def write_osc_shell_integration():
    # OSC 1337 ; ShellIntegrationVersion=[Pn] ; [Ps] ST
    write_osc_cmd("ShellIntegrationVersion=15;shell=xonsh")


def write_osc_cwd(newdir):
    # OSC 1337 ; CurrentDir=[current directory] ST
    write_osc_cmd(f"CurrentDir={newdir}")


def write_osc_user_host(env):
    user = env.get("USER")
    host = env.get("HOSTNAME")
    if user and host:
        write_osc_cmd(f"RemoteHost={user}@{host}")
