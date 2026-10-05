"""Stealth browser engine: Camoufox-first with transparent Playwright fallback.

Why Camoufox?
    Free, open-source anti-detect Firefox fork built for web scraping & AI agents
    (github.com/daijro/camoufox). Unlike JS-injection stealth (playwright-stealth),
    Camoufox spoofs fingerprints at the C++ implementation level - navigator,
    WebGL, fonts, WebRTC, timezone/locale, voices - so job boards cannot detect
    automation through JavaScript inspection. It exposes the standard Playwright
    API, so call sites barely change.

Disk discipline (project constraint: D-drive only)
    ``camoufox.pkgman`` resolves its storage root via
    ``platformdirs.user_cache_dir("camoufox")`` ONCE, at import time. We
    intercept that exact call and pin it to ``data/camoufox`` (override with the
    ``CAMOUFOX_INSTALL_DIR`` env var) BEFORE the first camoufox import, so the
    browser binary, GeoIP database and version metadata never land on C:.

Fallback guarantee
    If the ``camoufox`` package or its browser build is missing - or a launch
    fails - every entry point transparently falls back to vanilla Playwright
    Chromium (plus playwright-stealth when installed). Stealth is an upgrade,
    never a hard dependency: tests and CI keep working without it.

Usage
    Sync (scraper thread)::

        with launch_sync(headless=True) as browser:          # Browser object
            ctx = new_context_for(browser, locale="en-US")

    Sync (review-first autofill, visible window)::

        with launch_sync(headless=False, user_data_dir=profile, humanize=True) as ctx:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()

    Async (LLM apply loop)::

        async with launch_async(user_data_dir=profile, headless=True) as ctx:
            page = ctx.pages[0] if ctx.pages else await ctx.new_page()

    The yielded object is a Playwright *Browser* for ephemeral launches and a
    *BrowserContext* whenever ``user_data_dir`` is supplied (both engines agree
    on this shape).

CLI
    python -m src.stealth_browser --status   # what is installed, where
    python -m src.stealth_browser --fetch    # download browser to data/camoufox
"""
from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Iterator, Optional

logger = logging.getLogger(__name__)

# Engine used by the most recent successful launch ("camoufox" | "playwright").
last_engine: str = "none"

# Chromium-only flags kept for the fallback path (ignored by Firefox/Camoufox).
_CHROMIUM_STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]


def _enabled_by_env() -> bool:
    """Respect an explicit kill-switch: CAMOUFOX_ENABLED=0 forces Playwright."""
    return os.environ.get("CAMOUFOX_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}


def install_root() -> Path:
    """Where the Camoufox browser payload lives (always on the project drive)."""
    env = os.environ.get("CAMOUFOX_INSTALL_DIR", "").strip()
    if env:
        return Path(env)
    # Import lazily: this module must stay importable from any context.
    from . import config

    return config.DATA_DIR / "camoufox"


_storage_patched = False


def _apply_storage_redirect() -> None:
    """Pin camoufox's INSTALL_DIR to our D-drive root before first import.

    ``camoufox.pkgman`` executes ``INSTALL_DIR = Path(user_cache_dir("camoufox"))``
    at import time; wrapping ``platformdirs.user_cache_dir`` beforehand redirects
    every downstream path (binary, GeoIP DB, version.json, fontconfig cache)
    without touching any camoufox internals.
    """
    global _storage_patched
    if _storage_patched:
        return
    root = install_root()
    root.mkdir(parents=True, exist_ok=True)

    import platformdirs

    _original = platformdirs.user_cache_dir

    def _patched(appname: Optional[str] = None, *args: Any, **kwargs: Any) -> str:
        if appname == "camoufox":
            return str(root)
        return _original(appname, *args, **kwargs)  # type: ignore[misc]

    platformdirs.user_cache_dir = _patched  # type: ignore[assignment]
    _storage_patched = True


def _import_camoufox() -> Any | None:
    """Return the camoufox module after applying the storage redirect, or None."""
    if not _enabled_by_env():
        return None
    try:
        _apply_storage_redirect()
        import camoufox  # noqa: F401 - presence check only

        return camoufox
    except Exception as exc:  # ImportError or anything odd during patching
        logger.debug("camoufox unavailable (%s); stealth upgrades disabled", exc)
        return None


def camoufox_available() -> bool:
    """True when the package AND a fetched browser executable are usable."""
    camoufox = _import_camoufox()
    if camoufox is None:
        return False
    # Direct check against pkgman's launch_path logic (mirrors upstream CLI).
    try:
        from camoufox.pkgman import LAUNCH_FILE, OS_NAME, get_path

        exe = get_path(LAUNCH_FILE[OS_NAME])
        return Path(exe).exists()
    except Exception:
        return False


def _base_options(headless: bool, user_data_dir: Optional[str | Path],
                  proxy_url: Optional[str], humanize: bool) -> dict[str, Any]:
    """Options shared by sync/async Camoufox launches."""
    opts: dict[str, Any] = {
        "headless": bool(headless),
        # Pin fingerprint OS to the host OS family: bundled Windows fonts and
        # GPU strings then match reality, avoiding cross-OS consistency tells.
        "os": "windows",
        # Docs: caching costs memory and enables back/forward only. Off.
        "enable_cache": False,
    }
    if user_data_dir:
        opts["persistent_context"] = True
        opts["user_data_dir"] = _engine_profile_dir(user_data_dir)
    if humanize:
        opts["humanize"] = True
    if proxy_url:
        opts["proxy"] = {"server": proxy_url}
        # Align timezone/locale/lat-lon/WebRTC with the exit IP (needs [geoip]).
        opts["geoip"] = True
    return opts


def _engine_profile_dir(user_data_dir: str | Path, isolate_worker: bool = True) -> str:
    """Give each engine and worker process its own profile directory.

    Chromium and Firefox profile layouts are incompatible; sharing one directory
    across engines risks corruption. Camoufox gets ``<dir>-camoufox`` next to it.
    Multi-process tasks are isolated by PID to prevent Firefox parent.lock collisions.
    """
    p = Path(user_data_dir)
    target = p.with_name(p.name + "-camoufox")
    if isolate_worker:
        target = target / f"worker_{os.getpid()}"
    target.mkdir(parents=True, exist_ok=True)

    # Clean up stale parent.lock if leftover from an interrupted session
    lock_file = target / "parent.lock"
    if lock_file.exists():
        try:
            lock_file.unlink()
        except Exception:
            pass
    return str(target)


def _enter_camoufox(stack: Any, make_cm: Any, opts: dict[str, Any]) -> Any:
    """Enter a Camoufox context manager; degrade gracefully on geoip issues.

    The [geoip] extra downloads a MaxMind dataset on first use; if that fails
    (offline, blocked), retry once without geoip rather than losing stealth.
    """
    try:
        return stack.enter_context(make_cm(**opts))
    except Exception as exc:
        if "geoip" in opts:
            logger.warning("Camoufox geoip failed (%s); retrying without IP geolocation", exc)
            opts.pop("geoip", None)
            return stack.enter_context(make_cm(**opts))
        raise


async def _enter_camoufox_async(stack: Any, make_cm: Any, opts: dict[str, Any]) -> Any:
    """Async enter a Camoufox context manager for AsyncCamoufox."""
    try:
        return await stack.enter_async_context(make_cm(**opts))
    except Exception as exc:
        if "geoip" in opts:
            logger.warning("Camoufox geoip failed (%s); retrying without IP geolocation", exc)
            opts.pop("geoip", None)
            return await stack.enter_async_context(make_cm(**opts))
        raise


@contextmanager
def launch_sync(
    *,
    headless: bool = False,
    user_data_dir: Optional[str | Path] = None,
    proxy_url: Optional[str] = None,
    humanize: bool = False,
) -> Iterator[Any]:
    """Yield a Browser (ephemeral) or BrowserContext (persistent), stealth-first."""
    global last_engine
    proxy_url = proxy_url if proxy_url is not None else _configured_proxy()
    if _import_camoufox() is not None and camoufox_available():
        from contextlib import ExitStack

        from camoufox.sync_api import Camoufox

        opts = _base_options(headless, user_data_dir, proxy_url, humanize)
        with ExitStack() as stack:
            try:
                browser = _enter_camoufox(stack, Camoufox, opts)
                last_engine = "camoufox"
                logger.info("Stealth engine: Camoufox (headless=%s)", headless)
            except Exception as exc:
                logger.warning("Camoufox launch failed (%s); falling back to Chromium", exc)
                browser = None
            if browser is not None:
                yield browser
                return
    # Fallback: vanilla Playwright Chromium (previous behaviour, preserved).
    last_engine = "playwright"
    logger.info("Stealth engine: Playwright Chromium fallback (headless=%s)", headless)
    with _fallback_sync(headless, user_data_dir, proxy_url) as browser:
        yield browser


@asynccontextmanager
async def launch_async(
    *,
    headless: bool = True,
    user_data_dir: Optional[str | Path] = None,
    proxy_url: Optional[str] = None,
    humanize: bool = False,
) -> AsyncIterator[Any]:
    """Async mirror of :func:`launch_sync` for the LLM apply loop."""
    global last_engine
    proxy_url = proxy_url if proxy_url is not None else _configured_proxy()
    if _import_camoufox() is not None and camoufox_available():
        from contextlib import AsyncExitStack

        from camoufox.async_api import AsyncCamoufox

        opts = _base_options(headless, user_data_dir, proxy_url, humanize)
        async with AsyncExitStack() as stack:
            try:
                browser = await _enter_camoufox_async(stack, AsyncCamoufox, opts)
                last_engine = "camoufox"
                logger.info("Stealth engine: Camoufox async (headless=%s)", headless)
            except Exception as exc:
                logger.warning("Camoufox async launch failed (%s); falling back", exc)
                browser = None
            if browser is not None:
                yield browser
                return
    last_engine = "playwright"
    async with _fallback_async(headless, user_data_dir, proxy_url) as browser:
        yield browser


def _configured_proxy() -> Optional[str]:
    try:
        from . import config

        return config.proxy_url() or None
    except Exception:
        return None


@contextmanager
def _fallback_sync(headless: bool, user_data_dir: Optional[str | Path],
                   proxy_url: Optional[str]) -> Iterator[Any]:
    from playwright.sync_api import sync_playwright

    proxy_settings = {"server": proxy_url} if proxy_url else None
    with sync_playwright() as p:
        if user_data_dir:
            ctx = p.chromium.launch_persistent_context(
                str(user_data_dir), headless=headless, proxy=proxy_settings,
                accept_downloads=True, args=_CHROMIUM_STEALTH_ARGS,
            )
            try:
                yield ctx
            finally:
                ctx.close()
        else:
            browser = p.chromium.launch(headless=headless, proxy=proxy_settings,
                                        args=_CHROMIUM_STEALTH_ARGS)
            try:
                yield browser
            finally:
                browser.close()


@asynccontextmanager
async def _fallback_async(headless: bool, user_data_dir: Optional[str | Path],
                          proxy_url: Optional[str]) -> AsyncIterator[Any]:
    from playwright.async_api import async_playwright

    proxy_settings = {"server": proxy_url} if proxy_url else None
    p = await async_playwright().start()
    try:
        if user_data_dir:
            ctx = await p.chromium.launch_persistent_context(
                str(user_data_dir), headless=headless, proxy=proxy_settings,
                args=_CHROMIUM_STEALTH_ARGS,
            )
            try:
                yield ctx
            finally:
                await ctx.close()
        else:
            browser = await p.chromium.launch(headless=headless, proxy=proxy_settings,
                                              args=_CHROMIUM_STEALTH_ARGS)
            try:
                yield browser
            finally:
                await browser.close()
    finally:
        await p.stop()


# --- Status / installation helpers -------------------------------------------

def status() -> dict[str, Any]:
    """Machine-readable summary for --status and future Settings UI."""
    package = _import_camoufox() is not None
    browser_fetched = False
    exe_path = ""
    if package:
        try:
            from camoufox.pkgman import LAUNCH_FILE, OS_NAME, get_path

            exe_path = get_path(LAUNCH_FILE[OS_NAME])
            browser_fetched = Path(exe_path).exists()
        except Exception:
            pass
    try:
        from importlib.metadata import version as _meta_version

        pkg_version: Optional[str] = _meta_version("camoufox")
    except Exception:
        pkg_version = None
    return {
        "engine_last_used": last_engine,
        "package_installed": package,
        "package_version": pkg_version,
        "browser_fetched": browser_fetched,
        "executable": exe_path,
        "install_root": str(install_root()),
        "enabled_via_env": _enabled_by_env(),
    }


def fetch_browser() -> str:
    """Download the active Camoufox build into install_root() (D-drive safe).

    Mirrors ``python -m camoufox fetch`` but keeps the storage redirect active.
    """
    if _import_camoufox() is None:
        raise RuntimeError(
            "The 'camoufox' package is not installed.\n"
            'Install it with: pip install -U "camoufox[geoip]"'
        )
    _apply_storage_redirect()
    from camoufox.pkgman import CamoufoxFetcher

    fetcher = CamoufoxFetcher()
    fetcher.install()
    st = status()
    return f"Installed {st['executable']}" if st["browser_fetched"] else "Fetch finished."


def _cli(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Stealth browser engine control")
    parser.add_argument("--fetch", action="store_true", help="Download/update the Camoufox browser")
    parser.add_argument("--status", action="store_true", help="Show engine status as JSON")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.fetch:
        print(fetch_browser())
        return 0
    print(json.dumps(status(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
