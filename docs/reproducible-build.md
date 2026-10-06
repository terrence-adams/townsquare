# Offline reproducible build

Build inputs are a reviewed, hash-locked wheelhouse (`wheelhouse.lock.json`) and digest-pinned Python base
image archived with the release. Dockerfiles intentionally have no default base
tag and use `pip --no-index --find-links=/wheelhouse`; a build without that cached
wheelhouse fails rather than downloading current packages. Generate and retain an
SBOM (CycloneDX or SPDX) from that exact wheelhouse, then invoke
`tools/generate-release-artifacts.py` with the commit and immutable image digests.

The checked-in `sbom.cdx.json` is a release-input template, not a claim that the
placeholder images were built. Replace it together with release-manifest.json
only after an offline build, vulnerability scan, and independent review.
