# Semantic-patch mode

The persistent program is supplied as semantic IR. Return one object conforming
to the semantic-patch v0 schema. Use only `replace_subtree`; every operation must
name the stable target node and carry the expected canonical subtree digest.
