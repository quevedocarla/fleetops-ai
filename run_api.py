import asyncio
import selectors

import uvicorn


def create_selector_event_loop():

    selector = (
        selectors.SelectSelector()
    )

    loop = (
        asyncio.SelectorEventLoop(
            selector
        )
    )

    asyncio.set_event_loop(
        loop
    )

    return loop


async def main():

    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )

    server = uvicorn.Server(
        config
    )

    await server.serve()


if __name__ == "__main__":

    asyncio.run(
        main(),
        loop_factory=
            create_selector_event_loop,
    )