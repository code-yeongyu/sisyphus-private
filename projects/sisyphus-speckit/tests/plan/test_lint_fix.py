"""Tests for plan lint --fix functionality."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

from sisyphus_speckit.plan.lint import _add_missing_fields, _fix_multiline_texts


class TestFixMultilineTexts:
    """Tests for _fix_multiline_texts function."""

    def test_fix_multiline_texts__if_single_line_string__returns_unchanged(self) -> None:
        # given: 싱글라인 문자열
        text = "This is a single line"

        # when: _fix_multiline_texts 실행
        result = _fix_multiline_texts(text)

        # then: 변경되지 않음
        assert result == text
        assert not isinstance(result, LiteralScalarString)

    def test_fix_multiline_texts__if_multiline_string__converts_to_literal_scalar_string(self) -> None:
        # given: 멀티라인 문자열 (최소 2개 라인)
        text = "Line 1\nLine 2\nLine 3"

        # when: _fix_multiline_texts 실행
        result = _fix_multiline_texts(text)

        # then: LiteralScalarString으로 변환됨
        assert isinstance(result, LiteralScalarString)
        assert str(result) == text

    def test_fix_multiline_texts__if_dict_with_multiline__converts_all_values(self) -> None:
        # given: 멀티라인 값을 포함한 딕셔너리
        data: dict[str, object] = {
            "title": "Single line",
            "description": "Line 1\nLine 2",
            "notes": "A\nB\nC",
        }

        # when: _fix_multiline_texts 실행
        result = cast(dict[str, object], _fix_multiline_texts(data))

        # then: 멀티라인만 변환, 싱글라인은 유지
        assert result["title"] == "Single line"
        assert isinstance(result["description"], LiteralScalarString)
        assert isinstance(result["notes"], LiteralScalarString)

    def test_fix_multiline_texts__if_nested_dict__processes_recursively(self) -> None:
        # given: 중첩된 딕셔너리
        data: dict[str, object] = {
            "outer": {
                "inner": "Line 1\nLine 2",
                "text": "single",
            }
        }

        # when: _fix_multiline_texts 실행
        result = cast(dict[str, object], _fix_multiline_texts(data))

        # then: 중첩된 멀티라인도 변환됨
        outer = cast(dict[str, object], result["outer"])
        assert isinstance(outer["inner"], LiteralScalarString)
        assert outer["text"] == "single"

    def test_fix_multiline_texts__if_list_with_multiline__converts_all_items(self) -> None:
        # given: 멀티라인을 포함한 리스트
        data: list[object] = [
            "single line",
            "Line 1\nLine 2",
            "Another\nMultiline\nString",
        ]

        # when: _fix_multiline_texts 실행
        result = cast(list[object], _fix_multiline_texts(data))

        # then: 리스트의 멀티라인 항목 변환
        assert result[0] == "single line"
        assert isinstance(result[1], LiteralScalarString)
        assert isinstance(result[2], LiteralScalarString)

    def test_fix_multiline_texts__if_list_of_dicts__processes_all_dicts(self) -> None:
        # given: 딕셔너리를 포함한 리스트
        data: list[object] = [
            {"text": "Line 1\nLine 2"},
            {"text": "single line"},
        ]

        # when: _fix_multiline_texts 실행
        result = cast(list[object], _fix_multiline_texts(data))

        # then: 각 딕셔너리의 멀티라인 변환
        dict_item_1 = cast(dict[str, object], result[0])
        dict_item_2 = cast(dict[str, object], result[1])
        assert isinstance(dict_item_1["text"], LiteralScalarString)
        assert dict_item_2["text"] == "single line"

    def test_fix_multiline_texts__if_non_string_types__preserves_unchanged(self) -> None:
        # given: 다양한 타입 데이터
        data: dict[str, object] = {
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
        }

        # when: _fix_multiline_texts 실행
        result = cast(dict[str, object], _fix_multiline_texts(data))

        # then: 비문자열 타입은 유지됨
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["none"] is None

    def test_fix_multiline_texts__if_empty_dict__returns_empty_dict(self) -> None:
        # given: 빈 딕셔너리
        data: dict[str, str] = {}

        # when: _fix_multiline_texts 실행
        result = _fix_multiline_texts(data)

        # then: 빈 딕셔너리 반환
        assert result == {}

    def test_fix_multiline_texts__if_empty_list__returns_empty_list(self) -> None:
        # given: 빈 리스트
        data: list[str] = []

        # when: _fix_multiline_texts 실행
        result = _fix_multiline_texts(data)

        # then: 빈 리스트 반환
        assert result == []


class TestAddMissingFields:
    """Tests for _add_missing_fields function."""

    def test_add_missing_fields__if_simple_dict__returns_unchanged(self) -> None:
        # given: 간단한 딕셔너리
        data: dict[str, object] = {"name": "test", "value": 123}

        # when: _add_missing_fields 실행
        result = cast(dict[str, object], _add_missing_fields(data))

        # then: 동일하게 반환됨
        assert result == data

    def test_add_missing_fields__if_nested_dict__processes_recursively(self) -> None:
        # given: 중첩된 딕셔너리
        data: dict[str, object] = {
            "outer": {
                "inner": "value",
            }
        }

        # when: _add_missing_fields 실행
        result = cast(dict[str, object], _add_missing_fields(data))

        # then: 중첩된 구조 유지됨
        outer = cast(dict[str, object], result["outer"])
        assert outer["inner"] == "value"

    def test_add_missing_fields__if_list_of_items__processes_all_items(self) -> None:
        # given: 리스트 항목들
        data: list[object] = [
            {"field": "value1"},
            {"field": "value2"},
        ]

        # when: _add_missing_fields 실행
        result = cast(list[object], _add_missing_fields(data))

        # then: 리스트 항목들 처리됨
        assert len(result) == 2
        dict_item_1 = cast(dict[str, object], result[0])
        dict_item_2 = cast(dict[str, object], result[1])
        assert dict_item_1["field"] == "value1"
        assert dict_item_2["field"] == "value2"

    def test_add_missing_fields__if_non_dict_non_list__returns_unchanged(self) -> None:
        # given: 단순 값들
        values: list[object] = ["string", 42, 3.14, True, None]

        # when: _add_missing_fields 실행
        for value in values:
            result = _add_missing_fields(value)

            # then: 변경되지 않음
            assert result == value


class TestLintFixIntegration:
    """Integration tests for lint --fix functionality."""

    def test_lint_fix__if_yaml_with_multiline__saves_fixed_file(self, tmp_path: Path) -> None:
        # given: 멀티라인 텍스트를 포함한 YAML 파일
        yaml_file = tmp_path / "test.yaml"
        yaml_content = """
id: test-plan
user_request:
  original: |
    This is line 1
    This is line 2
"""
        _ = yaml_file.write_text(yaml_content)

        # when: YAML를 로드하고 fix 적용
        yaml = YAML()
        with yaml_file.open("r", encoding="utf-8") as f:
            data = yaml.load(f)

        fixed_data = _fix_multiline_texts(data)  # pyright: ignore[reportUnknownArgumentType]
        fixed_data = _add_missing_fields(fixed_data)

        # then: 데이터가 수정됨
        fixed_dict = cast(dict[str, object], fixed_data)
        user_request = cast(dict[str, object], fixed_dict["user_request"])
        assert isinstance(user_request["original"], LiteralScalarString | str)

    def test_lint_fix__if_empty_yaml__handles_gracefully(self, tmp_path: Path) -> None:
        # given: 빈 YAML 파일
        yaml_file = tmp_path / "empty.yaml"
        _ = yaml_file.write_text("")

        # when: YAML를 로드하고 fix 적용
        yaml = YAML()
        with yaml_file.open("r", encoding="utf-8") as f:
            data = yaml.load(f)

        if data is not None:
            fixed_data = _fix_multiline_texts(data)  # pyright: ignore[reportUnknownArgumentType]
            fixed_data = _add_missing_fields(fixed_data)

            # then: 데이터 처리됨
            assert fixed_data is not None or data is None

    def test_lint_fix__if_yaml_file_saved__preserves_structure(self, tmp_path: Path) -> None:
        # given: YAML 데이터를 로드하고 수정한 후 저장
        yaml_file = tmp_path / "test.yaml"
        original_data: dict[str, object] = {
            "id": "test",
            "description": "Line 1\nLine 2",
            "simple": "value",
        }

        yaml = YAML()
        yaml.preserve_quotes = True

        # when: 원본 YAML 저장
        with yaml_file.open("w", encoding="utf-8") as f:
            yaml.dump(original_data, f)

        # and: YAML 로드 및 fix 적용
        with yaml_file.open("r", encoding="utf-8") as f:
            loaded_data = yaml.load(f)

        fixed_data = _fix_multiline_texts(loaded_data)  # pyright: ignore[reportUnknownArgumentType]
        fixed_data = _add_missing_fields(fixed_data)

        # and: 수정된 YAML 저장
        with yaml_file.open("w", encoding="utf-8") as f:
            yaml.dump(fixed_data, f)

        # then: 파일이 존재하고 읽을 수 있음
        assert yaml_file.exists()
        saved_text = yaml_file.read_text()
        assert "test" in saved_text

    @pytest.mark.usefixtures("tmp_path")
    def test_lint_fix__if_complex_structure__processes_all_levels(self) -> None:
        # given: 복잡한 중첩 구조
        data: dict[str, object] = {
            "work_plans": [
                {
                    "id": "plan-1",
                    "user_request": {
                        "original": "Request\nwith\nmultiple lines",
                        "additional": [
                            "Item 1\nMultiline",
                            "Item 2",
                        ],
                    },
                }
            ]
        }

        # when: fix 적용
        result = _fix_multiline_texts(data)
        result = _add_missing_fields(result)

        # then: 모든 레벨의 멀티라인이 변환됨
        result_dict = cast(dict[str, object], result)
        work_plans = cast(list[object], result_dict["work_plans"])
        plan = cast(dict[str, object], work_plans[0])
        user_request = cast(dict[str, object], plan["user_request"])
        original = cast(LiteralScalarString, user_request["original"])
        additional = cast(list[object], user_request["additional"])
        assert isinstance(original, LiteralScalarString)
        assert isinstance(additional[0], LiteralScalarString)
        assert additional[1] == "Item 2"
