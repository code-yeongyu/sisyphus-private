<style>
    <type-safety>
        When writing python code, make sure you type hint everything.
        ## 타입 안전성
        ### 기본 원칙
        - 타입 힌트를 적극적으로 사용합니다
        - implicit generic 타입 사용을 지양합니다
        - Implicit usage of generics are not allowed. When the type is inferable (e.g. method's return type, defining variable) don't add the type hint.
        - 모든 함수의 파라미터에 타입 힌트가 있어야 합니다
        ### 타입 힌트 규칙
        - pytest의 fixture 파라미터도 타입을 명시해야 합니다:
            - `mocker: MockerFixture` (from pytest_mock)
            - 다른 fixture들도 적절한 타입 힌트 필요
        ### 타입 힌트 예시
            ```python
            from typing import List, Dict, Optional
            from spray.utils.platform import Platform
            from pytest_mock import MockerFixture

            def process_data(platform: Platform, data: List[Dict[str, str]]) -> Optional[str]:
                # 구현
                pass

            def test_something(mocker: MockerFixture) -> None:
                # 테스트 구현
                pass
            Never use '-> Any' as a method return type hint. (ruff check --rule ANN401)
            ```
    </type-safety>

    <types>
        I prefer using Literals over Enums. Please assume that the code you are facing is using Literal most of the time, and enums as exceptional cases.
    </types>

    <imports>
        - Nested imports are not allowed. Imports should always placed on the top of the code.
        - on __init__, always use "explicit-reexport", which is `from foo import bar as bar`. use of __all__ is not allowed.
        - NEVER EVER USE __all__ for exporting, use explicit-reexport like `from foo import bar as bar` to export modules.
    </imports>

    <async-first>
        Django ORM
        - django orm을 다룰 때에 async 사용을 해야합니다
        - 따라서 eager loading을 적극적으로 사용해야 합니다
        - django orm async 사용시에는 `async for`를 사용하여 list comprehension 결과를 수집해야 합니다
        - **`alist()`, `afilter()` 와 같은 존재하지 않는 메서드는 사용하지 않습니다** (`aget`, `adelete` 등 존재하는 메서드는 사용 가능합니다.)

        Example:
        ```python
        async def get_influencers(platform: Platform) -> List[Influencer]:
            # 올바른 방법: async for 사용
            influencers = [
                influencer async for influencer in
                Influencer.objects.select_related('brand').filter(platform=platform)
            ]
            return influencers

        # 틀린 방법 - alist()는 존재하지 않음
        # influencers = await Influencer.objects.filter(platform=platform).alist()
        ```
    </async-first>

    <test>
        Basic Principles:

        - 테스트 프레임워크는 pytest를 사용합니다
        - 테스트 코드는 모두 `tests` 폴더 내에 작성합니다
        - unittest와 django test는 사용하지 않습니다
        - 각각의 테스트는 테스트, 테스트 케이스, TC라고 부릅니다
        - 전체 테스트 세트는 테스트 세트, 테스트 스위트라고 부릅니다
        - 항상 원본 함수의 입출력을 먼저 테스트합니다
        - 변경된 DB를 조회하는 테스트는 부수적으로 작성합니다

        File Structure - Must follow
        **절대적인 배치 순서:**

        1. **imports**
        2. **pytestmark**
        3. **모든 테스트 함수들**
        4. **모든 fixture들 (반드시 맨 밑에 배치)**

        **주의사항:**

        - 기존 코드에서 fixture가 상단에 있어도 **무시하고 반드시 맨 밑으로 이동**
        - pytest는 fixture 정의 순서와 상관없이 의존성을 자동 해결함
        - **절대 테스트 함수와 fixture를 섞어서 배치하지 말 것**

        **올바른 예시:**

        ```python
        # imports
        import pytest

        # pytestmark
        pytestmark = [pytest.mark.django_db] # add this only when working with django & django orm

        # 모든 테스트 함수들
        def test_something():
            pass

        def test_another():
            pass

        # 모든 fixture들 (반드시 맨 밑)
        @pytest.fixture
        def my_fixture():
            pass
        ```

        **체크리스트:**

        - [ ] 모든 테스트 함수가 fixture보다 위에 있는가?
        - [ ] fixture들이 파일 맨 밑에 모여있는가?
        - [ ] imports, pytestmark, tests, fixtures 순서가 맞는가?

        Naming Rules - Test File Names:

        - 원본 파일 이름 앞에 `test_` prefix 붙입니다
            - e.g. `match.py` -> `test_match.py`
        - 원본 함수 하나 당 5개 이상의 TC를 만들어야 하는 경우, 테스트 파일 이름에 함수 이름도 포함
            - e.g. `test_{filename}__{func_name}.py`
            - `test_credit_service__deduct_credits.py`
            - `test_credit_service__repay_credits.py`
        - 단, 원본 함수 하나 당 테스트 파일은 반드시 한 개

        Naming Rules - Test Method Names:

        - 테스트 함수 이름은 항상 아래의 형식이어야 합니다:
            `test_{func_name}__if_{condition}__{result | error}`
        - 조건(condition)과 결과(result | error)는:
            - 사람이 이해하기 쉬워야 합니다
            - 함수의 인터페이스에 대한 것이어야 함 (입력 파라메터, 반환되는 값, 발생하는 에러)

        Naming Rules - Test Class Names:

        - 없습니다. 모든 테스트는 함수로만 작성합니다
        - 코드 프랙티스가 정립되기전의 레거시 코드의 테스트를 다루는 경우에는 class를 사용할 수 있으나, 이 경우를 제외하고는 항상 함수 테스트만 작성하도록 합니다

        pytestmark

        - `@pytest.mark.django_db` 대신 파일 맨 위에 `pytestmark = [pytest.mark.django_db]` 사용합니다.
    </test>
</style>

<package-manager>
    <preference>
        - Always use UV if required
        - Poetry, Conda, requirements.txt is only for legacy
        - don't change any if working with legacy
    </preference>
    <uv>
        Don't use `uv pip install`; use `uv add` instead.
    </uv>

    <poetry>
        Still on legacy projects, you have to work with
    </poetry>

    <venv>
    Always check if a virtual environment is active before running Python commands.
    1. **Check the Python executable path:**
        ```sh
        which python
        ```
    2. **Verify the path:** If the output points to a system Python (e.g., `/usr/bin/python`), you are not in a virtual environment. A venv path typically includes `.venv` or a similar directory name.
    3. **If not in a venv:** Activate it or use a run command.
        -   **To activate:** `source .venv/bin/activate`
        -   **To run a command directly:** `uv run ...` or `poetry run ...`
    </venv>
</package-manager>

<django>
    1. Async/Await patterns:
        - Use `async for` for async iteration over querysets
        - Use list comprehension with `async for` for collecting async query results
        - Never assume existence of methods like `alist()` unless explicitly shown in codebase
        - Use `sync_to_async()` for calling sync code in async context
        - Use `async_to_sync()` for calling async code in sync context
        - Be careful with nested sync_to_async/async_to_sync to avoid deadlocks
        - Remember that Django ORM methods are sync by default unless explicitly async
    2. Type hints:
        - Use proper Django model type hints
        - Use QuerySet[ModelType] for queryset type hints
        - Use Manager[ModelType] for manager type hints
        - Use Optional[] for nullable fields
        - Use proper return types for async methods

    <django-model>
        Index:
        - unique constraint 생성시 `unique_together` 대신 `constraints=[UniqueConstraint]`를 사용
        Examples:
        ```python
        from django.db import models
        from django.db.models import UniqueConstraint
        class MyModel(models.Model):
            field1 = models.CharField(max_length=100)
            field2 = models.CharField(max_length=100)
            class Meta:
                constraints = [
                    UniqueConstraint(fields=['field1', 'field2'], name='unique_field1_field2')
                ]
        ```
    </django-model>
</django>

<naming-rules>
축약형 이름보다는 풀어쓰는 이름으로 항상 작성하세요.
예를들어 for m in mutations 같은 형태 대신 for mutation in mutations, SPageInfo 같은 형태 대신 StrawberryPageInfo 처럼 풀어서 이해하기 쉽도록 해주세요
</naming-rules>
