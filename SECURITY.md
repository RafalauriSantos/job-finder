# Security policy

## Secrets

API keys, bot tokens, browser profiles, databases and runtime logs belong
outside the repository. Use environment variables or the local file
`~/.job-finder/secrets.env`. The example files contain placeholders only.

The local pre-commit hook performs a best-effort scan for common credential
formats. It is an additional safeguard, not a replacement for reviewing a
diff before publication.

## Reporting

Do not open a public issue containing a credential, private job history,
personal data or an authenticated browser export. Rotate an exposed secret
first, then report the affected file and the shortest reproducible description
through a private channel.

## Scope

The LinkedIn integration captures content already visible in the user's
authenticated browser. It does not attempt to bypass authentication,
challenges, rate limits or access controls.
