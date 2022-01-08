from xonsh.built_ins import XSH

from . import utils


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


XSH.env["PROMPT"] = utils.ShellIntegrationPrompt(XSH.env)
