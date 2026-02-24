import re
from functools import wraps

from xonsh.built_ins import XSH

from . import utils
from .semantic_prompt import ShellIntegrationPrompt, line_new_cmd_new

ghostty_shell_features = XSH.env["GHOSTTY_SHELL_FEATURES"].split(",")


@XSH.builtins.events.on_precommand
def iterm_precmd(**_):
    """write before starting to print out the output from the command"""
    utils.write_osc_output_prefix()


@XSH.builtins.events.on_postcommand
def iterm_postcmd(cmd, rtn, **_):
    utils.write_osc_cmd_status(rtn)


@XSH.builtins.events.on_chdir
def onchdir(olddir, newdir, **_):
    utils.write_osc7_cwd(XSH.env["HOSTNAME"], newdir)


def get_adjusted_prompt(prompt_function):
    """
    Same workaround as for bash ghostty integration:
    # bash doesn't redraw the leading lines in a multiline prompt
    # so we mark the start of each line (after each newline) as a secondary prompt;
    # this correctly handles multiline prompts by setting the first to primary
    # and the subsequent lines to secondary.
    """

    @wraps(prompt_function)
    def wrapper():
        prompt = prompt_function()
        return re.sub("(?<=\n)", f"\x01{line_new_cmd_new({'k': 's'})}\x02", prompt)

    return wrapper


XSH.env["PROMPT"] = get_adjusted_prompt(ShellIntegrationPrompt(XSH.env))
