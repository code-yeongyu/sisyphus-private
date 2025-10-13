"""Catppuccin theme definitions for Textual TUI."""

from __future__ import annotations

from catppuccin import PALETTE
from textual.theme import Theme

from sisyphus.utils.theme import ThemeName


def create_mocha_theme() -> Theme:
    """Create Catppuccin Mocha (dark) theme.

    Returns:
        Theme object with Mocha color palette
    """
    mocha = PALETTE.mocha.colors
    return Theme(
        name="mocha",
        primary=mocha.blue.hex,
        secondary=mocha.mauve.hex,
        warning=mocha.yellow.hex,
        error=mocha.red.hex,
        success=mocha.green.hex,
        accent=mocha.sapphire.hex,
        foreground=mocha.text.hex,
        background=mocha.base.hex,
        surface=mocha.mantle.hex,
        panel=mocha.crust.hex,
        dark=True,
    )


def create_latte_theme() -> Theme:
    """Create Catppuccin Latte (light) theme.

    Returns:
        Theme object with Latte color palette
    """
    latte = PALETTE.latte.colors
    return Theme(
        name="latte",
        primary=latte.blue.hex,
        secondary=latte.mauve.hex,
        warning=latte.yellow.hex,
        error=latte.red.hex,
        success=latte.green.hex,
        accent=latte.sapphire.hex,
        foreground=latte.text.hex,
        background=latte.base.hex,
        surface=latte.mantle.hex,
        panel=latte.crust.hex,
        dark=False,
    )


THEMES: dict[ThemeName, Theme] = {
    "mocha": create_mocha_theme(),
    "latte": create_latte_theme(),
}
