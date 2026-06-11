# Manifest Extension Policy

Future manifest fields should be explicit, schema-governed, and compatible with
strict readers.

## Rules

- Add fields through `data/ento_manifest_schema.json`, not ad hoc parsing.
- Keep `additionalProperties: false` unless an extension namespace is formally
  introduced.
- Do not rely on unauthenticated manifest fields for adversarial integrity.
- If a field affects decryption or interpretation, bind it through AAD in a new
  opt-in wire format.
- Document redaction behavior for each observability level before adding fields.

## Deferred Extension Namespace

A future `extensions` object may be introduced only with a schema for names,
value types, collision policy, and reader behavior when an extension is unknown.
