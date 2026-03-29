{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  packages = [
    pkgs.redis
    (pkgs.python312.withPackages (ps: with ps; [
      fastapi
      uvicorn
      pydantic
      passlib
      redis
      pytest
      httpx
      itsdangerous
      argon2_cffi
    ]))
  ];

  shellHook = ''
    export PYTHONPATH=.
    zsh
  '';
}
