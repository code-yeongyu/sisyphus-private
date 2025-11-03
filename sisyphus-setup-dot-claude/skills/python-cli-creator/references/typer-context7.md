### Typer First Steps Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

Documentation for getting started with Typer, including how to document a CLI app using function docstrings and integrating with Termynal for enhanced output. Includes tests for examples.

```Python
import typer

app = typer.Typer()

@app.command()
def main(name: str = typer.Argument("World", help="The name to greet.")):
    """Greets the user by name."""
    typer.echo(f"Hello {name}")

if __name__ == "__main__":
    app()

```

--------------------------------

### Typer Application Launching Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

Documentation on how to launch Typer applications, covering the setup and execution process. This includes tests for the examples provided in the documentation.

```Python
import typer

app = typer.Typer()

@app.command()
def main():
    """A simple Typer application."""
    typer.echo("Hello from Typer!")

if __name__ == "__main__":
    typer.run(main)

```

--------------------------------

### Install Typer Package

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

An example command to install the Typer package using pip. This is presented as a typical installation command, with a note that it's an example and not to be run immediately in this context.

```console
$ pip install typer
---> 100%
```

--------------------------------

### Install Typer CLI

Source: https://github.com/fastapi/typer/blob/master/typer-cli/README.md

Instructions for installing the Typer library, which includes the Typer command. It is recommended to install `typer` directly instead of the older `typer-cli` package.

```bash
pip install typer
```

--------------------------------

### Running an Installable CLI Application

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/commands/index.md

Demonstrates how an installable CLI application is invoked, typically without the 'python' prefix.

```console
$ magic-app

✨ Some magic here ✨
```

--------------------------------

### Execute CLI Program

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Executes a command from the installed CLI program. This example shows running the 'shoot' command, demonstrating that the package is functional after installation.

```console
$ rick-portal-gun shoot

// It works 🎉
Shooting portal gun
```

--------------------------------

### Install Typer

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/typer-command.md

Installs the Typer library, which includes the `typer` command for shell completion and documentation.

```bash
pip install typer
```

--------------------------------

### CLI Help and Command Execution Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/commands/options.md

Shows how to view the application's help message and execute various commands with different arguments and options. Includes examples for creating a user, deleting a user with and without confirmation, deleting all users with and without confirmation, and initializing the user database.

```console
// Check the help
python main.py --help

Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or customize the installation.
  --help                Show this message and exit.

Commands:
  create
  delete
  delete-all
  init

// Check the command create
$ python main.py create Camila

Creating user: Camila

// Now test the command delete
$ python main.py delete Camila

# Are you sure you want to delete the user? [y/n]: $ y

Deleting user: Camila

$ python main.py delete Wade

# Are you sure you want to delete the user? [y/n]: $ n

Operation cancelled

// And finally, the command delete-all
// Notice it doesn't have CLI arguments, only a CLI option

$ python main.py delete-all

# Are you sure you want to delete ALL users? [y/n]: $ y

Deleting all users

$ python main.py delete-all

# Are you sure you want to delete ALL users? [y/n]: $ n

Operation cancelled

// And if you pass the --force CLI option, it doesn't need to confirm

$ python main.py delete-all --force

Deleting all users

// And init that doesn't take any CLI parameter
$ python main.py init

Initializing user database

```

--------------------------------

### Test Installed Package

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Verifies that the installed package functions correctly by running its command-line interface.

```Shell
$ rick-portal-gun load

// It works! 🎉
Loading portal gun
```

--------------------------------

### CLI Usage Example

Source: https://github.com/fastapi/typer/blob/master/tests/assets/cli/richformattedapp-docs.md

Demonstrates the command-line interface usage for the 'hello' command, including required and optional arguments and available options.

```console
$ hello [OPTIONS] USER_1 [USER_2]
```

--------------------------------

### Example CLI Execution

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/options/callback-and-context.md

Shows an example of running the Typer CLI application from the console and the expected output when providing a name argument.

```console
$ python main.py --name Camila

Validating param: name
Hello Camila

```

--------------------------------

### Install Package with Poetry

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Installs the Python package using Poetry, a dependency management tool. This command fetches and installs all declared dependencies from the lock file.

```console
$ poetry install

Installing dependencies from lock file

No dependencies to install or update

  - Installing the current project: rick-portal-gun (0.1.0)
```

--------------------------------

### CLI Argument Handling and Output Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/first-steps.md

This section provides console output examples demonstrating the behavior of a Typer CLI application with two required arguments. It shows the help message, errors for missing arguments, and successful execution when both arguments are provided in the correct order.

```console
// Check the main --help
$ python main.py --help

Usage: main.py [OPTIONS] NAME
Try 'main.py --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'NAME'.                          │
╰───────────────────────────────────────────────────╯

typers on richify [»!?] via 🐍 v3.7.5 (env3.7)
❯ python main.py
Usage: main.py [OPTIONS] NAME LASTNAME
Try 'main.py --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'NAME'.                          │
╰───────────────────────────────────────────────────╯

// There are now 2 CLI arguments, name and lastname

// Now pass a single name argument
$ python main.py Camila

Usage: main.py [OPTIONS] NAME LASTNAME
Try 'main.py --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'LASTNAME'.                      │
╰───────────────────────────────────────────────────╯

// These 2 arguments are required, so, pass both:
$ python main.py Camila Gutiérrez

Hello Camila Gutiérrez
```

--------------------------------

### Git Push Command Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/commands/index.md

Demonstrates the usage of the 'git push' command with and without arguments, showcasing basic CLI interaction.

```console
$ git push

---> 100%

// The push command with one CLI option --set-upstream and 2 CLI arguments
$ git push --set-upstream origin master

---> 100%
```

--------------------------------

### Typer Path Parameter CLI Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/parameter-types/path.md

Provides example command-line interactions for a Typer application using Path parameters, demonstrating scenarios with missing files, existing files, and directories.

```Bash
# No config
$ python main.py

No config file
Aborted!

# Pass a config that doesn't exist
$ python main.py --config config.txt

The config doesn't exist

# Now create a quick config
$ echo "some settings" > config.txt

# And try again
$ python main.py --config config.txt

Config file contents: some settings

# And with a directory
$ python main.py --config ./

Config is a directory, will use all its config files

```

```Bash
$ python main.py --config config.txt

Usage: main.py [OPTIONS]
Try "main.py --help" for help.

Error: Invalid value for '--config': File 'config.txt' does not exist.

# Now create a quick config
$ echo "some settings" > config.txt

# And try again
$ python main.py --config config.txt

Config file contents: some settings

# And with a directory
$ python main.py --config ./

Usage: main.py [OPTIONS]
Try "main.py --help" for help.

Error: Invalid value for '--config': File './' is a directory.

```

--------------------------------

### Install Wheel Package with Pip

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Installs the built wheel package (`.whl` file) into the user's local environment using pip. The `--user` flag is crucial for avoiding global system installations.

```console
$ pip install --user /home/rick/rick-portal-gun/dist/rick_portal_gun-0.1.0-py3-none-any.whl

---> 100%
```

--------------------------------

### Explicit Typer Application Setup

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/commands/index.md

Shows the explicit way to create a Typer application using `typer.Typer()` and adding a command with `@app.command()`.

```python
from typing import Optional

import typer

app = typer.Typer()


@app.command()
def main(
    name: str,
    formal: bool = False,
):
    if formal:
        print(f"Hello Ms. {name}")
    else:
        print(f"Hello {name}")


if __name__ == "__main__":
    app()

```

--------------------------------

### Install Package from PyPI

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Shows how to install a Python package from PyPI using pip, including dependency resolution and download progress.

```Shell
$ pip install --user rick-portal-gun

// Notice that it says "Downloading" 🚀
Collecting rick-portal-gun
  Downloading rick_portal_gun-0.1.0-py3-none-any.whl.metadata (435 bytes)
Requirement already satisfied: typer<0.13.0,>=0.12.3 in ./.local/lib/python3.10/site-packages (from rick-portal-gun==0.1.0) (0.12.3)
Requirement already satisfied: typing-extensions>=3.7.4.3 in ./.local/lib/python3.10/site-packages (from typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (4.11.0)
Requirement already satisfied: click>=8.0.0 in ./.local/lib/python3.10/site-packages (from typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (8.1.7)
Requirement already satisfied: shellingham>=1.3.0 in ./.local/lib/python3.10/site-packages (from typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (1.5.4)
Requirement already satisfied: rich>=10.11.0 in ./.local/lib/python3.10/site-packages (from typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (13.7.1)
Requirement already satisfied: pygments<3.0.0,>=2.13.0 in ./.local/lib/python3.10/site-packages (from rich>=10.11.0->typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (2.17.2)
Requirement already satisfied: markdown-it-py>=2.2.0 in ./.local/lib/python3.10/site-packages (from rich>=10.11.0->typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (3.0.0)
Requirement already satisfied: mdurl~=0.1 in ./.local/lib/python3.10/site-packages (from markdown-it-py>=2.2.0->rich>=10.11.0->typer<0.13.0,>=0.12.3->rick-portal-gun==0.1.0) (0.1.2)
Downloading rick_portal_gun-0.1.0-py3-none-any.whl (1.8 kB)
Installing collected packages: rick-portal-gun
Successfully installed rick-portal-gun-0.1.0
```

--------------------------------

### Install Typer-Slim

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/install.md

Installs the 'typer-slim' package, which provides the core Typer functionality without the default extra dependencies like 'rich' and 'shellingham'. This is suitable for advanced users who want a more minimal installation.

```Bash
pip install "typer-slim[standard]"
```

--------------------------------

### Running a Simple Python Script

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/commands/index.md

A basic example of running a Python script directly.

```console
$ python main.py

✨ Some magic here ✨
```

--------------------------------

### Running Users Add Command via Installed Package (Console)

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/one-file-per-command.md

Demonstrates how to execute the 'users add' subcommand of the Typer CLI application after it has been installed as a package.

```console
$ mycli users add Camila

Adding user: Camila
```

--------------------------------

### Install Typer Dependencies

Source: https://github.com/fastapi/typer/blob/master/docs/contributing.md

Installs the project's dependencies from requirements.txt using uv within the Docker container.

```bash
uv pip install -r requirements.txt
```

--------------------------------

### Python Type Hint Example for Typer

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/index.md

Demonstrates how to use Python type hints for function parameters in Typer. This allows Typer and editors to infer parameter types, enabling features like autocompletion and inline error checking.

```Python
from typing import Optional

def type_example(name: str, formal: bool = False, intro: Optional[str] = None):
    pass
```

--------------------------------

### Install Harry Package Version 1

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Demonstrates how to install a specific version (v1) of the 'harry' package using pip. This command is used to illustrate dependency management issues when installing packages globally.

```console
$ pip install "harry==1"
```

--------------------------------

### Verify CLI Program Installation

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Checks if the CLI program is accessible in the environment and displays its help message. This confirms the package was installed correctly and its commands are available.

```console
// You can use the which program to check which rick-portal-gun program is available (if any)
$ which rick-portal-gun

// You get the one from your environment
/home/rick/.cache/pypoetry/virtualenvs/rick-portal-gun-w31dJa0b-py3.10/bin/rick-portal-gun

// Try it
$ rick-portal-gun --help

// You get all the standard help
Usage: rick-portal-gun [OPTIONS] COMMAND [ARGS]...

  Awesome Portal Gun

Options:
  --install-completion  Install completion for the current shell.
  --show-completion     Show completion for the current shell, to copy it or customize the installation.

  --help                Show this message and exit.

Commands:
  load   Load the portal gun
  shoot  Shoot the portal gun
```

--------------------------------

### Install Packages from requirements.txt with uv

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Installs packages from a requirements.txt file using the 'uv' package manager. This offers a faster alternative to pip for dependency installation.

```Shell
$ uv pip install -r requirements.txt
---> 100%
```

--------------------------------

### Installing Typer with Standard Dependencies

Source: https://github.com/fastapi/typer/blob/master/README.md

Shows the command to install the Typer package, which includes optional dependencies like 'rich' for formatted errors and 'shellingham' for automatic shell detection during completion installation.

```Bash
pip install typer
```

--------------------------------

### Install Typer with Pip

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/install.md

Installs the Typer library using pip. By default, this installation includes the 'rich' and 'shellingham' libraries for enhanced CLI features.

```Bash
pip install typer
```

```Console
$ pip install typer
---> 100%
Successfully installed typer click shellingham rich
```

--------------------------------

### Running Version Command via Installed Package (Console)

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/one-file-per-command.md

Illustrates executing the 'version' command of the Typer CLI application after it has been installed as a package.

```console
$ mycli version

My CLI Version 1.0
```

--------------------------------

### Example Console Output for Completion

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/options/callback-and-context.md

Demonstrates how shell completion works with Typer, including listing commands, options, and executing the application with a valid option.

```console
$ typer ./main.py [TAB][TAB]

run    -- Run the provided Typer app.
utils  -- Extra utility commands for Typer apps.

$ typer ./main.py run --help

Usage: typer run [OPTIONS]

  Run the provided Typer app.

Options:
  --name TEXT  [required]
  --help       Show this message and exit.

$ typer ./main.py run --[TAB][TAB]

--help  -- Show this message and exit.
--name

$ typer ./main.py run --name Camila

Hello Camila
```

--------------------------------

### PATH Environment Variable Example (Windows)

Source: https://github.com/fastapi/typer/blob/master/docs/environment-variables.md

This snippet displays a common PATH environment variable setup on Windows systems, indicating the directories the OS checks for executable files.

```plaintext
C:\Program Files\Python312\Scripts;C:\Program Files\Python312;C:\Windows\System32
```

--------------------------------

### Install Packages Directly with uv

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Installs Python packages directly using the 'uv' package manager. This is an alternative to pip for faster installations.

```Shell
$ uv pip install typer
---> 100%
```

--------------------------------

### Install Typer Completion (typer-slim)

Source: https://github.com/fastapi/typer/blob/master/docs/features.md

When using 'typer-slim' (without shellingham), you need to specify the shell for completion installation. This command installs completion for the specified shell (e.g., bash).

```bash
--install-completion bash
```

--------------------------------

### Console Output Example

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/app-dir.md

Demonstrates the console output when running the CLI application. It shows the message indicating that the configuration file does not yet exist.

```Console
$ python main.py

Config file doesn't exist yet

```

--------------------------------

### Live Documentation Server

Source: https://github.com/fastapi/typer/blob/master/docs/contributing.md

Starts a live-reloading server for the project's documentation using a local script. It serves the documentation on http://127.0.0.1:8008.

```bash
python ./scripts/docs.py live
```

--------------------------------

### Install Typer Completion (with shellingham)

Source: https://github.com/fastapi/typer/blob/master/docs/features.md

This command installs shell completion for the current shell. Typer automatically detects the shell and installs the appropriate completion script. This requires the 'shellingham' library.

```bash
--install-completion
```

--------------------------------

### Running and Testing Typer CLI Commands

Source: https://github.com/fastapi/typer/blob/master/README.md

This section provides examples of how to run the Typer CLI applications from the command line. It includes examples of invoking the basic 'main' command with and without arguments, and how to access the auto-generated help messages for the main application and its subcommands. It also shows how to use the 'goodbye' command with and without the '--formal' option.

```Bash
# Run your application
$ python main.py

# You get a nice error, you are missing NAME
Usage: main.py [OPTIONS] NAME
Try 'main.py --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'NAME'.                          │
╰───────────────────────────────────────────────────╯


# You get a --help for free
$ python main.py --help

Usage: main.py [OPTIONS] NAME

╭─ Arguments ───────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]   |
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯

# Now pass the NAME argument
$ python main.py Camila

Hello Camila

# It works! 🎉

# Check the new help for the subcommand application
$ python main.py --help

 Usage: main.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────╮
│ --install-completion          Install completion  │
│                               for the current     │
│                               shell.              │
│ --show-completion             Show completion for │
│                               the current shell,  │
│                               to copy it or       │
│                               customize the       │
│                               installation.       │
│ --help                        Show this message   │
│                               and exit.           │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ goodbye                                           │
│ hello                                             │
╰───────────────────────────────────────────────────╯

# Check the help for the 'hello' command
$ python main.py hello --help

 Usage: main.py hello [OPTIONS] NAME

╭─ Arguments ───────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]   │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯

# Check the help for the 'goodbye' command
$ python main.py goodbye --help

 Usage: main.py goodbye [OPTIONS] NAME

╭─ Arguments ───────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]   │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --formal    --no-formal      [default: no-formal] │
│ --help                       Show this message    │
│                              and exit.            │
╰───────────────────────────────────────────────────╯

# Use it with the hello command
$ python main.py hello Camila

Hello Camila

# And with the goodbye command
$ python main.py goodbye Camila

Bye Camila!

# And with --formal
$ python main.py goodbye --formal Camila

Goodbye Ms. Camila. Have a good day.
```

--------------------------------

### Running and Testing Typer CLI Commands

Source: https://github.com/fastapi/typer/blob/master/docs/index.md

This section provides examples of how to run the Typer CLI applications from the command line. It includes examples of invoking the basic 'main' command with and without arguments, and how to access the auto-generated help messages for the main application and its subcommands. It also shows how to use the 'goodbye' command with and without the '--formal' option.

```Bash
# Run your application
$ python main.py

# You get a nice error, you are missing NAME
Usage: main.py [OPTIONS] NAME
Try 'main.py --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'NAME'.                          │
╰───────────────────────────────────────────────────╯


# You get a --help for free
$ python main.py --help

Usage: main.py [OPTIONS] NAME

╭─ Arguments ───────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]   |
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯

# Now pass the NAME argument
$ python main.py Camila

Hello Camila

# It works! 🎉

# Check the new help for the subcommand application
$ python main.py --help

 Usage: main.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────╮
│ --install-completion          Install completion  │
│                               for the current     │
│                               shell.              │
│ --show-completion             Show completion for │
│                               the current shell,  │
│                               to copy it or       │
│                               customize the       │
│                               installation.       │
│ --help                        Show this message   │
│                               and exit.           │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ goodbye                                           │
│ hello                                             │
╰───────────────────────────────────────────────────╯

# Check the help for the 'hello' command
$ python main.py hello --help

 Usage: main.py hello [OPTIONS] NAME

╭─ Arguments ───────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]   │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯

# Check the help for the 'goodbye' command
$ python main.py goodbye --help

 Usage: main.py goodbye [OPTIONS] NAME

╭─ Arguments ───────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]   │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --formal    --no-formal      [default: no-formal] │
│ --help                       Show this message    │
│                              and exit.            │
╰───────────────────────────────────────────────────╯

# Use it with the hello command
$ python main.py hello Camila

Hello Camila

# And with the goodbye command
$ python main.py goodbye Camila

Bye Camila!

# And with --formal
$ python main.py goodbye --formal Camila

Goodbye Ms. Camila. Have a good day.
```

--------------------------------

### Install Typer Slim

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/typer-command.md

Installs a slim version of Typer that does not include the `typer` command. The command can still be accessed via `python -m typer`.

```bash
pip install typer-slim
```

--------------------------------

### Install Typer CLI Completion

Source: https://github.com/fastapi/typer/blob/master/docs/contributing.md

Installs shell completion for the Typer CLI when Typer CLI itself is installed. This provides autocompletion for Typer commands in the terminal.

```bash
typer --install-completion
```

--------------------------------

### Install Requirements with Pip

Source: https://github.com/fastapi/typer/blob/master/docs/contributing.md

Installs all project dependencies and the local Typer package in editable mode using a requirements file.

```console
pip install -r requirements.txt
```

--------------------------------

### Typer CLI - Contributing Guide Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

This snippet refers to the contributing guide for the Typer project, outlining how developers can contribute to the library's development.

```Python
https://typer.tiangolo.com/contributing/
```

--------------------------------

### Install Packages Directly with Pip

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Installs Python packages directly using pip without a requirements file. This is useful for quick installations or when not managing dependencies in a file.

```Shell
$ pip install typer

---> 100%
```

--------------------------------

### Create a Basic Typer App

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/first-steps.md

This Python script demonstrates the simplest possible Typer application. It prints 'Hello World' when executed and can display help information using the --help flag.

```Python
from typer import Typer

app = Typer()

@app.command()
def main():
    print("Hello World")

if __name__ == "__main__":
    app()
```

--------------------------------

### Typer Auto Completion Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

Documentation on enabling auto-completion options (`--install-completion`, `--show-completion`) in Typer applications when `click-completion` is installed. Includes tests for these features.

```Python
import typer

app = typer.Typer()

@app.command()
def main(name: str = typer.Option("World", "--name", "-n")):
    typer.echo(f"Hello {name}")

if __name__ == "__main__":
    app()

```

--------------------------------

### Install Packages from requirements.txt with Pip

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Installs all packages listed in a requirements.txt file using pip. This is the standard way to manage project dependencies.

```Shell
$ pip install -r requirements.txt
---> 100%
```

--------------------------------

### Installing Typer without Optional Dependencies

Source: https://github.com/fastapi/typer/blob/master/README.md

Illustrates how to install the 'typer-slim' package, which provides the core Typer functionality without the optional 'rich' and 'shellingham' dependencies. This is useful for projects that prefer a minimal set of dependencies.

```Bash
pip install "typer-slim[standard]"
```

--------------------------------

### Install Typer with Standard Dependencies

Source: https://github.com/fastapi/typer/blob/master/docs/index.md

Install the Typer package using pip, which includes optional dependencies like 'rich' for enhanced error formatting and 'shellingham' for automatic shell detection during completion installation.

```Bash
pip install typer
```

--------------------------------

### Install Typer Shell Completion

Source: https://github.com/fastapi/typer/blob/master/docs/contributing.md

Installs shell completion for the Typer CLI. This command needs to be run inside the shell where completion is desired.

```bash
typer --install-completion
```

--------------------------------

### UUID Parameter CLI Usage Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/parameter-types/uuid.md

These console examples show how to interact with a Typer CLI application that accepts a UUID parameter. The first example demonstrates passing a valid UUID v4, and the output shows the received UUID and its version. The second example shows an invalid UUID, resulting in a usage error message from Typer.

```console
python main.py d48edaa6-871a-4082-a196-4daab372d4a1
```

```console
USER_ID is d48edaa6-871a-4082-a196-4daab372d4a1
UUID version is: 4
```

```console
python main.py 7479706572-72756c6573
```

```console
Usage: main.py [OPTIONS] USER_ID
Try "main.py --help" for help.

Error: Invalid value for 'USER_ID': 7479706572-72756c6573 is not a valid UUID.
```

--------------------------------

### Navigate and Run Python Script (Project A)

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Demonstrates navigating to a project directory and executing a Python script. This example highlights a scenario where the incorrect virtual environment might be active, leading to import errors.

```Bash
$ cd ~/code/prisoner-of-azkaban

$ python main.py

// Error importing sirius, it's not installed 😱
Traceback (most recent call last):
    File "main.py", line 1, in <module>
        import sirius
```

--------------------------------

### Running a Typer Application

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/index.md

Shows the basic command to run a Typer application from the terminal. Assumes the code is saved in a file named 'main.py'.

```Console
$ python main.py
```

--------------------------------

### CLI Help Output with Typer

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/first-steps.md

This console output demonstrates the help text generated for a Typer CLI application. It shows the usage, arguments, options, and their descriptions, derived from the Python code and docstrings.

```Console
$ python main.py --help

Usage: main.py [OPTIONS] NAME

 Say hi to NAME, optionally with a --lastname.
 If --formal is used, say hi very formally.

╭─ Arguments ───────────────────────────────────────────────────────╮
│ *    name      TEXT  [default: None] [required]                   │
╰───────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────╮
│ --lastname                             TEXT
│ --formal                --no-formal    [default: no-formal]
│ --help                                     Show this message
│                                              and exit.
╰───────────────────────────────────────────────────────────────────╯

```

--------------------------------

### Git Remote Command Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/subcommands/index.md

Demonstrates the usage of the 'git remote' command, including listing current remotes, showing verbose output, and adding a new remote repository. This serves as an example for creating similar nested command structures in Typer applications.

```console
$ git remote

origin

$ git remote -v

origin  git@github.com:yourusername/typer.git (fetch)
origin  git@github.com:yourusername/typer.git (push)

$ git remote add upstream https://github.com/fastapi/typer.git

$ git remote -v

origin  git@github.com:yourusername/typer.git (fetch)
origin  git@github.com:yourusername/typer.git (push)
upstream        https://github.com/fastapi/typer.git (fetch)
upstream        https://github.com/fastapi/typer.git (push)
```

--------------------------------

### Install Typer with Rich Integration

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

This command installs Typer along with all optional dependencies, including the Rich library, which enables enhanced CLI output features.

```Console
pip install "typer[all]"
```

--------------------------------

### Typer CLI Options Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

Documentation for defining and using CLI options in Typer applications. This section includes tests for the examples provided in the documentation.

```Python
import typer

app = typer.Typer()

@app.command()
def main(
    name: str = typer.Option("World", "--name", "-n", help="The name to greet.")
):
    typer.echo(f"Hello {name}")

if __name__ == "__main__":
    app()

```

--------------------------------

### Typer CLI Help Output and Execution Example

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/parameter-types/index.md

Shows the help message generated by Typer for a CLI application with various parameter types (string, integer, float, boolean flags). It also includes examples of calling the CLI with different arguments and the resulting output, demonstrating type conversion and validation.

```console
$ python main.py --help

// Notice how --age is an INTEGER and --height-meters is a FLOAT
Usage: main.py [OPTIONS] NAME

Arguments:
  NAME  [required]

Options:
  --age INTEGER           [default: 20]
  --height-meters FLOAT   [default: 1.89]
  --female / --no-female  [default: True]
  --help                  Show this message and exit.

// Call it with CLI parameters
$ python main.py Camila --age 15 --height-meters 1.70 --female

// All the data has the correct Python type
NAME is Camila, of type: class 'str'
--age is 15, of type: class 'int'
--height-meters is 1.7, of type: class 'float'
--female is True, of type: class 'bool'

// And if you pass an incorrect type
$ python main.py Camila --age 15.3

Usage: main.py [OPTIONS] NAME
Try "main.py --help" for help.

Error: Invalid value for '--age': '15.3' is not a valid integer

// Because 15.3 is not an INTEGER (it's a float)

```

--------------------------------

### Typer CLI Arguments Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

Documentation for defining and using CLI arguments in Typer applications. This section includes tests for the examples provided in the documentation.

```Python
import typer

app = typer.Typer()

@app.command()
def main(name: str = typer.Argument(..., help="The name to greet.")):
    typer.echo(f"Hello {name}")

if __name__ == "__main__":
    app()

```

--------------------------------

### Install Typer Command Completion

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/typer-command.md

Installs shell completion for the `typer` command. This enables features like tab completion for subcommands and options in the terminal.

```console
$ typer --install-completion
bash completion installed in /home/user/.bashrc.
Completion will take effect once you restart the terminal.
```

--------------------------------

### Install Typer

Source: https://github.com/fastapi/typer/blob/master/README.md

Installs the Typer library and its dependencies (rich, shellingham) using pip. This is the first step to using Typer for building CLI applications.

```console
$ pip install typer
---> 100%
Successfully installed typer rich shellingham
```

--------------------------------

### Rich Spinner Example

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/progressbar.md

Shows how to use Rich to display spinners for operations where the duration is unknown. This example displays two spinners simultaneously.

```Python
from typer import Typer
from rich.progress import Progress

app = Typer()


@app.command()
def main():
    with Progress() as progress:
        task1 = progress.add_task("[red]Processing...", total=100)
        task2 = progress.add_task("[green]Preparing...", total=100)

        while not progress.finished:
            progress.update(task1, advance=0.9)
            progress.update(task2, advance=0.5)


if __name__ == "__main__":
    app()

```

--------------------------------

### Running Python Script Directly

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/first-steps.md

Demonstrates the standard way to execute a Python script from the command line without any special tools.

```Console
$ python main.py

Hello World
```

--------------------------------

### Configure Package Scripts in pyproject.toml

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Configures the `pyproject.toml` file to define the command-line script for the installed package. It specifies the entry point for the CLI application.

```TOML
[tool.poetry]
name = "rick-portal-gun"
version = "0.1.0"
description = ""
authors = ["Rick Sanchez <rick@example.com>"]
readme = "README.md"

[tool.poetry.scripts]
rick-portal-gun = "rick_portal_gun.main:app"

[tool.poetry.dependencies]
python = "^3.10"
typer = "^0.12.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

--------------------------------

### Execute CLI Program

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/package.md

Demonstrates how to execute the packaged CLI program from the terminal after installation. The command name is defined in the `pyproject.toml`.

```Console
$ rick-portal-gun

// Something happens here ✨
```

--------------------------------

### CLI Help and Usage Examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/multiple-values/arguments-with-multiple-values.md

This section provides examples of how to use the CLI arguments defined with multiple values, including checking the help message, using default values, and handling incorrect numbers of arguments.

```console
$ python main.py --help

Usage: main.py [OPTIONS] [NAMES]...

Arguments:
  [NAMES]...  Select 3 characters to play with  [default: Harry, Hermione, Ron]

Options:
  --help                Show this message and exit.

$ python main.py

Hello Harry
Hello Hermione
Hello Ron

$ python main.py Draco Hagrid

Error: Argument 'names' takes 3 values

$ python main.py Draco Hagrid Dobby

Hello Draco
Hello Hagrid
Hello Dobby

```

--------------------------------

### Running Sample Script with Typer Command

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/typer-command.md

Shows how to execute the sample Typer script using the `typer` command, which enables shell completion.

```console
$ typer my_custom_script.py run hello

Hello World!

$ typer my_custom_script.py run hello --name Camila

Hello Camila!

$ typer my_custom_script.py run bye --name Camila

Bye Camila
```

--------------------------------

### Typer Commands Documentation

Source: https://github.com/fastapi/typer/blob/master/docs/release-notes.md

Documentation for Typer commands, including the use of Typer callbacks and handling one or multiple commands. This section includes tests for all examples and addresses bug fixes.

```Python
import typer

app = typer.Typer()

@app.callback()
def main():
    """A main command with a callback."""
    typer.echo("Executing main callback")

@app.command()
def create():
    """Creates something."""
    typer.echo("Creating...")

@app.command()
def delete():
    """Deletes something."""
    typer.echo("Deleting...")

if __name__ == "__main__":
    app()

```

--------------------------------

### CLI Example: Reading Config File

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/parameter-types/file.md

A bash command to create a configuration file and then run a Python script that reads it using Typer's file parameter.

```Bash
$ echo "some settings" > config.txt
$ echo "some more settings" >> config.txt
$ python main.py --config config.txt
```

--------------------------------

### Typer CLI datetime help and usage examples

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/parameter-types/datetime.md

This section shows the command-line interface help output for a Typer application expecting a `datetime` parameter. It includes examples of passing valid and invalid datetime strings, demonstrating Typer's parsing and error handling capabilities.

```console
$ python main.py --help

Usage: main.py [OPTIONS] BIRTH:[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]

Arguments:
  BIRTH:[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S][required]

Options:
  --help                Show this message and exit.

// Pass a datetime
$ python main.py 1956-01-31T10:00:00

Interesting day to be born: 1956-01-31 10:00:00
Birth hour: 10

// An invalid date
$ python main.py july-19-1989

Usage: main.py [OPTIONS] [%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d%H:%M:%S]

Error: Invalid value for 'BIRTH:[%Y-%m-%d|%Y-%m-%dT%H:%M:%S|%Y-%m-%d %H:%M:%S]': 'july-19-1989' does not match the formats '%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'.
```

--------------------------------

### Running Sample Script with Python

Source: https://github.com/fastapi/typer/blob/master/docs/tutorial/typer-command.md

Demonstrates how to run the sample Typer script using the standard Python interpreter.

```console
$ python my_custom_script.py hello

Hello World!

$ python my_custom_script.py hello --name Camila

Hello Camila!

$ python my_custom_script.py bye --name Camila

Bye Camila
```

--------------------------------

### Install Typer Slim with Standard Dependencies

Source: https://github.com/fastapi/typer/blob/master/docs/index.md

Install the 'typer-slim' package with the 'standard' extra dependencies. This provides the same core functionality as 'typer' but without 'rich' and 'shellingham' included by default.

```Bash
pip install "typer-slim[standard]"
```

--------------------------------

### PATH Variable Example (Linux/macOS)

Source: https://github.com/fastapi/typer/blob/master/docs/virtual-environments.md

Illustrates the PATH environment variable before and after activating a virtual environment on Linux/macOS. It shows how the virtual environment's bin directory is prepended to the PATH.

```plaintext
Before activation:
/usr/bin:/bin:/usr/sbin:/sbin

After activation:
/home/user/code/awesome-project/.venv/bin:/usr/bin:/bin:/usr/sbin:/sbin
```
