# Splits prompt into Input, Output, Prompt semantic zones with OSC 133
# gitlab.freedesktop.org/Per_Bothner/specifications/blob/master/
# proposals/semantic-prompts.md

from typing import TYPE_CHECKING, Optional

from .utils import (
    Codes,
    ansi_esc,
    form_term_prompt_prefix,
    form_term_prompt_suffix,
    opt_dict_to_str,
    write_to_out,
)

if TYPE_CHECKING:
    from xonsh.environ import Env


def osc_cmd(prefix: str, opt: dict):
    opt_s = opt_dict_to_str(opt)
    return f"{Codes.OSC}133;{prefix}{opt_s}{Codes.BEL}"


def line_new():
    # OSC "133;L\007" Do a fresh-line: If the cursor is the initial column
    # (left, assuming left-to-right writing), do nothing
    # Otherwise, do the equivalent of "\r\n"
    return osc_cmd("L", {})


def line_new_cmd_new(opt=None):  # form_term_prompt_prefix, but with opt
    opt = opt or {}
    # OSC "133;A" options "\007" First do a fresh-line.
    # Then start a new command, and enter prompt mode
    return osc_cmd("A", opt)


def line_new_cmd_new_kill_old(opt=None):
    opt = opt or {}
    # OSC "133;N" options "\007" Same as OSC "133;A"
    # but may first implicitly terminate a previous command
    return osc_cmd("N", opt)


def prompt_start(opt=None):
    opt = opt or {"k": "i"}
    # OSC "133;P" options "\007" Explicit start of prompt.
    # Optional after  'A' or 'N'
    # 'k' (kind) option specifies the type of prompt: ↓
    return osc_cmd("P", opt)


def prompt_start_primary():
    return prompt_start({"k": "i"})  # 'i'nitial regular primary prompt (default)


def prompt_start_right():
    return prompt_start({"k": "r"})  # 'r'ight-side


def prompt_start_continue():
    return prompt_start({"k": "c"})  # 'c'ontinuation (can edit previous lines)


def prompt_start_secondary():
    return prompt_start({"k": "s"})  # 's'econdary


def prompt_end_input_start(opt=None):
    opt = opt or {}
    # form_term_prompt_suffix, but with opt
    # OSC "133;B" options "\007" End of prompt and start of user input,
    # terminated by a OSC "133;C" or another prompt (OSC "133;P").
    return osc_cmd("B", opt)


def prompt_end_input_start_nl(opt=None):
    opt = opt or {}
    # OSC "133;I" options "\007" End of prompt and start of user input,
    # terminated by EOL
    return osc_cmd("I", opt)


def input_end_output_start(opt=None):
    opt = opt or {}
    # write_osc_output_prefix, but with opt
    # OSC "133;C" options "\007" End of input, and start of output
    return osc_cmd("C", opt)


def cmd_end(opt=None):  # write_osc_cmd_status   , but with opt
    opt = opt or {}
    # OSC "133;D" [";" exit-code _options ]"\007" End of current command
    return osc_cmd("D", opt)


# helper printer functions
def write_input_end_output_start(opt=None):
    opt = opt or {}
    write_to_out(input_end_output_start(opt))


def write_cmd_end(opt=None):
    opt = opt or {}
    write_to_out(cmd_end(opt))


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
                prefix = line_new_cmd_new(self.ext_opt) + prompt_start_primary()
                suffix = prompt_end_input_start()
            elif (
                self.prompt_name == "RIGHT_PROMPT"
            ):  # todo: bugs https://github.com/wez/wezterm/issues/3115
                prefix = prompt_start_right()
                suffix = "\n"  # spec mandates ending witn a ␤?
            elif self.prompt_name == "BOTTOM_TOOLBAR":
                prefix = prompt_start_secondary()
                suffix = ""  # ... ␤ bugs and adds and extra empty line
            elif self.prompt_name == "MULTILINE_PROMPT":
                env = self.env
                prefix, suffix = "", ""
                _pre, _pos = "MULTILINE_PROMPT_PRE", "MULTILINE_PROMPT_POS"
                if not (_pre_val := env.get(_pre)) and not _pre_val == "":
                    env[_pre] = ansi_esc(prompt_start_continue())
                if not (_pos_val := env.get(_pos)) and not _pos_val == "":
                    env[_pos] = ansi_esc(prompt_end_input_start())
            else:
                return prompt
        prefix = (
            ansi_esc(prefix) if prefix else ""
        )  # don't escape empty pre/suf-fix (breaks multiline prompts)
        suffix = ansi_esc(suffix) if suffix else ""
        return prefix + prompt + suffix
