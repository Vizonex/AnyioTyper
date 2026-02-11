import asyncio
import sys
import typing
from enum import Enum

import pytest
from typer.testing import CliRunner

from anyio_typer import AnyioTyper


class User(str, Enum):
    rick = "Rick"
    morty = "Morty"


PARAMS = [
    pytest.param(
        ("asyncio", {"use_uvloop": True}),  # anyio now supports winloop
        id="asyncio[uvloop]"
        if sys.platform != "win32"
        else "asyncio[winloop]",
    ),
    pytest.param(("asyncio", {"use_uvloop": False}), id="asyncio"),
    pytest.param(("trio", {}), id="trio"),
]

if sys.platform == "win32":
    PARAMS.append(
        pytest.param(
            ("asyncio", {"loop_factory": asyncio.SelectorEventLoop}),
            id="asyncio[win32+selector]",
        ),
    )


@pytest.fixture(params=PARAMS)
def anyio_backend(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture()
def typer_runner() -> CliRunner:
    return CliRunner()


def test_enum_choice(
    typer_runner: CliRunner, anyio_backend: tuple[str, dict[str, typing.Any]]
) -> None:
    # This test is only for coverage of the new custom TyperChoice class
    _anyio_name, data = anyio_backend

    app = AnyioTyper(context_settings={"token_normalize_func": str.lower})

    @app.anyio_command(
        backend=_anyio_name,
        options=data,
    )
    async def hello(name: User = User.rick) -> None:
        print(f"Hello {name.value}!")

    result = typer_runner.invoke(
        app, ["--name", "morty"], catch_exceptions=False
    )
    assert result.exit_code == 0
