# Post-Quantum Transition Note

ENTO uses AES-256-GCM for data encryption. No post-quantum change is currently
needed for the symmetric track encryption layer.

Potential post-quantum integration points are external to the current wire
format:

- ML-KEM for wrapping or transporting ENTO master keys.
- ML-DSA for signing release bundles, SBOMs, artifact manifests, or containers.
- Hybrid signatures during a migration period where classical and PQ signatures
  are both required by policy.

Do not relabel this as an implemented control until a release pipeline actually
emits and validates the relevant PQ artifacts.
