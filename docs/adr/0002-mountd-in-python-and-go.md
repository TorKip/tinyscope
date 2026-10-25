# mountd is built twice: Python first, then Go

Each `mountd` feature is built in Python first and, once finished, again in Go. This is deliberate duplication for learning: Python gives the fastest start on the Pi (GPIO and IMU libraries), Go doubles as practice and gives a single binary. Both must pass the same behaviour tests (e.g. an LX200 conversation run against either), which keeps them honest and lets us compare them on the same hardware.

## Consequences

- The core must stay small and the tests language-neutral, or the second implementation becomes a chore.
- Which version is "the" release for others to build is open until both exist.
