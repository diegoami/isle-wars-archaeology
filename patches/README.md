# patches/

Recipes for derived variants (`variant/1`): a patch script plus `<variant>.json`. The script asserts the input bytes at every patch site and the output hash. Patched binaries are rebuilt locally from the user's copy and never stored anywhere (ADR-006).
