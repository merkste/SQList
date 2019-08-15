{ nixpkgsSrc ? <nixpkgs>, sqlistSrc ? { outPath = ./.; }}:

let
  pkgs = import nixpkgsSrc {};
in pkgs.callPackage ./default.nix { inherit sqlistSrc; }
