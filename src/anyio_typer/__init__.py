import sys
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import anyio
from typer import Argument as Argument
from typer import Context as Context
from typer import Option as Option
from typer import Typer
from typer.main import (
    DEFAULT_MARKUP_MODE,
    Default,
    MarkupMode,
    TyperCommand,
    TyperGroup,
)

if sys.version_info >= (3, 13, 3):
    from warnings import deprecated
else:
    from typing_extensions import deprecated


T = TypeVar("T")
P = ParamSpec("P")

__author__ = "Vizonex"
__license__ = "MIT"
__version__ = "0.2.0"

# majority of functions were ripped from typer for
# hacking asyncrhonous code in to inject

__all__ = (
    "AnyioTyper",
    "Argument",
    "Context",
    "Option",
    "run",
    "trio_run",
    "uvloop_run",
)


class AnyioTyper(Typer):
    """Typer and Anyio commandline for making asynchronous CLIs"""

    # TODO: Might implement some new items into __init__ hence it's existance.
    def __init__(
        self,
        *,
        name: str | None = Default(None),
        cls: type[TyperGroup] | None = Default(None),
        invoke_without_command: bool = Default(False),
        no_args_is_help: bool = Default(False),
        subcommand_metavar: str | None = Default(None),
        chain: bool = Default(False),
        result_callback: Callable[..., Any] | None = Default(None),
        context_settings: dict[Any, Any] | None = Default(None),
        callback: Callable[..., Any] | None = Default(None),
        help: str | None = Default(None),
        epilog: str | None = Default(None),
        short_help: str | None = Default(None),
        options_metavar: str = Default("[OPTIONS]"),
        add_help_option: bool = Default(True),
        hidden: bool = Default(False),
        deprecated: bool = Default(False),
        add_completion: bool = True,
        rich_markup_mode: MarkupMode = DEFAULT_MARKUP_MODE,
        rich_help_panel: str | None = Default(None),
        suggest_commands: bool = True,
        pretty_exceptions_enable: bool = True,
        pretty_exceptions_show_locals: bool = True,
        pretty_exceptions_short: bool = True,
    ) -> None:
        super().__init__(
            name=name,
            cls=cls,
            invoke_without_command=invoke_without_command,
            no_args_is_help=no_args_is_help,
            subcommand_metavar=subcommand_metavar,
            chain=chain,
            result_callback=result_callback,
            context_settings=context_settings,
            callback=callback,
            help=help,
            epilog=epilog,
            short_help=short_help,
            options_metavar=options_metavar,
            add_help_option=add_help_option,
            hidden=hidden,
            deprecated=deprecated,
            add_completion=add_completion,
            rich_markup_mode=rich_markup_mode,
            rich_help_panel=rich_help_panel,
            suggest_commands=suggest_commands,
            pretty_exceptions_enable=pretty_exceptions_enable,
            pretty_exceptions_show_locals=pretty_exceptions_show_locals,
            pretty_exceptions_short=pretty_exceptions_short,
        )

    def _wrap(
        self,
        func: Callable[P, Awaitable[T]],
        backend: str = "asyncio",
        options: dict[str, Any] = {},
    ):
        """Used for assistance in wrapping functions
        so that the typer backend can understand how to
        read them. And remeber how to fire each task off.
        """

        @wraps(func)
        def sync_func(*args: P.args, **kwargs: P.kwargs) -> T:
            # Depacks Async function and then runs it
            async def _main(
                args: tuple[Any, ...], kwargs: dict[str, Any]
            ) -> T:
                return await func(*args, **kwargs)

            return anyio.run(
                _main,
                args,
                kwargs,
                backend=backend,
                backend_options=options,
            )

        return sync_func

    def anyio_callback(
        self,
        backend: str = "asyncio",
        options: dict[str, Any] = {},
        *,
        cls: type[TyperGroup] | None = Default(None),
        invoke_without_command: bool = Default(False),
        no_args_is_help: bool = Default(False),
        subcommand_metavar: str | None = Default(None),
        chain: bool = Default(False),
        result_callback: Callable[..., Any] | None = Default(None),
        context_settings: dict[Any, Any] | None = Default(None),
        help: str | None = Default(None),
        epilog: str | None = Default(None),
        short_help: str | None = Default(None),
        options_metavar: str | None = Default(None),
        add_help_option: bool = Default(True),
        hidden: bool = Default(False),
        deprecated: bool = Default(False),
        rich_help_panel: str | None = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """overrides callback to be fired using anyio instead

        ----

        **NOTE**: that this will not run on the same eventloop you may need
        to get creative or subclass off `AnyioTyper` if your goal is to make
        that work"""

        def decorator(
            async_func: Callable[P, Awaitable[T]],
        ) -> Callable[P, Awaitable[T]]:
            self.callback(
                cls=cls,
                invoke_without_command=invoke_without_command,
                no_args_is_help=no_args_is_help,
                subcommand_metavar=subcommand_metavar,
                chain=chain,
                result_callback=result_callback,
                context_settings=context_settings,
                help=help,
                epilog=epilog,
                short_help=short_help,
                options_metavar=options_metavar,
                add_help_option=add_help_option,
                hidden=hidden,
                deprecated=deprecated,
                rich_help_panel=rich_help_panel,
            )(self._wrap(async_func, backend=backend, options=options))
            return async_func

        return decorator

    def anyio_command(
        self,
        name: str | None = None,
        backend: str = "asyncio",
        options: dict[str, Any] = {},
        *,
        cls: type[TyperCommand] | None = None,
        context_settings: dict[Any, Any] | None = None,
        help: str | None = None,
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: str | None = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """
        Wraps in an asynchronous command to be initiated to run using
        anyio rather than a synchronous one.

        ---

        Based on anyio's own warnings, know that the current thread must
        not be already running an event loop.

        :param name: The name of this subcommand.
            See [the tutorial about name and help](https://typer.tiangolo.com/tutorial/subcommands/name-and-help)
            for different ways of setting a command's name, and which one takes
            priority.
        :type name: str | None
        :param backend: name of the asynchronous event loop implementation –
            currently either ``asyncio`` or ``trio``
        :type backend: str
        :param options: keyword arguments to call the backend
            implementation using documented [here](https://anyio.readthedocs.io/en/stable/basics.html#backend-options)
        :type options: dict[str, Any]
        :param cls: The class of this subcommand. Mainly used when
            [using the Click library underneath](https://typer.tiangolo.com/tutorial/using-click/).
            Can usually be left at the default value `None`.
            Otherwise, should be a subtype of `TyperGroup`.
            In our case with anyio-typer using it's sibling `async-click`
            would be an extermely a rare case scenario (currently,
            mixing both is obviously unsupported).
        :type cls: type[TyperCommand] | None
        :param context_settings: Pass configurations for the [context](https://typer.tiangolo.com/tutorial/commands/context/).
                Available configurations can be found in the docs for Click's
                `Context` [here](https://click.palletsprojects.com/en/stable/api/#context).
        :type context_settings: dict[Any, Any] | None
        :param help: Help text for the subcommand.
                See [the tutorial about name and help](https://typer.tiangolo.com/tutorial/subcommands/name-and-help)
                for different ways of setting a command's help, and which one
                takes priority.
        :type help: str | None
        :param epilog: Text that will be printed right after the help text.
        :type epilog: str | None
        :param short_help: A shortened version of the help text that can be
            used e.g. in the help table listing subcommands. When not defined,
            the normal `help` text will be used instead.
        :type short_help: str | None
        :param options_metavar: In the example usage string of the help text
            for a command, the default placeholder for various arguments
            is `[OPTIONS]`. Set `options_metavar` to change this into a
            different string. When `None`, the default value will be used.
        :type options_metavar: str
        :param add_help_option: **Note**: you probably shouldn't use this
                parameter, it is inherited
                from Click and supported for compatibility.

                ---
                By default each command registers a `--help` option. This can
                be disabled by this parameter.

        :type add_help_option: bool
        :param no_args_is_help:
            If this is set to `True`, running a command without any
            arguments will automatically show the help page.
        :type no_args_is_help: bool
        :param hidden:
            Hide this command from help outputs. `False` by default.
        :type hidden: bool
        :param deprecated:
                Mark this command as deprecated in the help outputs. `False` by
                default.
        :type deprecated: bool
        :param rich_help_panel:
                Set the panel name of the command when the help is printed with
                Rich.
        :type rich_help_panel: str | None
        :return: Wrapper to store a function with
        :rtype:
            Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]
        :raises RuntimeError: if an asynchronous event loop is already running
            in this thread
        :raises LookupError: if the named backend is not found
        """

        def decorator(
            async_func: Callable[P, Awaitable[T]],
        ) -> Callable[P, Awaitable[T]]:
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
            )(self._wrap(async_func, backend=backend, options=options))
            return async_func

        return decorator

    @deprecated(
        "winloop & uvloop together have now been supported since anyio"
        " 4.11+, try doing this instead\n"
        '\n@app.anyio_command(options={"use_uvloop": True},)\n'
        "def myfunc(...):"
        "\n    ..."
    )
    def uvloop_command(
        self,
        name: str | None = None,
        *,
        cls: type[TyperCommand] | None = None,
        context_settings: dict[Any, Any] | None = None,
        help: str | None = None,
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: str | None = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """Helps to configure either uvloop or winloop.

        WARNING
        -------

        THIS FUNCTIONALITY IS DEPRECTAED TRY THIS INSTEAD!!!

        ::

            from anyio_typer import AnyioTyper

            app = AnyioTyper()

            @app.anyio_command(options={"use_uvloop": True})
            def myfunc(arg:str):
                ...

        """

        return self.anyio_command(
            name,
            cls=cls,
            backend="asyncio",
            options={"use_uvloop": True},
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

    @deprecated(
        "Functionality for wrapping Trio is obsolete use\n"
        '`anyio_command(backend="trio")` instead'
    )
    def trio_command(
        self,
        name: str | None = None,
        *,
        cls: type[TyperCommand] | None = None,
        context_settings: dict[Any, Any] | None = None,
        help: str | None = None,
        epilog: str | None = None,
        short_help: str | None = None,
        options_metavar: str = "[OPTIONS]",
        add_help_option: bool = True,
        no_args_is_help: bool = False,
        hidden: bool = False,
        deprecated: bool = False,
        rich_help_panel: str | None = Default(None),
    ) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
        """Helps to configure either uvloop or winloop.

        WARNING
        -------

        THIS FUNCTIONALITY IS DEPRECTAED TRY THIS INSTEAD!!!

        ::

            from anyio_typer import AnyioTyper

            app = AnyioTyper()

            @app.anyio_command(backend='trio')
            def myfunc(arg:str):
                ...

        """
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


@deprecated(
    "winloop support was added in anyio in 4.11+ use "
    '`run(func, options={"use_uvloop": True})` or'
    '`run(func, "asyncio", {"use_uvloop": True})`  instead'
)
def uvloop_run(
    function: Callable[..., Awaitable[Any]],
):
    """Runs a uvloop/winloop command over a single application.
    if operating system is windows `winloop` is used otherwise use `uvloop`
    """
    run(function, "asyncio", {"use_uvloop": True})


@deprecated(
    "Functionality for wrapping Trio is obsolete use\n"
    '`run(func, "trio")` instead'
)
def trio_run(
    function: Callable[..., Awaitable[Any]],
):
    """Runs trio command over a single application"""
    run(function, "trio")
