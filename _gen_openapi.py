"""Generate OpenAPI schema from the FastAPI app and verify endpoints."""

import json
import os
import sys
from pathlib import Path

from ai_gateway.main import app

schema = app.openapi()
paths = sorted(schema["paths"].keys())
print("Registered paths:")
for p in paths:
    methods = list(schema["paths"][p].keys())
    print(f"  {methods[0].upper():7s} {p}")

required = [
    ("/v1/health", "get"),
    ("/v1/prompt-version", "get"),
    ("/v1/dialogue/respond", "post"),
    ("/v1/dialogue/classify-intent", "post"),
    ("/v1/case/recap", "post"),
]
print()
all_ok = True
for path, method in required:
    if path in schema["paths"] and method in schema["paths"][path]:
        print(f"  OK {method.upper():7s} {path}")
    else:
        print(f"  MISSING: {method.upper():7s} {path}")
        all_ok = False

out_dir = os.path.join(os.path.dirname(__file__), "docs")
os.makedirs(out_dir, exist_ok=True)
with open(os.path.join(out_dir, "openapi.json"), "w") as f:
    json.dump(schema, f, indent=2)

print("\nOpenAPI schema saved to docs/openapi.json")
print(f"Total {len(paths)} endpoints registered")
print(f"All required endpoints present: {all_ok}")

sys.exit(0 if all_ok else 1)
