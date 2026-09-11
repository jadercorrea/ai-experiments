# Semantic patch construction task 001

This local, permanently contaminated task isolates the edit representation.
Both arms begin with the TypeScript projection of the same persistent semantic
program and face the same public and hidden Deno tests.

- `source_patch` applies a unified diff in an audited staging workspace.
- `semantic_patch` applies checked subtree replacements to the persistent IR,
  validates the result, and projects it deterministically.

The reference artifacts establish construction viability only. They are public,
so this task cannot support a model-efficacy claim.
