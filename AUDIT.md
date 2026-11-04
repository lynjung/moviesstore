# Audit — November 4, 2026

## Live observations before deployment

Read-only HTTP checks passed for home, about, catalog, search requests, cart,
login, signup, all four movie detail pages, four posters, CSS, logo and about
image. Protected order history redirected to the hosted login page.

`/movies/999999/` returned HTTP 500 with a Django debug traceback. The source fix
returns 404. Disable production debug and rotate the previously committed secret
when deploying (see README).

Browser automation was unavailable, so responsive appearance and interactive
browser behavior have not been visually verified. Authenticated changes were
tested locally with an isolated database rather than creating production users,
reviews or orders. This audit does not certify every possible input or workload.

## Source fixes and verification

- Return 404 for nonexistent movies; scope review edits/deletes to movie and owner.
- Validate review text and show form errors on edit.
- Require POST and CSRF protection for delete, report, logout, cart add/clear and purchase.
- Validate quantities 1–10, normalize cart keys, and remove stale cart entries.
- Commit order and items atomically; prevent repeated purchases from an empty cart.
- Correct order links and use saved purchase prices in history.
- Correct local login redirects and honor safe same-host return URLs.
- Escape custom form errors; handle missing posters; constrain images to screen width.
- Add environment-based production settings, pinned dependencies and GitHub Actions.
- Stop tracking the local SQLite database, bytecode and macOS metadata; preserve local files.

All 12 regression tests pass. Django's system check and migration drift check
pass. Production checks with debug disabled and a validation-only secret report
only optional HSTS subdomain/preload warnings W005/W021, intentionally left off.
No schema changes are required.

## Follow-up deployment

The GitHub source update is separate from the hosted app. Follow README's database
backup/restore procedure before the first pull, configure a private secret and
`DJANGO_DEBUG=False`, collect static assets and reload PythonAnywhere. Retest
sign-in, reviews, checkout and order history after deployment. Checkout records
orders only; there is no payment gateway or movie delivery implementation.
