import pytest
from pydantic import ValidationError

from sisyphus.core.plans.models import ReferenceItem

pytestmark = [pytest.mark.anyio]


async def test_reference_uri_and_inline_both__if_both_provided__raises_validation_error() -> None:
    # given
    data = {
        "uri": "https://example.com/doc",
        "inline": "This is inline text",
    }

    # when & then
    with pytest.raises(ValidationError) as exc_info:
        ReferenceItem(**data)
    assert "uri와 inline은 동시에 사용할 수 없습니다" in str(exc_info.value)


async def test_reference_all_none__if_no_fields_provided__raises_validation_error() -> None:
    # given
    data = {}

    # when & then
    with pytest.raises(ValidationError) as exc_info:
        ReferenceItem(**data)
    assert "ref_id, uri 또는 inline 중 하나는 필수입니다" in str(exc_info.value)


async def test_reference_ref_id_with_uri_and_inline__if_all_three_provided__raises_validation_error() -> None:
    # given
    data = {
        "ref_id": "ref_123",
        "uri": "https://example.com",
        "inline": "Text content",
    }

    # when & then
    with pytest.raises(ValidationError) as exc_info:
        ReferenceItem(**data)
    assert "uri와 inline은 동시에 사용할 수 없습니다" in str(exc_info.value)


async def test_reference_only_ref_id__if_ref_id_only__creates_successfully() -> None:
    # given
    data = {"ref_id": "ref_valid"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.ref_id == "ref_valid"
    assert ref.uri is None
    assert ref.inline is None


async def test_reference_only_uri__if_uri_only__creates_successfully() -> None:
    # given
    data = {"uri": "https://docs.example.com"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.uri == "https://docs.example.com"
    assert ref.ref_id is None
    assert ref.inline is None


async def test_reference_only_inline__if_inline_only__creates_successfully() -> None:
    # given
    data = {"inline": "Direct inline content here"}

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.inline == "Direct inline content here"
    assert ref.ref_id is None
    assert ref.uri is None


async def test_reference_ref_id_with_uri__if_both_provided__creates_successfully() -> None:
    # given
    data = {
        "ref_id": "ref_001",
        "uri": "https://example.com/api",
    }

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.ref_id == "ref_001"
    assert ref.uri == "https://example.com/api"
    assert ref.inline is None


async def test_reference_ref_id_with_inline__if_both_provided__creates_successfully() -> None:
    # given
    data = {
        "ref_id": "ref_002",
        "inline": "Inline text with ref_id",
    }

    # when
    ref = ReferenceItem(**data)

    # then
    assert ref.ref_id == "ref_002"
    assert ref.inline == "Inline text with ref_id"
    assert ref.uri is None
