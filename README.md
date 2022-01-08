# Terminal Emulators integration
[Shell integration](https://iterm2.com/documentation-escape-codes.html) for Xonsh shell. 
The following terminal emulators are supported 
- [iTerm2](https://iterm2.com/documentation-shell-integration.html)
- [kitty](https://sw.kovidgoyal.net/kitty/shell-integration/) 
  - Please follow [the manual integration guide](https://sw.kovidgoyal.net/kitty/shell-integration/#manual-shell-integration) 


## Installation

To install use pip:

``` bash
xpip install xontrib-term-integrations
# or: xpip install -U git+https://github.com/jnoortheen/xontrib-term-integrations
```

## Usage

``` bash
# this modifies the $PROMPT function. So load it after setting $PROMPT if you have a custom value
xontrib load term_integration
```
