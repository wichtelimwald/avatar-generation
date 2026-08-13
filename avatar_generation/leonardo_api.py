"""
Shared Avatar Generation — Leonardo.ai API Client

Functions for interacting with the Leonardo.ai REST API:
generation submission, polling, and image download.
"""
from __future__ import annotations

import time

import requests

from config import LEONARDO_API_BASE


def request_with_retry(method: str, url: str, headers: dict,
                       max_retries: int = 3, **kwargs) -> requests.Response:
    """Make an HTTP request with retry logic for transient errors."""
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.request(method, url, headers=headers, **kwargs)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 15))
                print(f"  ⏳ Rate limited (429). Waiting {retry_after}s "
                      f"(attempt {attempt}/{max_retries})...")
                time.sleep(retry_after)
                continue

            if response.status_code >= 500 and attempt < max_retries:
                wait = 5 * attempt
                print(f"  ⚠️  Server error ({response.status_code}). "
                      f"Retrying in {wait}s (attempt {attempt}/{max_retries})...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except requests.exceptions.ConnectionError as exc:
            if attempt < max_retries:
                wait = 5 * attempt
                print(f"  ⚠️  Connection error: {exc}. "
                      f"Retrying in {wait}s (attempt {attempt}/{max_retries})...")
                time.sleep(wait)
                continue
            raise

    # Final attempt after all retries exhausted
    response = requests.request(method, url, headers=headers, **kwargs)
    response.raise_for_status()
    return response


def create_generation(api_key: str, prompt: str, negative: str,
                      generation_params: dict,
                      seed: int | None = None,
                      transparency: str | None = None) -> dict:
    """Submit a generation request to Leonardo.ai API.

    Args:
        api_key: Leonardo.ai API key.
        prompt: Positive prompt text.
        negative: Negative prompt text.
        generation_params: Generation parameters (model, size, steps, etc.).
        seed: Optional fixed seed for reproducibility.
        transparency: Optional transparency mode (e.g. ``"foreground_only"``).
    """
    url = f"{LEONARDO_API_BASE}/generations"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
    }

    payload = {
        **generation_params,
        "prompt": prompt,
        "negative_prompt": negative,
    }
    if seed is not None:
        payload["seed"] = seed
    if transparency is not None:
        payload["transparency"] = transparency

    response = request_with_retry("POST", url, headers, json=payload, timeout=60)
    data = response.json()

    generation_id = data.get("sdGenerationJob", {}).get("generationId")
    if not generation_id:
        raise ValueError(f"No generationId in response: {data}")

    return {
        "generationId": generation_id,
        "prompt_length": len(prompt),
        "negative_length": len(negative),
        "seed": seed,
    }


def poll_generation(api_key: str, generation_id: str,
                    max_wait: int = 120) -> dict:
    """Poll for generation completion and return the result."""
    url = f"{LEONARDO_API_BASE}/generations/{generation_id}"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}",
    }

    start = time.time()
    while time.time() - start < max_wait:
        response = request_with_retry("GET", url, headers, timeout=30)
        data = response.json()

        generation = data.get("generations_by_pk", {})
        status = generation.get("status")

        if status == "COMPLETE":
            return generation
        elif status == "FAILED":
            raise RuntimeError(f"Generation failed: {generation}")

        print(f"  Status: {status} — waiting 5s...")
        time.sleep(5)

    raise TimeoutError(
        f"Generation {generation_id} did not complete within {max_wait}s"
    )


def download_image(url: str, output_path) -> None:
    """Download an image from a URL to a local path."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    print(f"  Downloaded: {output_path} ({len(response.content)} bytes)")
