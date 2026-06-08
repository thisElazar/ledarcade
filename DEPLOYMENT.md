# Deployment & Branch Workflow

How code goes from an idea to a customer's cabinet.

## The model in one picture

```
feature/x ──PR──▶ main ──(verify on dev cabinet)──▶ git tag v1.4 ──▶ fleet pulls v1.4
  your work    [CI: smoke +    always green,           the release       on next boot
               parity gate]    reviewed trunk          (deliberate)
```

- **`main`** is the trunk: always green, CI-gated, deployable in principle. All work lands here via pull requests. **Never commit directly to `main`.**
- **A release is a tag**, not a branch. When a commit on `main` is verified on the dev cabinet, tag it `vMAJOR.MINOR` (e.g. `v1.4`).
- **Distribution cabinets run the latest tag.** They never run `main`'s tip.
- **The dev cabinet runs `main`.** It is the test bed — the only place "works on real hardware" is ever checked.

There is no `stable` branch. The tag *is* the deploy pointer.

## Why a deliberate release gate (and not just "deploy main")

CI runs on an x86 Linux box with no LED matrix. It proves the code imports and
every visual/game constructs and animates without crashing. It **cannot** see
visual correctness, color/timing, or Raspberry Pi performance. Those only show
up on real hardware. The dev-cabinet check before tagging is that gate; the tag
is how the fleet is kept from running anything that hasn't passed it.

## Day-to-day: making a change

```bash
git checkout main && git pull
git checkout -b feature/my-change
# ... work, commit ...
git push -u origin feature/my-change
gh pr create --base main
# CI must go green, then merge the PR.
```

## Cutting a release

After the change is merged to `main` and verified on the dev cabinet:

```bash
git checkout main && git pull
git tag v1.4            # next version, vMAJOR.MINOR
git push origin v1.4
```

Distribution cabinets pick it up on their next boot (see `start.sh`). To force
an update, reboot the cabinet.

## How cabinets update (`start.sh`)

On boot, `start.sh` chooses its update mode by the gitignored `.dev` flag:

- **Dev cabinet** (`.dev` present): `git pull --ff-only` — latest `main`.
- **Distribution cabinet** (no `.dev`): fetch tags, check out the highest `v*` tag.

A fresh distribution cabinet is set up by `provision.sh`, which clones the repo
and checks out the latest tag.

## Rollback

A distribution cabinet sits on whatever the highest `v*` tag is. To roll a bad
release back, either delete the bad tag and let cabinets fall back to the prior
one, or check out the previous tag on the affected cabinet:

```bash
git checkout v1.3      # on the cabinet, then restart the service
```

## Reading the deployed version off a cabinet

The **SYSTEM INFO** panel shows:

- `PY:`  the Python version the cabinet is running.
- `VER:` the release tag (e.g. `v1.4`) — or, on the dev cabinet, the nearest tag
  plus commit offset.

This lets you confirm exactly what code and runtime any cabinet is on without
plugging in a keyboard.
