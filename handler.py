"""
Single, static RunPod Serverless entrypoint.

RunPod's GitHub-repo deploy check resolves the Dockerfile's CMD to a
concrete entrypoint file and verifies that file calls
runpod.serverless.start(...). A shell `if/then/else` CMD switching
between src/handler_direct.py and src/handler_streaming.py at container
start gives it no single file to resolve, which produced a false
"handler not found" result even though the call exists in both files.

This file is the one thing the Dockerfile CMD always runs. It performs
the HANDLER_TYPE branch in Python (not shell) and is the only place that
calls runpod.serverless.start() inside the built image, so static
detection always finds it regardless of HANDLER_TYPE.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import runpod

HANDLER_TYPE = os.environ.get("HANDLER_TYPE", "direct").lower()

if HANDLER_TYPE == "streaming":
    from handler_streaming import handler_streaming

    runpod.serverless.start({
        "handler": handler_streaming,
        "return_aggregate_stream": True,
    })
else:
    from handler_direct import handler_direct

    runpod.serverless.start({"handler": handler_direct})
