# Pure string equality extension

This construction adds one closed-catalog intrinsic to semantic IR without
changing the frozen v0 implementation or the identity of the candidate task
that required it.

`string.equals(string, string) -> boolean` is pure: it performs exact,
case-sensitive equality, declares no effect, requires no capability, and lowers
deterministically to TypeScript strict equality.

The reference patch inserts the requested reserved-identifier guard before the
existing database read. Local validation establishes construction support only.
The candidate matrix remains frozen, no concrete benchmark task is sealed here,
and no model call or efficacy claim is authorized.

See [`observation.json`](observation.json) for the machine-readable chronology,
digests, and behavior checks.
