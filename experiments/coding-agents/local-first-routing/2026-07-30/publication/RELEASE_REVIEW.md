# Release-candidate review

Date: 2026-08-19

Scope: local experiment tree before external publication

## Automated triage completed

- High-risk credential-pattern scan: zero matches for AWS access keys, private
  key headers, bearer-token-shaped values, Telegram bot-token assignments,
  AWS secret assignments, and common `sk-` token forms.
- Personal-path scan: zero `/Users/...` paths. The retained `/home/...`
  references are paths inside experiment containers.
- Keychain references: limited to declared service/account metadata and
  container construction; no retrieved credential value was recorded.
- Filesystem links: zero symlinks in the experiment tree.
- Calibration repository license metadata: five `MIT` repositories and one
  `Apache-2.0` repository (`go-git`). All six are OSI-compatible according to
  the frozen screening metadata.
- Integrity lock: generated only after the publication documents were added.

The scans reported only filenames or matched category labels. No credential
value was printed during review.

## Human release gate still required

Pattern scans are not proof that arbitrary prose, patches, or event streams are
free of sensitive information. Before an external release, a human must review
the raw evidence and confirm:

1. repository attribution and license-notice obligations for redistributed
   patches and excerpts;
2. absence of personal data, credentials, or unredacted request content outside
   the automated patterns;
3. exclusion of generated workspaces, Git internals, caches, and any mutable
   third-party source tree not intended as a release asset;
4. agreement between the final archive contents and the release manifest.

Failure of this gate blocks publication but does not change or invalidate the
scientific calibration results.
