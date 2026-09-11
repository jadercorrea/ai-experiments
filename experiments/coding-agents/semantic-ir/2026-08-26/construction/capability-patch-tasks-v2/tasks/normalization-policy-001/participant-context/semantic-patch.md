# Semantic capability patch mode

Inspect the base program, closed catalog, program schema, expression grammar,
and semantic patch schema. Select the node IDs you intend to replace, then call
`semantic_state_inspect` once with those IDs. This read-only operation does not
consume a mutation attempt. Copy the returned `state_token` and each matching
`target_token` verbatim into one `replace_subtree` submission. The orchestrator
resolves those opaque preconditions and applies the patch transactionally.
