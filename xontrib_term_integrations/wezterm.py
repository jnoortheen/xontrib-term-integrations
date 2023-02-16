# Hook up xonsh shell integration for WezTerm, but the sequences used are not WezTerm
# specific and may provide the same functionality for other terminals.
# Most terminals are good at ignoring OSC sequences that they don't understand,
# but if not there are some bypasses:
# WEZTERM_SHELL_SKIP_ALL            - disables all
# WEZTERM_SHELL_SKIP_SEMANTIC_ZONES - disables zones
# WEZTERM_SHELL_SKIP_CWD            - disables OSC 7 cwd setting
# WEZTERM_SHELL_SKIP_USER_VARS      - disable user vars that capture info about running
# programs
# How to test
# Set multiclick to select zones in WezTerm, then multiclick to see which areas select
# Use MoveForwardZoneOfType/MoveBackwardZoneOfType key bindings

import os
import subprocess
import sys

from xonsh.built_ins import XSH

from . import utils

env = XSH.env or {}
evalx = XSH.builtins.evalx

_skip_all = env.get("WEZTERM_SHELL_SKIP_ALL", False)
_skip_cwd = env.get("WEZTERM_SHELL_SKIP_CWD", False)
_skip_zone = env.get("WEZTERM_SHELL_SKIP_SEMANTIC_ZONES", False)
_skip_usr_var = env.get("WEZTERM_SHELL_SKIP_USER_VARS", False)

get_bin = XSH.commands_cache.locate_binary
get_bin_lazy = XSH.commands_cache.lazy_locate_binary


def _command(name, ignore_alias=False):
    """Find           command        in cache (including aliases)"""
    return get_bin_lazy(name, ignore_alias)


def isCmd(name, ignore_alias=False):
    """Test whether a command exists in cache (including aliases)"""
    return True if _command(name, ignore_alias) else False


if not _skip_all:

    def wezterm_write_osc7_cwd(newdir):
        host = env.get("HOSTNAME", "")
        utils.write_osc7_cwd(host, newdir)
        # ↓ don't see the point in a helper function
        # emits an OSC 7 sequence to inform the terminal
        # of the current working directory
        # It prefers to use a helper command provided by WezTerm if is installed,
        # but falls back to a simple command otherwise
        # if isCmd('wezterm') and\
        # (0 == evalx('wezterm set-working-directory 2>/dev/null').returncode):
        #    return
        # else:
        #    host = env.get("HOSTNAME", '')
        #    utils.write_osc7_cwd(host, newdir)

    if not _skip_zone:

        @XSH.builtins.events.on_precommand  # Fires just before a command is executed
        def wezterm_cmd_pre(cmd: str, **_):
            """Write before starting to print out the output from the command"""
            utils.SemanticPrompt.write_input_end_output_start()
            if not _skip_usr_var:
                utils.set_user_var(
                    "WEZTERM_PROG", cmd
                )  # tell WezTerm the full command that is being run

    @XSH.builtins.events.on_postcommand
    def wezterm_cmd_pos(rtn=0, **_):  # Inform WezTerm of command success/failure
        opt = {f"{rtn}": None, "aid": os.getpid()}
        utils.SemanticPrompt.write_cmd_end(opt)

    if not _skip_cwd:

        @XSH.builtins.events.on_chdir
        def onchdir(olddir, newdir, **_):
            wezterm_write_osc7_cwd(newdir)

    if not _skip_usr_var:

        @XSH.builtins.events.on_pre_prompt  # Fires just before showing the prompt
        def wezterm_prompt_pre():
            """Write before starting to print out the output from the command"""
            # get Xonsh available prompt fields
            promptx = env.get("PROMPT_FIELDS", [])

            # 1 tell WezTerm that no command is being run
            utils.set_user_var("WEZTERM_PROG", "")

            # 2 tell WezTerm the username
            if user_xon := promptx["user"] if "user" in promptx else None:
                user = user_xon
            else:  # fallback to capturing `id -un` ??? likely never needed
                full_cmd = ["id", "-un"]
                proc = subprocess.run(full_cmd, capture_output=True)
                out = proc.stdout.decode().rstrip("\n")
                print(proc.stderr.decode().rstrip("\n"), file=sys.stderr)
                user = out
            utils.set_user_var("WEZTERM_USER", user)

            # 3 tell WezTerm the hostname
            if hostname_wez := env.get("WEZTERM_HOSTNAME"):
                hostname = hostname_wez
            elif hostname_xon := promptx["hostname"] if "hostname" in promptx else None:
                hostname = hostname_xon
            else:  # fallback to calling out hostname/ctl
                if isCmd("hostname"):
                    full_cmd = ["hostname"]
                elif isCmd("hostnamectl"):
                    full_cmd = ["hostnamectl", "hostname"]
                proc = subprocess.run(full_cmd, capture_output=True)
                out = proc.stdout.decode().rstrip("\n")
                print(proc.stderr.decode().rstrip("\n"), file=sys.stderr)
                hostname = out
            utils.set_user_var("WEZTERM_HOST", hostname)

            # 4 tell WezTerm whether the pane is running inside tmux
            if env.get("TMUX", ""):
                utils.set_user_var("WEZTERM_IN_TMUX", "1")
            else:
                utils.set_user_var("WEZTERM_IN_TMUX", "0")

    prompt_name = ["PROMPT", "RIGHT_PROMPT", "BOTTOM_TOOLBAR", "MULTILINE_PROMPT"]
    extend = False if _skip_zone else True
    opt = {"cl": "m", "aid": os.getpid()}
    for prompt in prompt_name:
        if XSH.env[prompt]:
            XSH.env[prompt] = utils.ShellIntegrationPrompt(
                XSH.env, prompt_name=prompt, extend=True, ext_opt=opt
            )
