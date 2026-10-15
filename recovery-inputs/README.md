# TownSquare workspace recovery inputs (unreviewed)

This branch preserves the TownSquare Workspace dirty snapshot from 2026-10-15 on top of feature commit aa2aeb5. The five-file dirty diff and the 48 previously untracked project files are represented directly in the working tree. `SHA256SUMS.txt` records the pre-commit bytes for those files and the additional preserved inputs.

The additional VR008 dirty input is preserved as a patch under `recovery-inputs/VR008/`, with its untracked test. Its patch is based on the coordinator-route source state and does not apply cleanly as a whole to this snapshot because it overlaps registry schema and session-registry changes. The patch and its untracked test are retained for later compatible integration; they have not been applied here.

This recovery branch is unreviewed and untested. It is a preservation point only, not a merge-ready or deployment-ready candidate.
