#!/usr/bin/env python
"""Benchmark key list endpoints with auth and cache-aware timing stats.

Usage:
  python scripts/benchmark_endpoints.py --base-url http://127.0.0.1:8000
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class BenchmarkResult:
    endpoint: str
    iterations: int
    first_ms: float
    mean_ms: float
    p50_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float
    hot_mean_ms: float


def _request_json(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any] | None = None,
    timeout: float = 15.0,
) -> tuple[int, Any]:
    data = None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url=url, method=method, data=data, headers=req_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.getcode(), json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        parsed = None
        if body:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError:
                parsed = body
        return exc.code, parsed
    except (urllib.error.URLError, ConnectionResetError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"Request error for {method} {url}: {exc}") from exc


def _get_token(base_url: str, username: str, password: str) -> str:
    login_url = f"{base_url}/api/v1/auth/login"
    register_url = f"{base_url}/api/v1/auth/register"

    def _login(candidate_username: str, candidate_password: str) -> tuple[int, Any]:
        return _request_json(
            "POST",
            login_url,
            payload={"username": candidate_username, "password": candidate_password},
        )

    def _register(candidate_username: str, candidate_password: str) -> tuple[int, Any]:
        return _request_json(
            "POST",
            register_url,
            payload={
                "username": candidate_username,
                "email": f"{candidate_username}@example.com",
                "password": candidate_password,
            },
        )

    status_code, body = _login(username, password)
    if status_code == 200 and isinstance(body, dict) and body.get("access_token"):
        return str(body["access_token"])

    if status_code in (401, 404):
        reg_status, reg_body = _register(username, password)
        status_code, body = _login(username, password)
        if status_code == 200 and isinstance(body, dict) and body.get("access_token"):
            return str(body["access_token"])

        # If preferred username cannot be used, fallback to a unique benchmark user.
        fallback_username = f"{username}_{int(time.time())}"
        reg_status_fb, reg_body_fb = _register(fallback_username, password)
        if reg_status_fb not in (200, 201, 400):
            raise RuntimeError(
                "Failed to register benchmark user. "
                f"initial_register=HTTP {reg_status} body={reg_body!r}, "
                f"fallback_register=HTTP {reg_status_fb} body={reg_body_fb!r}"
            )

        status_code_fb, body_fb = _login(fallback_username, password)
        if status_code_fb == 200 and isinstance(body_fb, dict) and body_fb.get("access_token"):
            return str(body_fb["access_token"])

        raise RuntimeError(
            "Failed to login benchmark user after registration attempts. "
            f"initial_login=HTTP {status_code} body={body!r}, "
            f"fallback_login=HTTP {status_code_fb} body={body_fb!r}"
        )

    raise RuntimeError(f"Failed to login benchmark user: HTTP {status_code} body={body!r}")


def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    idx = (len(values) - 1) * p
    low = int(idx)
    high = min(low + 1, len(values) - 1)
    if low == high:
        return values[low]
    return values[low] + (values[high] - values[low]) * (idx - low)


def benchmark_endpoint(
    base_url: str,
    path: str,
    token: str,
    warmup: int,
    iterations: int,
    timeout: float,
    retries: int,
) -> BenchmarkResult:
    url = f"{base_url}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    def _get_with_retries() -> tuple[int, Any]:
        attempts = max(1, retries + 1)
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                return _request_json("GET", url, headers=headers, timeout=timeout)
            except RuntimeError as exc:
                last_error = exc
                time.sleep(0.2)
        raise RuntimeError(f"Request failed after {attempts} attempts: {last_error}") from last_error

    for _ in range(warmup):
        status_code, body = _get_with_retries()
        if status_code != 200:
            raise RuntimeError(f"Warmup failed for {path}: HTTP {status_code} body={body!r}")

    timings: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        status_code, body = _get_with_retries()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        if status_code != 200:
            raise RuntimeError(f"Benchmark failed for {path}: HTTP {status_code} body={body!r}")
        timings.append(elapsed_ms)

    sorted_timings = sorted(timings)
    hot_timings = timings[1:] if len(timings) > 1 else timings

    return BenchmarkResult(
        endpoint=path,
        iterations=iterations,
        first_ms=timings[0],
        mean_ms=statistics.fmean(timings),
        p50_ms=_percentile(sorted_timings, 0.50),
        p95_ms=_percentile(sorted_timings, 0.95),
        min_ms=min(timings),
        max_ms=max(timings),
        hot_mean_ms=statistics.fmean(hot_timings),
    )


def print_result(result: BenchmarkResult) -> None:
    print(f"\nEndpoint: {result.endpoint}")
    print(f"  iterations: {result.iterations}")
    print(f"  first request (cold-ish): {result.first_ms:.2f} ms")
    print(f"  mean: {result.mean_ms:.2f} ms")
    print(f"  mean (hot): {result.hot_mean_ms:.2f} ms")
    print(f"  p50: {result.p50_ms:.2f} ms")
    print(f"  p95: {result.p95_ms:.2f} ms")
    print(f"  min/max: {result.min_ms:.2f} / {result.max_ms:.2f} ms")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Team Tournament API list endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    parser.add_argument("--username", default="benchmark_user", help="Username for auth")
    parser.add_argument("--password", default="benchmark_pass_123!", help="Password for auth")
    parser.add_argument("--warmup", type=int, default=3, help="Warmup requests per endpoint")
    parser.add_argument("--iterations", type=int, default=30, help="Measured requests per endpoint")
    parser.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=2, help="Retries per request on connection errors")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_url = args.base_url.rstrip("/")

    try:
        token = _get_token(base_url, args.username, args.password)
    except RuntimeError as exc:
        raise SystemExit(
            f"Unable to authenticate against {base_url}. "
            f"Make sure the API is running, then retry.\nDetails: {exc}"
        ) from exc

    print(f"Authenticated as '{args.username}'.")

    endpoints = [
        "/api/v1/players?skip=0&limit=100",
        "/api/v1/teams?skip=0&limit=100",
        "/api/v1/subteams?skip=0&limit=100",
    ]

    all_results: list[BenchmarkResult] = []
    for path in endpoints:
        try:
            result = benchmark_endpoint(
                base_url=base_url,
                path=path,
                token=token,
                warmup=args.warmup,
                iterations=args.iterations,
                timeout=args.timeout,
                retries=args.retries,
            )
        except RuntimeError as exc:
            raise SystemExit(
                f"Benchmark failed for {path}. "
                "Check API/server stability and retry.\n"
                f"Details: {exc}"
            ) from exc
        all_results.append(result)
        print_result(result)

    print("\nSummary (hot mean, lower is better):")
    for result in all_results:
        print(f"  {result.endpoint}: {result.hot_mean_ms:.2f} ms")


if __name__ == "__main__":
    main()
