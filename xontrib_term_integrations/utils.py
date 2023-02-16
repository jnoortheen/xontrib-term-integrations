import base64
import sys
from typing import Optional

from xonsh.built_ins import XSH
from xonsh.environ import Env

envx = XSH.env or {}


class Codes:
    # https://iterm2.com/documentation-escape-codes.html equivalents
    ESC = "\x1b"  # Escape, starts all the escape sequences
    BEL = "\x07"  # Bell
    ST = ESC + "\\"  # 0x9C String Terminator: terminates S in other controls
    OSC = ESC + "]"  # \x5d Operating System Command
    CSI = ESC + "["  #      Control Sequence Introducer
    DCS = ESC + "P"  # 0x90 Device Control String (terminated by ST)
    # User-Defined Keys; get/set Termcap/Terminfo data


class ShellIntegrationPrompt:
    def __init__(
        self,
        env: "Env",
        prompt_name="PROMPT",
        extend=False,
        ext_opt: Optional[dict] = None,
    ):
        self.env = env
        self.extend = extend
        self.ext_opt = ext_opt or {}
        self.prompt_name = prompt_name
        self.old_prompt = env[prompt_name]

    def __call__(self, **_):
        prompt = self.old_prompt() if callable(self.old_prompt) else self.old_prompt
        if not self.extend:
            prefix, suffix = (
                form() for form in [form_term_prompt_prefix, form_term_prompt_suffix]
            )
        else:
            if self.prompt_name == "PROMPT":
                prefix = (
                    SemanticPrompt.line_new_cmd_new(self.ext_opt)
                    + SemanticPrompt.prompt_start_primary()
                )
                suffix = SemanticPrompt.prompt_end_input_start()
            elif (
                self.prompt_name == "RIGHT_PROMPT"
            ):  # todo: bugs https://github.com/wez/wezterm/issues/3115
                prefix = SemanticPrompt.prompt_start_right()
                suffix = "\n"  # spec mandates ending witn a ␤?
            elif self.prompt_name == "BOTTOM_TOOLBAR":
                prefix = SemanticPrompt.prompt_start_secondary()
                suffix = ""  # ... ␤ bugs and adds and extra empty line
            elif (
                self.prompt_name == "MULTILINE_PROMPT"
            ):  # todo: bugs https://github.com/xonsh/xonsh/issues/5058
                prefix = SemanticPrompt.prompt_start_continue()
                prefix = ""
                suffix = ""
            else:
                return prompt
        prefix = (
            ansi_esc(prefix) if prefix else ""
        )  # don't escape empty pre/suf-fix (breaks multiline prompts)
        suffix = ansi_esc(suffix) if suffix else ""
        return prefix + prompt + suffix


class SemanticPrompt:
    # Splits prompt into Input, Output, Prompt semantic zones with OSC 133
    # gitlab.freedesktop.org/Per_Bothner/specifications/blob/master/
    # proposals/semantic-prompts.md

    @staticmethod
    def osc_cmd(prefix, opt):
        opt_s = opt_dict_to_str(opt)
        return f"{Codes.OSC}133;{prefix}{opt_s}{Codes.BEL}"

    @staticmethod
    def line_new():
        # OSC "133;L\007" Do a fresh-line: If the cursor is the initial column
        # (left, assuming left-to-right writing), do nothing
        # Otherwise, do the equivalent of "\r\n"
        return SemanticPrompt.osc_cmd("L", {})

    @staticmethod
    def line_new_cmd_new(opt=None):  # form_term_prompt_prefix, but with opt
        opt = opt or {}
        # OSC "133;A" options "\007" First do a fresh-line.
        # Then start a new command, and enter prompt mode
        return SemanticPrompt.osc_cmd("A", opt)

    @staticmethod
    def line_new_cmd_new_kill_old(opt=None):
        opt = opt or {}
        # OSC "133;N" options "\007" Same as OSC "133;A"
        # but may first implicitly terminate a previous command
        return SemanticPrompt.osc_cmd("N", opt)

    @staticmethod
    def prompt_start(opt=None):
        opt = opt or {"k": "i"}
        # OSC "133;P" options "\007" Explicit start of prompt.
        # Optional after  'A' or 'N'
        # 'k' (kind) option specifies the type of prompt: ↓
        return SemanticPrompt.osc_cmd("P", opt)

    @staticmethod
    def prompt_start_primary():
        return SemanticPrompt.prompt_start(
            {"k": "i"}
        )  # 'i'nitial regular primary prompt (default)

    @staticmethod
    def prompt_start_right():
        return SemanticPrompt.prompt_start({"k": "r"})  # 'r'ight-side

    @staticmethod
    def prompt_start_continue():
        return SemanticPrompt.prompt_start(
            {"k": "c"}
        )  # 'c'ontinuation (can edit previous lines)

    @staticmethod
    def prompt_start_secondary():
        return SemanticPrompt.prompt_start({"k": "s"})  # 's'econdary

    @staticmethod
    def prompt_end_input_start(opt=None):
        opt = opt or {}
        # form_term_prompt_suffix, but with opt
        # OSC "133;B" options "\007" End of prompt and start of user input,
        # terminated by a OSC "133;C" or another prompt (OSC "133;P").
        return SemanticPrompt.osc_cmd("B", opt)

    @staticmethod
    def prompt_end_input_start_nl(opt=None):
        opt = opt or {}
        # OSC "133;I" options "\007" End of prompt and start of user input,
        # terminated by EOL
        return SemanticPrompt.osc_cmd("I", opt)

    @staticmethod
    def input_end_output_start(opt=None):
        opt = opt or {}
        # write_osc_output_prefix, but with opt
        # OSC "133;C" options "\007" End of input, and start of output
        return SemanticPrompt.osc_cmd("C", opt)

    @staticmethod
    def cmd_end(opt=None):  # write_osc_cmd_status   , but with opt
        opt = opt or {}
        # OSC "133;D" [";" exit-code _options ]"\007" End of current command
        return SemanticPrompt.osc_cmd("D", opt)

    # helper printer functions
    @staticmethod
    def write_input_end_output_start(opt=None):
        opt = opt or {}
        write_to_out(SemanticPrompt.input_end_output_start(opt))

    @staticmethod
    def write_cmd_end(opt=None):
        opt = opt or {}
        write_to_out(SemanticPrompt.cmd_end(opt))


def opt_dict_to_str(opt):
    # convert options dictionary to `options ::= (";" option)*`, where
    # option is a simple string when dictionary value is 'None'
    # option is a `named-option ::= option-name "=" value` otherwise
    # (allows for named options with empty string values when dictionary value is '')
    if not type(opt) == dict:
        return ""
    if s := ";".join(
        [str(k) + ("=" + str(v) if v is not None else "") for k, v in opt.items()]
    ):
        return ";" + s
    return ""


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


def esc_esc(code):  # doubles ESC (or escapes ESC with another ESC)
    return code.replace(Codes.ESC, Codes.ESC + Codes.ESC)


def form_term_prompt_prefix():
    # FTCS_PROMPT        Sent just before start of shell prompt
    # OSC 133 ; A ST
    return term_mark("A")


def form_term_prompt_suffix():
    # FTCS_COMMAND_START Sent just after end of shell prompt,
    # before the user-entered command
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
    #         [Ps] is a file URL with a hostname and a path
    #         like file://example.com/usr/bin
    write_osc7_cmd(f"file://{host}{newdir}")


def write_osc_user_host(env):
    user = env.get("USER")
    host = env.get("HOSTNAME")
    if user and host:
        write_osc_cmd(f"RemoteHost={user}@{host}")


def set_user_var(
    var, val
):  # emit an OSC 1337 sequence to set a user var associated with the current
    # terminal pane
    val_b = val.encode("ascii")
    val_b64 = base64.b64encode(val_b)
    val_s64 = val_b64.decode("ascii")
    user_var = f"SetUserVar={var}={val_s64}"
    if envx.get("TMUX", ""):
        # github.com/tmux/tmux/wiki/FAQ
        # #what-is-the-passthrough-escape-sequence-and-how-do-i-use-it
        # Add "set -g allow-passthrough on" to your tmux.conf
        write_tmux_cmd(term_osc_cmd(user_var))
    else:
        write_osc_cmd(user_var)
