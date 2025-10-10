"""Test @on decorator with Input.Submitted."""

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, Static


class SearchBox(Vertical):
    """A composite widget with an input and a status display."""

    def compose(self) -> ComposeResult:
        """Compose child widgets."""
        yield Input(placeholder="Type something and press Enter", id="search-input")
        yield Static("Waiting for input…", id="status")

    @on(Input.Submitted, "#search-input")
    def handle_submit(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        status = self.query_one("#status", Static)
        status.update(f"You submitted: {event.value}")
        event.input.value = ""
        event.stop()


class DemoApp(App[None]):
    """Test app."""

    CSS = """
    Screen {
        align: center middle;
    }
    SearchBox {
        width: 60;
        border: round yellow;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the app."""
        yield SearchBox()


if __name__ == "__main__":
    DemoApp().run()
