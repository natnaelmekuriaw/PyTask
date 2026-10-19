# Runtime dependency constraints

`runtime.txt` pins the installed application dependency set used for the
Linux Python 3.12 image. It includes transitive runtime dependencies and the
psycopg binary extra. CI uses the same constraints for application checks.

To update, resolve the project's declared runtime requirements in a clean
Python 3.12 environment, review dependency changes, and run the full suite
and Docker build. Keep development-only dependencies outside this list.
Do not edit pins independently of the requirements that constrain them.

The base image tag and build backend can still change. These constraints
do not claim bit-for-bit reproducibility. For a release, record the built
image digest and use that exact image for all roles and rollback decisions.
