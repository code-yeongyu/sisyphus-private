from textual.app import App, ComposeResult

from sisyphus.ui.tui.components.input_bar import InputBar


class TestApp(App[None]):
    def compose(self) -> ComposeResult:
        yield InputBar()


if __name__ == "__main__":
    TestApp().run()
