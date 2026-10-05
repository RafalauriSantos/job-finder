"""Optional, deliberately bounded Playwright collector.

It requires a separate local profile and a manually authenticated session.
It stops on challenge/rate-limit signals and never attempts to bypass them.
"""
import asyncio
import json
import os
import time
from urllib.request import Request, urlopen
from pathlib import Path

from core.linkedin_ingest import RateController


async def collect(urls, profile=None):
    from playwright.async_api import async_playwright
    profile = profile or str(Path.home() / ".job-finder" / "linkedin-browser")
    governor = RateController(
        max_actions_per_hour=int(os.getenv("LINKEDIN_MAX_ACTIONS_PER_HOUR", "12")),
        min_interval_seconds=int(os.getenv("LINKEDIN_MIN_INTERVAL_SECONDS", "120")),
    )
    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(profile, headless=False)
        page = await browser.new_page()
        for url in urls:
            now = time.time()
            if not governor.allow(now):
                break
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            body = (await page.locator("body").inner_text()).lower()
            if any(signal in body for signal in ("captcha", "verify", "unusual activity", "temporarily restricted")):
                governor.pause(time.time())
                break
            cards = await page.locator('div[data-urn], div.feed-shared-update-v2, article').all()
            for card in cards:
                text = (await card.inner_text()).strip()
                if not text:
                    continue
                links = await card.locator('a[href]').evaluate_all("els => els.map(e => e.href)")
                payload = json.dumps({"url": next((x for x in links if 'linkedin.com/' in x), url),
                                      "text": text, "source_type": "post"}).encode()
                request = Request("http://127.0.0.1:8765/v1/linkedin/captures", data=payload,
                                  headers={"Content-Type": "application/json"}, method="POST")
                try:
                    with urlopen(request, timeout=5):
                        pass
                except OSError:
                    pass
            governor.record(time.time())
            await asyncio.sleep(2)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(collect(os.getenv("LINKEDIN_URLS", "").split(",")))
