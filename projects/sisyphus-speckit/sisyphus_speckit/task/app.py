from __future__ import annotations

import typer

from sisyphus_speckit.task.accept import task_accept
from sisyphus_speckit.task.continue_work import continue_work
from sisyphus_speckit.task.current import show_current
from sisyphus_speckit.task.next import show_next
from sisyphus_speckit.task.previous import show_previous
from sisyphus_speckit.task.show import show_task
from sisyphus_speckit.task.verify.bash import verify_bash
from sisyphus_speckit.task.verify.llm import verify_llm
from sisyphus_speckit.task.verify.llm_mark import verify_llm_mark
from sisyphus_speckit.task.verify.manual import verify_manual
from sisyphus_speckit.task.verify.manual_mark import verify_manual_mark
from sisyphus_speckit.task.verify.status import verify_status

task_app = typer.Typer(name="task", help="Task navigation and verification commands")
verify_app = typer.Typer(name="verify", help="Verification management commands")

task_app.add_typer(verify_app)

task_app.command(name="show")(show_task)
task_app.command(name="current")(show_current)
task_app.command(name="next")(show_next)
task_app.command(name="previous")(show_previous)
task_app.command(name="continue")(continue_work)
task_app.command(name="accept")(task_accept)

verify_app.command(name="bash")(verify_bash)
verify_app.command(name="llm")(verify_llm)
verify_app.command(name="llm-mark")(verify_llm_mark)
verify_app.command(name="manual")(verify_manual)
verify_app.command(name="manual-mark")(verify_manual_mark)
verify_app.command(name="status")(verify_status)
