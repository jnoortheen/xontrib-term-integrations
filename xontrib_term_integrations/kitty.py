from xonsh.built_ins import XSH
from xonsh.completers.completer import add_one_completer

from . import kitty_completions, utils


@XSH.builtins.events.on_precommand
def iterm_precmd(**_):
    """write before starting to print out the output from the command"""
    utils.write_osc_output_prefix()


# Inform iTerm2 of command success/failure here
@XSH.builtins.events.on_postcommand
def iterm_postcmd(rtn=0, **_):
    utils.write_osc_cmd_status(rtn)


@XSH.builtins.events.on_chdir
def onchdir(olddir, newdir, **_):
    utils.write_osc_cwd(newdir)


@XSH.builtins.events.on_post_init
def onpostinit(**__):
    env = XSH.env or {}
    utils.write_osc_shell_integration()
    utils.write_osc_user_host(env)


def ps2_multiline_prompt():
    """a callable that prints out OSC tokens as well"""
    utils.write_term_mark("A;k=s")
    return "."


XSH.env["PROMPT"] = utils.ShellIntegrationPrompt(XSH.env)
XSH.env["MULTILINE_PROMPT"] = ps2_multiline_prompt

add_one_completer("kitty", kitty_completions.xonsh_complete, loc="<import")
