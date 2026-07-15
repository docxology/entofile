# Formal model {#sec:formal_model}

This section gives a compact formal account of the ENTO container so that the
benchmark results in [@sec:results] and [@sec:benchmark_interpretation] can be
read against precise definitions rather than prose. The model is deliberately
minimal: it fixes notation for the track envelope, states the ciphertext-expansion
law that the measurements verify exactly, and defines the integrity and
observability predicates that [@sec:security_verification] and
[@sec:proof_observability] exercise.

## Container as a typed track map

Fix a master key $K \in \{0,1\}^{8\kappa}$ with \(\kappa = {{MASTER_KEY_BYTES}}\) bytes. A
container $C$ over a finite track-id set $\mathcal{I}$ is a partial map from track
ids to typed, encrypted payloads,

$$
C : \mathcal{I} \rightharpoonup \mathcal{U} \times \mathcal{B},
$$ {#eq:container_map}

where $\mathcal{U}$ is the ontology-URI set (the *typed* axis of the format) and
$\mathcal{B} = \{0,1\}^{*}$ is the byte space of stored ciphertext. The *omnitrack*
property of [@eq:container_map] is that $|\mathcal{I}|$ is unbounded and the tracks
are heterogeneous: a single $C$ may bind ento:timeseries.eeg, ento:genomics.vcf,
and ento:spectrogram simultaneously ([@sec:ontology_fixtures]).

## Per-track key derivation and encryption

Each track is encrypted under its own key, derived from $K$ by HKDF-SHA256
[@krawczyk2010hkdf; @nistfips1804] with a track-binding info string,

$$
k_i = \mathrm{HKDF\text{-}SHA256}\bigl(K,\; \texttt{"ento:track:"} \,\|\, i\bigr), \qquad i \in \mathcal{I},
$$ {#eq:track_key}

so distinct tracks receive cryptographically independent keys and the track id is
bound into the derivation ([@eq:track_key]). Operationally, this means a
ciphertext for eeg is not merely a blob under the master key; it is checked
under the eeg subkey, so a cross-track swap fails before plaintext is released.
For a plaintext
$m_i \in \{0,1\}^{8n}$ of $n$ bytes, the stored member is the concatenation

$$
\mathrm{ENC}(k_i, m_i) = \nu_i \,\|\, \tau_i \,\|\, c_i,
$$ {#eq:track_member}

where $\nu_i$ is the {{NONCE_BYTES}}-byte AES-256-GCM nonce, \(\tau_i\) is the
{{TAG_BYTES}}-byte authentication tag, and $c_i$ is the ciphertext body
[@nistfips197; @rfc5116; @dworkin2007gcm; @mcgrew2004gcm]. Because GCM is a stream-based AEAD mode, it preserves the
length of the bytes supplied to encryption; for default format {{FORMAT_VERSION}},
those bytes are the original-length prefix plus payload padded to a PADMÉ bucket.

## Exported-manifest context binding

The stable default authenticates the format label and track identifier. The
opt-in profile {{FORMAT_VERSION_NEXT}} adds a canonical binding for the
manifest view that is actually exported. Let pi(M) remove
manifest_binding and each sha256_ciphertext field from manifest M,
while preserving root values and track order. Define

$$
B(M) = \operatorname{SHA256}\left(
\operatorname{JSON}_{\mathrm{UTF8,sorted,compact}}\left(\pi(M)\right)
\right).
$$ {#eq:manifest_binding}

Equation [@eq:manifest_binding] is implemented by compute_manifest_binding()
and excludes only the binding field and the post-encryption ciphertext digest
fields.

The ciphertext digest is excluded because encryption depends on B(M) and
would otherwise create a circular definition. The track associated data for
{{FORMAT_VERSION_NEXT}} is

$$
A_i = \texttt{"ento:"} \mathbin\Vert {{FORMAT_VERSION_NEXT}}
\mathbin\Vert \texttt{":manifest:"} \mathbin\Vert B(M)
\mathbin\Vert \texttt{":track:"} \mathbin\Vert i.
$$ {#eq:manifest_aad}

Equation [@eq:manifest_aad] is the exact track_aad() string passed to
AES-256-GCM for the {{FORMAT_VERSION_NEXT}} profile.

Because M is the exported view, changing observability, creator, timestamp,
track order, descriptor fields, or redaction changes B(M). A keyed reader
therefore rejects a rewritten context even if an attacker recomputes the
public binding and all unkeyed ciphertext digests. This proves only
keyed-context integrity; it does not prove origin, signature validity, custody,
streaming safety, or interoperability with another container ecosystem.

## The ciphertext-expansion law

Let H = {{TRACK_HEADER_BYTES}} be the fixed header size (nonce plus tag, from
[@eq:track_member]). Since tracks are stored uncompressed (ZIP_STORED) and
format {{FORMAT_VERSION}} pads the encrypted body to PADME(n+8)
bytes, the default per-track expansion ratio is exactly

$$
r(n) \;=\; \frac{H + \operatorname{PADME}(n+8)}{n}.
$$ {#eq:expansion_law}

[@eq:expansion_law] is an identity, not an empirical fit: it predicts a strictly
decreasing upper envelope in n that asymptotes toward 1 as n tends to infinity,
with overhead attributable to the authenticated header and PADMÉ bucket.
[@fig:expansion_law] overlays the measured fixture-track ratios on this curve;
the maximum absolute residual is reported in the figure title and is at
floating-point noise level, confirming the law holds for the implementation
rather than merely approximating it. The decomposition of header and padded body
parts is shown per track in [@fig:crypto_overhead].

## Integrity predicate

Verification reports an integrity level (see [@sec:security_verification]) that is
a function of what was actually checked. Writing key for master key supplied and
every track's GCM tag verified, and dig for every ciphertext digest present and
matched, the level is

$$
\mathrm{integrity}(C) =
\begin{cases}
\textsf{key-authenticated} & \text{if } \mathsf{key},\\
\textsf{digest-only} & \text{if } \neg\,\mathsf{key} \,\wedge\, \mathsf{dig},\\
\textsf{unverified} & \text{otherwise.}
\end{cases}
$$ {#eq:integrity_levels}

Only the key-authenticated branch of [@eq:integrity_levels] resists an
adversary who controls the container bytes: the unkeyed digests and proof chain
([@sec:proof_observability]) are recomputable by anyone, so digest-only
detects accidental corruption alone. This distinction is why the manuscript
reports keyless verification as a pipeline consistency check and tamper rejection
as a keyed AEAD result. The proof hash is over the implementation's exact emitted
manifest JSON bytes, not a general JCS serialization [@rfc8785]. The CLI fails
closed on unverified by default ([@sec:security_verification]).

## Observability redaction is monotone

Let mu_l(C) be the exported manifest at observability level
l in {0,...,{{CONFIG_OBSERVABILITY_LEVEL_MAX}}}, and |mu_l(C)| its byte size.
Redaction is subtractive on field content: lowering l only removes or shortens
field classes (digests, then resolution descriptors, then type URIs - the sealed
level replaces each type URI with the shorter sentinel ento:opaque), and does not
re-encrypt the payload for the stable and compatibility profiles. The opt-in
authenticated-context profile binds the selected view into AEAD context, so
changing the view requires repacking. Under the implementation's URI registry -
where every ontology URI is at least as long as that sentinel - the exported
manifest size is therefore observed to be monotone non-decreasing in the level,

$$
\ell_1 \le \ell_2 \;\Longrightarrow\; |\mu_{\ell_1}(C)| \le |\mu_{\ell_2}(C)|.
$$ {#eq:observability_monotone}

[@eq:observability_monotone] is a property of the current field schema rather
than a guarantee for arbitrary registries (a hypothetical type URI shorter than
the sentinel could invert the top step); it is what
[@fig:observability_manifest_size] and [@fig:manifest_multitrack] show across
the fixture tracks, and it is the basis for the confidentiality-versus-
auditability trade-off discussed in [@sec:benchmark_interpretation].
