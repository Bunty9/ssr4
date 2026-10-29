# Security and safety policy

SSR4 connects to **230 VAC mains** and to your home network, so two kinds of problems are
handled privately:

1. **Electrical safety problems**: anything that could expose someone to mains voltage or start
   a fire. Examples: insufficient creepage or clearance, an isolation barrier that can be
   bridged, a protection that fails unsafe, a component used beyond its rating.
2. **Firmware and network security problems**: for example a way to switch outputs without the
   API key, bypass the over-temperature protections remotely, or take over OTA updates.

## How to report

Use GitHub's private reporting: open the **Security** tab of this repository and choose
**Report a vulnerability**. Please include the board revision or commit, what you found, how to
reproduce it and, for electrical issues, measurements or photos if you have them.

Please do not open a public issue for these until a fix or a clear warning is published.

## What to expect

- An acknowledgement within 7 days.
- For a confirmed safety problem: a warning at the top of the README and in the release notes
  as soon as it is confirmed, then a fix in the design.
- Credit in the changelog if you want it.

## Supported versions

Only the latest revision on the default branch is maintained. Boards built from older
revisions should be checked against the current README warnings.

## Scope notes

- The firmware uses ESPHome's encrypted native API and a password-protected OTA update. Default
  credentials are never shipped: `firmware/secrets.example.yaml` holds placeholders that must
  be replaced.
- The keys in `firmware/packages/sim_host.yaml` and `firmware/targets/host.yaml` are published
  **on purpose**: they belong to the PC simulation only and are never used on a real board.
