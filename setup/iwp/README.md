# setup/iwp/

The `iwp-runtime` bootstrap profile (W3a): an idempotent setup script that ends by running `preflight --tokens <profile tokens>` (game-archaeologist ADR-004). Its exit code is never trusted on its own.
