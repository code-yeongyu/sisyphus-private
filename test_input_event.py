"""Test Input.Submitted event handling in Textual."""

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static


class TestInputApp(App[None]):
    """Test app to verify Input.Submitted event handling."""

    CSS = """
    #container {
        height: 100%;
    }

    #status {
        height: 3;
        background: $panel;
        padding: 1;
    }

    #input-widget {
        height: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app."""
        with Vertical(id="container"):
            yield Static("Status: Ready", id="status")
            yield Input(placeholder="Type and press Enter", id="input-widget")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Input.Submitted event."""
        self.log.info(f"on_input_submitted called: value='{event.value}'")
        status = self.query_one("#status", Static)
        status.update(f"Status: Received '{event.value}'")
        event.input.value = ""


if __name__ == "__main__":
    app = TestInputApp()
    app.run()
