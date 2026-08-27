# Semantic patch mode

Inspect the base program, closed catalog, program schema, expression grammar,
and semantic patch schema. Submit one checked semantic patch using only
`replace_subtree`. The orchestrator applies it transactionally and derives any
redundant canonical metadata before lowering.
