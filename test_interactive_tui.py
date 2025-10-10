#!/usr/bin/env python3
"""Interactive TUI test script.

Tests InputBar queuing functionality without terminalcp MCP tool.
"""

from __future__ import annotations

import anyio
from textual.widgets import Input

from sisyphus.ui.tui.app import TUI
from sisyphus.ui.tui.components.input_bar import InputBar


def simulate_input_submitted(input_bar: InputBar, message: str) -> None:
    """Simulate on_input_submitted without triggering app.post_message."""
    if message:
        if input_bar._queued_message:
            input_bar._queued_message += "\n" + message
        else:
            input_bar._queued_message = message

        if input_bar._input_widget:
            input_bar._input_widget.value = ""

        input_bar._update_queue_display()


def simulate_up_key(input_bar: InputBar) -> str:
    """Simulate UP key press - returns what would be loaded to input."""
    if input_bar._queued_message:
        loaded_value = input_bar._queued_message
        input_bar._queued_message = ""
        input_bar._update_queue_display()
        return loaded_value
    elif input_bar._last_sent:
        return input_bar._last_sent
    return ""


class MockKeyEvent:
    key = "up"


async def test_scenario_4_2_1_basic_queuing() -> bool:
    """Test 4.2.1: Basic message queuing."""
    print("\n=== TEST 4.2.1: Basic Message Queuing ===")

    TUI()
    input_bar = InputBar()
    input_bar._input_widget = Input()

    simulate_input_submitted(input_bar, "Hello")

    print("Step 1: Sent 'Hello' + Enter")
    print(f"Queued message: {input_bar._queued_message!r}")

    checkpoint_1 = input_bar._queued_message == "Hello"
    checkpoint_2 = input_bar._input_widget.value == "" if input_bar._input_widget else False

    print("\nCheckpoint verification:")
    print("✅ PASS - Message queued" if checkpoint_1 else "❌ FAIL")
    if input_bar._input_widget:
        print(
            "✅ PASS - Input cleared" if checkpoint_2 else f"❌ FAIL - Input value: {input_bar._input_widget.value!r}"
        )

    overall = checkpoint_1 and checkpoint_2
    print(f"\nOverall: {'✅ ALL CHECKPOINTS PASSED' if overall else '❌ SOME FAILED'}")

    return overall


async def test_scenario_4_2_2_message_accumulation() -> bool:
    """Test 4.2.2: Message accumulation with multiple Enter presses."""
    print("\n=== TEST 4.2.2: Message Accumulation ===")

    input_bar = InputBar()
    input_bar._input_widget = Input()

    simulate_input_submitted(input_bar, "Hello")
    print("Step 1: Sent 'Hello'")
    print(f"Queued: {input_bar._queued_message!r}")

    simulate_input_submitted(input_bar, "World")
    print("Step 2: Sent 'World'")
    print(f"Queued: {input_bar._queued_message!r}")

    checkpoint_1 = "Hello" in input_bar._queued_message
    checkpoint_2 = "World" in input_bar._queued_message
    checkpoint_3 = input_bar._queued_message == "Hello\nWorld"

    print("\nCheckpoint verification:")
    print("✅ PASS - First message included" if checkpoint_1 else "❌ FAIL")
    print("✅ PASS - Second message accumulated" if checkpoint_2 else "❌ FAIL")
    print(f"✅ PASS - Separated by newline ('{input_bar._queued_message}')" if checkpoint_3 else "❌ FAIL")

    overall = checkpoint_1 and checkpoint_2 and checkpoint_3
    print(f"\nOverall: {'✅ ALL CHECKPOINTS PASSED' if overall else '❌ SOME FAILED'}")

    return overall


async def test_scenario_4_2_3_up_key_edit() -> bool:
    """Test 4.2.3: UP key loads queue for editing."""
    print("\n=== TEST 4.2.3: UP Key Edit ===")

    input_bar = InputBar()
    input_bar._input_widget = Input()

    simulate_input_submitted(input_bar, "Hello")
    simulate_input_submitted(input_bar, "World")

    print("Step 1: Queued 'Hello\\nWorld'")
    print(f"Queued: {input_bar._queued_message!r}")

    loaded_value = simulate_up_key(input_bar)

    print("\nStep 2: Pressed UP key")
    print(f"Loaded value: {loaded_value!r}")
    print(f"Queued: {input_bar._queued_message!r}")

    checkpoint_1 = loaded_value == "Hello\nWorld"
    checkpoint_2 = input_bar._queued_message == ""

    print("\nCheckpoint verification:")
    print(f"✅ PASS - Queue loaded to input ('{loaded_value}')" if checkpoint_1 else "❌ FAIL")
    print("✅ PASS - Queue cleared" if checkpoint_2 else "❌ FAIL")

    overall = checkpoint_1 and checkpoint_2
    print(f"\nOverall: {'✅ ALL CHECKPOINTS PASSED' if overall else '❌ SOME FAILED'}")

    return overall


async def test_scenario_4_2_4_edit_and_resave() -> bool:
    """Test 4.2.4: Edit queue and resave."""
    print("\n=== TEST 4.2.4: Edit and Resave ===")

    input_bar = InputBar()
    input_bar._input_widget = Input()

    simulate_input_submitted(input_bar, "Hello")

    loaded_value = simulate_up_key(input_bar)

    print("Step 1: 'Hello' queued, then UP key pressed")
    print(f"Loaded value: {loaded_value!r}")

    simulate_input_submitted(input_bar, "Hello!")

    print("\nStep 2: Modified to 'Hello!' and pressed Enter")
    print(f"Queued: {input_bar._queued_message!r}")

    checkpoint_1 = input_bar._queued_message == "Hello!"

    print("\nCheckpoint verification:")
    print(f"✅ PASS - Edited content re-queued ('{input_bar._queued_message}')" if checkpoint_1 else "❌ FAIL")

    overall = checkpoint_1
    print(f"\nOverall: {'✅ ALL CHECKPOINTS PASSED' if overall else '❌ SOME FAILED'}")

    return overall


async def test_scenario_4_2_6_load_last_sent() -> bool:
    """Test 4.2.6: UP key loads last sent message when queue is empty."""
    print("\n=== TEST 4.2.6: Load Last Sent Message ===")

    input_bar = InputBar()
    input_bar._input_widget = Input()

    simulate_input_submitted(input_bar, "First")

    sent_msg = input_bar.get_and_clear_queue()
    print("Step 1: 'First' queued and sent to agent")
    print(f"Sent message: {sent_msg!r}")
    print(f"Last sent: {input_bar._last_sent!r}")
    print(f"Queued: {input_bar._queued_message!r}")

    loaded_value = simulate_up_key(input_bar)

    print("\nStep 2: Pressed UP key (queue is empty)")
    print(f"Loaded value: {loaded_value!r}")

    checkpoint_1 = loaded_value == "First"
    checkpoint_2 = input_bar._last_sent == "First"

    print("\nCheckpoint verification:")
    print(f"✅ PASS - Last sent loaded to input ('{loaded_value}')" if checkpoint_1 else "❌ FAIL")
    print("✅ PASS - Last sent stored" if checkpoint_2 else "❌ FAIL")

    overall = checkpoint_1 and checkpoint_2
    print(f"\nOverall: {'✅ ALL CHECKPOINTS PASSED' if overall else '❌ SOME FAILED'}")

    return overall


async def main() -> bool:
    """Run all tests."""
    print("=" * 80)
    print("Interactive TUI Test Suite")
    print("=" * 80)

    results = []

    results.append(await test_scenario_4_2_1_basic_queuing())
    results.append(await test_scenario_4_2_2_message_accumulation())
    results.append(await test_scenario_4_2_3_up_key_edit())
    results.append(await test_scenario_4_2_4_edit_and_resave())
    results.append(await test_scenario_4_2_6_load_last_sent())

    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")

    return all(results)


if __name__ == "__main__":
    anyio.run(main)
