# AnyioTyper
Wraps In Typer with Anyio, unlike `Async-Typer` AnyioTyper's goal is to allow customization 
with different eventloops 

```python
from anyio_typer import AnyioTyper, Option
from typing import Annotated
app = AnyioTyper()

# This example uses a library called cyares you can install it with `pip install cyares`

# NOTE: winloop is supported by default if your on a windows operating system
@app.uvloop_command()
async def uvloop(
    host:str,
    rt:Annotated[str, Option(help="A Type of record to uncover", show_default=True)] = "A" 
    ):
    """Use Uvloop or Winloop for DNS Resolving"""
    
    from cyares.aio import DNSResolver

    async with DNSResolver(["8.8.8.8", "8.8.4.4"]) as resolver:
        result = await resolver.query(host, rt)
    print(result)

@app.trio_command()
async def trio(
    host:str,
    rt:Annotated[str, Option(help="A Type of record to uncover", show_default=True)] = "A" 
    ):
    """Use Trio for DNS Resolving"""
    from cyares.trio import DNSResolver

    async with DNSResolver(["8.8.8.8", "8.8.4.4"]) as resolver:
        result = await resolver.query(host, rt)
    print(result)


if __name__ == "__main__":
    app()
```
