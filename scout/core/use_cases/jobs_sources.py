"""Job source detection and URL normalization."""

from __future__ import annotations

from enum import Enum
from urllib.parse import urlparse


class JobSourcePlatform(str, Enum):
    GREENHOUSE = "greenhouse"
    ASHBY = "ashby"
    WORKDAY = "workday"
    NATIVE = "native"
    UNKNOWN = "unknown"


def detect_job_source_platform(url: str) -> JobSourcePlatform:
    host = urlparse(url).netloc.lower()
    if "greenhouse.io" in host:
        return JobSourcePlatform.GREENHOUSE
    if "ashbyhq.com" in host:
        return JobSourcePlatform.ASHBY
    if "myworkdayjobs.com" in host:
        return JobSourcePlatform.WORKDAY
    if host:
        return JobSourcePlatform.NATIVE
    return JobSourcePlatform.UNKNOWN
