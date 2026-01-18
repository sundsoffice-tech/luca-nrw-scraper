# -*- coding: utf-8 -*-
"""
Simple logging utilities for the network layer.
"""

import json
from datetime import datetime


def log(level: str, msg: str, **ctx):
    """
    Log a message with optional context.
    
    Args:
        level: Log level (info, warn, error, debug, fatal)
        msg: Log message
        **ctx: Additional context key-value pairs
    """
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ctx_str = (" " + json.dumps(ctx, ensure_ascii=False)) if ctx else ""
    line = f"[{ts}] [{level.upper():7}] {msg}{ctx_str}"
    print(line, flush=True)
