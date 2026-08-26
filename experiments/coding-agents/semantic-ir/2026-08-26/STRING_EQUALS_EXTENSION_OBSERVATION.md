# Pure string equality extension observation

## Result

Semantic IR catalog v1 adds one operation:

```text
string.equals(string, string) -> boolean
```

The operation is exact, case-sensitive, and pure. It requires no runtime
capability, contributes no declared effect, executes directly in the reference
interpreter, and projects deterministically to TypeScript `===`.

With this addition, a checked semantic patch can express the frozen
`reserved-id-guard-001` task family: normalize the identifier, reject the exact
reserved value `root`, and do so before any database access. The local reference
construction preserves the empty-input, found-user, and missing-user paths.

## Why this is v1 rather than a v0 edit

The experiment's earlier observations pin the v0 schema and implementation by
hash. Rewriting those files would retroactively change the interface under
historical measurements. The extension therefore creates an additive catalog
version and leaves v0 byte-for-byte unchanged.

The expression grammar itself did not need to grow. Calls, strings, variables,
and typed conditionals already existed; only the closed catalog lacked equality.
Program IR v1 consequently references the frozen v0 expression grammar and
changes the program and catalog version headers. A small v1 execution layer adds
the new intrinsic, while semantic patch v0 remains the edit protocol.

This is useful evidence about where the language boundary currently lies: the
guard was not blocked by JSON or tree structure. It was blocked by the semantic
instruction set shared by validation, interpretation, and lowering.

## Chronology and claim boundary

The heterogeneous candidate matrix was committed first at `16d29a5`. Its task
identity, required semantics, and `extension_required` disposition remain
unchanged. The extension was selected solely from that predeclared requirement,
before concrete task sealing or model calls.

The construction establishes that the extension is implementable and sufficient
for one reference guard. It does not establish that a model can generate the
patch, that semantic patches outperform source diffs, or that the candidate will
pass the future hidden benchmark. Those questions remain behind the final task
lock and model-execution gates.

Machine-readable evidence, including hashes and behavior checks, is in
[`construction/extensions/string-equals-001/observation.json`](construction/extensions/string-equals-001/observation.json).

## Next gate

Implement the second predeclared extension,
`directory.get_by_id: string -> option<user>` with the explicit
`network.read:directory` effect, using the same additive-version and chronology
discipline. Only then should the six concrete task instances and their hidden
evaluators be sealed.
