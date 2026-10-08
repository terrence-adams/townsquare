# VR-20261008-townsquare-181 integration validation — 2026-10-08

**reviewed branch head:** `125303e`  
**merge commit:** `5e57bf6`  
**integration correction:** `09ef912`  
**target branch:** `townsquare-mvp`  
**lifecycle effect:** none — Story remains `WORKING`; no deployment or operator acceptance is claimed

The independently reviewed Cable reader was merged without squashing so the original Opus expansion, the Sonnet compact rework, and both forward corrections remain visible in Git history.

The first Windows integration run produced one failure while all 22 Vertical tracker tests passed. `test_state_and_inbox_written_atomically_with_private_mode` expected POSIX mode `0600`, but Windows reports emulated mode bits as `0666`. This did not contradict the measured Cable result: the same test passed on Cable/Linux with mode `0600`. Commit `09ef912` retains the atomic-write and temporary-file assertions on every platform and applies the mode-bit assertion only on POSIX hosts.

Post-correction verification:

- `python -W error::ResourceWarning -m unittest -v tests.test_host_reader` — 13 tests, `OK`, no warnings on Venom/Windows.
- `python -m unittest tests.test_vertical_poc_roadmap` — 22 tests, `OK`.
- Cable/Linux had already run the same 13 reader tests with resource warnings treated as errors — `OK`.
- Cable legacy poller and crontab hashes remained unchanged.
- `git diff --check` returned no error.

The code is integrated into `townsquare-mvp`. Installation, scheduling, automatic delivery, wake behavior, and operator acceptance are separate work and are not implied by this record.
