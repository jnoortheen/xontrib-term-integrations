import sys
import base64

from xonsh.environ import Env
from xonsh.built_ins import XSH

envx = XSH.env or {}

class Codes:
    # https://iterm2.com/documentation-escape-codes.html equivalents
    ESC = "\x1b"     # Escape, starts all the escape sequences
    BEL = "\x07"     # Bell
    ST  = ESC + "\\" # 0x9C String Terminator: terminates strings in other controls
    OSC = ESC + "]"  # \x5d Operating System Command
    CSI = ESC + "["  #      Control Sequence Introducer
    DCS = ESC + "P"  # 0x90 Device Control String (terminated by ST): User-Defined Keys; get/set Termcap/Terminfo data

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
    return f"{Codes.OSC}133;{code}{Codes.BEL}"


def term_osc_cmd(code):
    return f"{Codes.OSC}1337;{code}{Codes.BEL}"


def term_osc7_cmd(code):
    return f"{Codes.OSC}7;{code}{Codes.ST}"


def term_dcs_cmd(code):
    return f"{Codes.DCS}{code}{Codes.ST}"


def term_tmux_cmd(code):
    # github.com/tmux/tmux/wiki/FAQ#what-is-the-passthrough-escape-sequence-and-how-do-i-use-it
    # ESC in the wrapped sequence must be doubled
    return term_dcs_cmd(esc_esc(code))


def esc_esc(code): # doubles ESC (or escapes ESC with another ESC)
    return code.replace(Codes.ESC, Codes.ESC+Codes.ESC)


def form_term_prompt_prefix():
    # FTCS_PROMPT        Sent just before start of shell prompt
    # OSC 133 ; A ST
    return term_mark("A")


def form_term_prompt_suffix():
    # FTCS_COMMAND_START Sent just after end of shell prompt, before the user-entered command
    # OSC 133 ; B ST
    return term_mark("B")


def write_term_mark(code):
    return write_to_out(term_mark(code))


def write_osc_cmd(code):
    return write_to_out(term_osc_cmd(code))


def write_osc7_cmd(code):
    return write_to_out(term_osc7_cmd(code))


def write_dcs_cmd(code):
    return write_to_out(term_dcs_cmd(code))


def write_tmux_cmd(code):
    return write_to_out(term_tmux_cmd(code))


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


def write_osc7_cwd(host, newdir):
    # OSC 7 ; [Ps] ST
    #         [Ps] is a file URL with a hostname and a path, like file://example.com/usr/bin
    write_osc7_cmd(f"file://{host}{newdir}")

def write_osc_user_host(env):
    user = env.get("USER")
    host = env.get("HOSTNAME")
    if user and host:
        write_osc_cmd(f"RemoteHost={user}@{host}")

def set_user_var(var, val): # emit an OSC 1337 sequence to set a user var associated with the current terminal pane
    val_b   = val.encode('ascii')
    val_b64 = base64.b64encode(val_b)
    val_s64 = val_b64.decode('ascii')
    user_var = f"SetUserVar={var}={val_s64}"
    if envx.get("TMUX", ''):
        # github.com/tmux/tmux/wiki/FAQ#what-is-the-passthrough-escape-sequence-and-how-do-i-use-it
        # Add "set -g allow-passthrough on" to your tmux.conf
        write_tmux_cmd(term_osc_cmd(user_var))
    else:
        write_osc_cmd(user_var)
