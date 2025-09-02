import sys
from functools import wraps
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Optional,
    Type,
    TypeVar,
    Union,
)

import anyio
from typer import Option as Option, Typer
from typer.main import Default, TyperCommand
import sys

if sys.version_info < (3, 10):
    from typing_extensions import ParamSpec
else:
    from typing import ParamSpec

T = TypeVar("T")
P = ParamSpec("P")

__author__ = "Vizonex"
__license__ = "MIT"
__version__ = "0.1.0"


# majority of functions were ripped from typer for hacking asyncrhonous code in to inject


class AnyioTyper(Typer):
    """Typer and Anyio commandline for making asynchronous CLIs"""

    def anyio_command(
        self,
        name: Optional[str] = None,
        backend: str = "asyncio",
        options: dict[str, str] = {},
        *,
        cls: Optional[Type[TyperCommand]] = None,
        context_settings: Optional[Dict[Any, Any]] = None,
        help: Optional[str] = None,
        epilog: Optional[str] = None,
        short_help: Optional[str] = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        # Rich settings
        rich_help_panel: Union[str, None] = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """Wraps in an asynchronous command rather than a synchronous one"""

        def decorator(
            async_func: Callable[P, Awaitable[T]],
        ) -> Callable[P, Awaitable[T]]:
            @wraps(async_func)
            def sync_func(*args: P.args, **kwargs: P.kwargs) -> T:
                # Depacks Async function and then runs it
                async def _main(args: tuple[Any, ...], kwargs: dict[str, Any]) -> T:
                    return await async_func(*args, **kwargs)

                return anyio.run(
                    _main, args, kwargs, backend=backend, backend_options=options
                )

            self.command(
                name,
                cls=cls,
                context_settings=context_settings,
                help=help,
                epilog=epilog,
                short_help=short_help,
                options_metavar=options_metavar,
                add_help_option=add_help_option,
                no_args_is_help=no_args_is_help,
                hidden=hidden,
                deprecated=deprecated,
                rich_help_panel=rich_help_panel,
            )(sync_func)

            return async_func

        return decorator

    def uvloop_command(
        self,
        name: Optional[str] = None,
        *,
        cls: Optional[Type[TyperCommand]] = None,
        context_settings: Optional[Dict[Any, Any]] = None,
        help: Optional[str] = None,
        epilog: Optional[str] = None,
        short_help: Optional[str] = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: Union[str, None] = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """Helps to configure either uvloop or winloop."""

        # XXX: winloop is currently not supported by anyio without 
        # passing something hacky tricks so this function was made 
        # to enable this feature
        if sys.platform == "win32":
            import winloop as uvloop
        else:
            import uvloop

        return self.anyio_command(
            name,
            cls=cls,
            backend="asyncio",
            options={"loop_factory": uvloop.new_event_loop},
            context_settings=context_settings,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            no_args_is_help=no_args_is_help,
            hidden=hidden,
            deprecated=deprecated,
            rich_help_panel=rich_help_panel,
        )

    def trio_command(
        self,
        name: Optional[str] = None,
        *,
        cls: Optional[Type[TyperCommand]] = None,
        context_settings: Optional[Dict[Any, Any]] = None,
        help: Optional[str] = None,
        epilog: Optional[str] = None,
        short_help: Optional[str] = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: Union[str, None] = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        return self.anyio_command(
            name,
            backend="trio",
            cls=cls,
            context_settings=context_settings,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            no_args_is_help=no_args_is_help,
            hidden=hidden,
            deprecated=deprecated,
            rich_help_panel=rich_help_panel,
        )


def run(
    function: Callable[..., Awaitable[Any]],
    backend: str = "asyncio",
    options: dict[str, str] = {},
) -> None:
    """Runs a command asynchronously"""
    app = AnyioTyper(add_completion=False)
    app.anyio_command(backend=backend, options=options)(function)
    app()


def uvloop_run(
    function: Callable[..., Awaitable[Any]],
):
    """Runs a uvloop/winloop command over a single application.
    if operating system is windows `winloop` is used otherwise use `uvloop`
    """
    app = AnyioTyper(add_completion=False)
    app.uvloop_command()(function)
    app()


def trio_run(
    function: Callable[..., Awaitable[Any]],
):
    """Runs trio command over a single application"""
    app = AnyioTyper(add_completion=False)
    app.trio_command()(function)
    app()
