from __future__ import annotations

import typer

from sisyphus_speckit.plan.accept_as_verification_agent import accept_as_verification_agent
from sisyphus_speckit.plan.export import export_plan
from sisyphus_speckit.plan.graph import show_graph
from sisyphus_speckit.plan.init import init_plan
from sisyphus_speckit.plan.lint import lint_plan
from sisyphus_speckit.plan.mark_completed import mark_completed_command
from sisyphus_speckit.plan.mark_fully_done import mark_fully_done_command
from sisyphus_speckit.plan.status import status
from sisyphus_speckit.plan.verify_final import verify_final_plan

plan_app = typer.Typer(name="plan", help="Plan management commands")

plan_app.command(name="lint")(lint_plan)
plan_app.command(name="init")(init_plan)
plan_app.command(name="graph")(show_graph)
plan_app.command(name="verify-final")(verify_final_plan)
plan_app.command(name="export")(export_plan)
plan_app.command(name="accept-as-verification-agent")(accept_as_verification_agent)
plan_app.command(name="mark completed")(mark_completed_command)
plan_app.command(name="mark fully-done")(mark_fully_done_command)
plan_app.command(name="status")(status)
