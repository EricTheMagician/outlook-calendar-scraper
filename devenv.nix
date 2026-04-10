{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  dotenv.disableHint = true;
  # https://devenv.sh/basics/
  env = {
  };
  # https://devenv.sh/packages/
  packages = [
    pkgs.git
    pkgs.pyrefly
    pkgs.nixfmt
    pkgs.playwright
    pkgs.playwright-driver.browsers
  ];

  # https://devenv.sh/languages/
  languages.python =
    let
      ics-no-check = pkgs.python313Packages.ics.overridePythonAttrs (old: {
        doCheck = false;
        doInstallCheck = true;
      });
    in
    {
      enable = true;
      directory = "./src";
      package = (
        pkgs.python314.withPackages (ps: [
          ps.niquests
          ps.playwright
          ps.playwright-stealth
          ps.pytest
          ps.python-dateutil
          ps.types-python-dateutil
          (ps.ics.overridePythonAttrs (old: {
            doCheck = false;
            doInstallCheck = true;
          }))
        ])
      );
      lsp.package = pkgs.pyrefly;
      venv.enable = true;
    };

  # https://devenv.sh/processes/
  # processes.dev.exec = "${lib.getExe pkgs.watchexec} -n -- ls -la";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';

  # https://devenv.sh/basics/
  enterShell = ''
    export PLAYWRIGHT_BROWSERS_PATH="${pkgs.playwright-driver.browsers}"
    export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS="true"
    export DEVENV_PYTHON_INTERPRETER="${lib.getExe config.languages.python.package}"

    cat <<EOF > .env
    PLAYWRIGHT_BROWSERS_PATH="$PLAYWRIGHT_BROWSERS_PATH"
    PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS="$PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"
    DEVENV_PYTHON_INTERPRETER="$DEVENV_PYTHON_INTERPRETER"
    PATH=$PATH
    EOF
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  git-hooks = {
    enable = true;
    hooks = {
      shellcheck.enable = true;
      beautysh.enable = true;
      # format Python code
      black.enable = true;
      # Check for files that would conflict in case-insensitive filesystems.
      check-case-conflicts.enable = true;
      # Check for files that contain merge conflict strings.
      check-merge-conflicts.enable = true;
      # Check TOML files for syntax errors.
      check-toml.enable = true;
      # Check XML files for syntax errors.
      check-xml.enable = true;
      # Check YAML files for syntax errors.
      check-yaml.enable = true;
      # Remove UTF-8 byte order marker.
      fix-byte-order-marker.enable = true;
    };
  };

  # See full reference at https://devenv.sh/reference/options/
}
