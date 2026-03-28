# MAPP Worker

## Architectural Design

The idea is many of these workers can exist at the same time, all calling back
to the API.

Each worker has a series of machines it's tasked with watching, and it routinely
ssh's in to those and checks their status. Each worker will require a user's
credentials to be installed to allow it to authenticate with each machine it's
watching, and we should avoid storing these on disk in an unencrypted format.

Essentially the architecture looks like:

```
Worker 1 -------\
Worker 2 -------|
...             | ----> Website API ---> Website front-end
Worker n-1 -----|
Worker n -------/
```
