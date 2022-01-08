"""Completers for pip."""
import contextlib
import os
import subprocess

from xonsh.built_ins import XSH
from xonsh.completers.tools import RichCompletion, contextual_command_completer
from xonsh.parsers.completion_context import CommandContext


def create_rich_completion(line: str, append_space=False):
    line = line.strip()
    if "\t" in line:
        cmd, desc = map(str.strip, line.split("\t", maxsplit=1))
    else:
        cmd, desc = line, ""

    # special treatment for path completions.
    # not appending space even if it is a single candidate.
    if cmd.endswith(os.pathsep):
        append_space = False

    return RichCompletion(
        cmd,
        description=desc,
        append_space=append_space,
    )


def generate_completions_from_string(output: str):
    """Rich completion from multi-line string, each line representing a completion."""
    if output:
        lines = output.strip().splitlines(keepends=False)
        # if there is a single completion candidate then maybe it is over
        append_space = len(lines) == 1
        for line in lines:
            comp = create_rich_completion(line, append_space)
            yield comp


def run_subproc(exe: str, *tokens: "str"):
    env = XSH.env.detype()

    with contextlib.suppress(FileNotFoundError):
        proc = subprocess.Popen(
            [exe, "+complete", "fish2"],
            stderr=subprocess.DEVNULL,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=env,
            text=True,
        )
        out, _ = proc.communicate(input="\n".join(tokens))
        return out


def get_completions(*args):
    if not args:
        return
    exe = args[0]
    output = run_subproc(exe, *args)
    return generate_completions_from_string(output)


@contextual_command_completer
def xonsh_complete(ctx: CommandContext):
    """Completes python's package manager pip."""
    if not ctx.completing_command("kitty"):
        return None

    # like fish's
    # commandline --tokenize --cut-at-cursor --current-process
    tokens = [arg.raw_value for arg in ctx.args[: ctx.arg_index]]

    # it already filters by prefix, just return it
    return get_completions(*tokens, ctx.prefix)


if __name__ == "__main__":
    # small testing won't hurt
    from xonsh.main import setup

    setup()
    print(list(get_completions("kitty", "-")))
    print(list(get_completions("kitty", "--")))
    print(list(get_completions("kitty", "--d")))
