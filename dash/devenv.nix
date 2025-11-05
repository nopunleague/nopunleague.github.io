{ pkgs, lib, config, inputs, ... }:

  let 
    buildInputs = with pkgs; [
    stdenv.cc.cc 
    libuv 
    zlib
  ];
  in 
{
  env = {
    LD_LIBRARY_PATH = "${lib.makeLibraryPath buildInputs}";
  };

  languages.python = {
    enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
    
  };
scripts.runmain.exec = "uv run python espn_test.py";
}
