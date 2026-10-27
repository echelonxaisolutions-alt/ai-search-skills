"""Shared helpers for crawl4ai skill scripts. Import, don't run."""
import asyncio
import sys


def run(coro):
    """Run an async main() with the correct Windows event-loop policy.

    Playwright launches the browser via a subprocess, which on Windows needs the
    Proactor loop (the default on 3.8+, but we set it explicitly so the scripts
    are robust no matter how they're invoked)."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    return asyncio.run(coro)


def browser_config(stealth=False, headless=True, proxy=None, user_data_dir=None):
    from crawl4ai import BrowserConfig
    kwargs = dict(headless=headless, verbose=False)
    if proxy:
        kwargs["proxy"] = proxy
    if user_data_dir:
        # Persistent profile = keep a logged-in session across runs.
        kwargs["use_managed_browser"] = True
        kwargs["user_data_dir"] = user_data_dir
    if stealth:
        # patchright + stealth patches ship with crawl4ai; browser_type switch
        # to the undetected engine when available.
        kwargs["enable_stealth"] = True
    try:
        return BrowserConfig(**kwargs)
    except TypeError:
        # Older/newer field names: drop unknown keys and retry minimally.
        return BrowserConfig(headless=headless, verbose=False)


def cache_mode(fresh):
    from crawl4ai import CacheMode
    return CacheMode.BYPASS if fresh else CacheMode.ENABLED


def eprint(*a):
    print(*a, file=sys.stderr)
