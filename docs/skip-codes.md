# Skip codes — `SkipCode`

Every value of `SkipCode` in `src/astart/rules/reasons.py` — why the
runner did not apply a selected fix. Each line gives the string value
and the sentence from the member's docstring.

- `subject-missing` — The subject could not be located in the final tree.
- `conflict` — Another fix already edited the same node.
- `preconditions-changed` — The fix's preconditions no longer held.
- `applier-failed` — The applier raised.
- `write-back` — The tree could not be written without reformatting.
- `checker-rejected` — The external type checker reported a new error.
