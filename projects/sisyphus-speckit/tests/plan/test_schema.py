"""Tests for plan schema command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sisyphus_speckit.plan.schema import plan_schema


def test_plan_schema__if_no_output__prints_to_console(capsys: pytest.CaptureFixture[str]) -> None:
    # given: 출력 파일 없음
    # when: plan_schema 실행
    plan_schema(output=None)
    captured = capsys.readouterr()

    # then: JSON 스키마 출력
    assert captured.out
    assert "$defs" in captured.out or "PlanDocument" in captured.out


def test_plan_schema__if_output_file__saves_to_file(tmp_path: Path) -> None:
    # given: 임시 출력 파일
    output_file = tmp_path / "schema.json"

    # when: plan_schema 실행
    plan_schema(output=output_file)

    # then: 파일 생성 및 JSON 유효성
    assert output_file.exists()
    schema = json.loads(output_file.read_text())
    assert isinstance(schema, dict)


def test_plan_schema__validates_schema_structure(tmp_path: Path) -> None:
    # given: 임시 출력 파일
    output_file = tmp_path / "schema.json"

    # when: 스키마 생성
    plan_schema(output=output_file)
    schema = json.loads(output_file.read_text())

    # then: 스키마는 필요한 구조를 가짐
    assert "$defs" in schema or "properties" in schema
    # Verify it's a valid Pydantic JSON schema
    assert "title" in schema or "$defs" in schema
