from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static


class QueueableInput(Input):
    def action_submit(self) -> None:
        self.post_message(self.Submitted(self, self.value))


class TestApp(App[None]):
    CSS = """
    #container { height: 100%; }
    #status { height: 3; background: $panel; padding: 1; }
    #input-widget { height: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="container"):
            yield Static("Status: Ready", id="status")
            yield QueueableInput(placeholder="Type and press Enter", id="input-widget")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.log.info(f"on_input_submitted called: value='{event.value}'")
        status = self.query_one("#status", Static)
        status.update(f"Status: Received '{event.value}'")
        event.input.value = ""


if __name__ == "__main__":
    app = TestApp()
    app.run()
