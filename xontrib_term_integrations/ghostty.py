import re

from xonsh.built_ins import XSH

from . import utils
from .semantic_prompt import ShellIntegrationPrompt

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


def get_adjusted_prompt():
    prompt = ShellIntegrationPrompt(XSH.env)()
    return re.sub("(?<=\n)", "\x01\x1b]133;A;k=s\x07\x02", prompt)


XSH.env["PROMPT"] = get_adjusted_prompt()
