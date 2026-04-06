#!/usr/bin/env node

"use strict";

const { spawn, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const MIN_PYTHON = { major: 3, minor: 10 };
const INSTALL_METADATA_PATH = path.join(".claude", "skill-automation-package.json");

function main() {
  const [, , subcommand, ...forwardedArgs] = process.argv;

  if (subcommand !== "install" && subcommand !== "update") {
    printUsage(subcommand);
    process.exitCode = 1;
    return;
  }

  const packageRoot = path.resolve(__dirname, "..");
  const installerPath = path.resolve(packageRoot, "scripts", "install.py");
  if (!fs.existsSync(installerPath)) {
    console.error(
      `skill-automation-package: expected installer at ${installerPath}, but it was not found.`,
    );
    console.error("Reinstall the package or run it from a complete package checkout.");
    process.exitCode = 1;
    return;
  }

  const packageInfo = readPackageInfo(packageRoot);
  if (!packageInfo.ok) {
    console.error(packageInfo.message);
    process.exitCode = 1;
    return;
  }

  const targetRoot = resolveTargetRoot(forwardedArgs);
  if (subcommand === "update" && !targetRoot) {
    console.error("skill-automation-package: update requires --target <repo>.");
    printUsage();
    process.exitCode = 1;
    return;
  }

  const installState = targetRoot ? detectInstallState(targetRoot, packageInfo.version) : null;
  if (subcommand === "update") {
    const updateDecision = handleUpdateState(installState, packageInfo.version);
    if (updateDecision === "stop-success") {
      process.exitCode = 0;
      return;
    }
    if (updateDecision === "stop-failure") {
      process.exitCode = 1;
      return;
    }
  } else if (installState) {
    printInstallState(installState, packageInfo.version);
  }

  const python = findPython();
  if (!python.ok) {
    printPythonError(python);
    process.exitCode = 1;
    return;
  }

  const child = spawn(python.command, [...python.args, installerPath, ...forwardedArgs], {
    stdio: "inherit",
  });

  child.on("error", (error) => {
    console.error(`skill-automation-package: failed to launch ${python.display}.`);
    console.error(error.message);
    process.exitCode = 1;
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exitCode = code === null ? 1 : code;
  });
}

function readPackageInfo(packageRoot) {
  const packageJsonPath = path.join(packageRoot, "package.json");
  if (!fs.existsSync(packageJsonPath)) {
    return {
      ok: false,
      message: `skill-automation-package: expected package metadata at ${packageJsonPath}, but it was not found.`,
    };
  }

  try {
    const raw = fs.readFileSync(packageJsonPath, "utf8");
    const manifest = JSON.parse(raw);
    if (typeof manifest.version !== "string" || manifest.version.trim() === "") {
      return {
        ok: false,
        message: `skill-automation-package: package metadata at ${packageJsonPath} does not contain a valid version string.`,
      };
    }
    return { ok: true, version: manifest.version.trim() };
  } catch (error) {
    return {
      ok: false,
      message: `skill-automation-package: failed to read package metadata from ${packageJsonPath}: ${error.message}`,
    };
  }
}

function resolveTargetRoot(forwardedArgs) {
  let targetValue = null;

  for (let index = 0; index < forwardedArgs.length; index += 1) {
    const argument = forwardedArgs[index];

    if (argument === "--target" && index + 1 < forwardedArgs.length) {
      targetValue = forwardedArgs[index + 1];
      index += 1;
      continue;
    }

    if (argument.startsWith("--target=")) {
      targetValue = argument.slice("--target=".length);
    }
  }

  if (!targetValue) {
    return null;
  }

  return path.resolve(process.cwd(), targetValue);
}

function detectInstallState(targetRoot, currentVersion) {
  const metadataPath = path.join(targetRoot, INSTALL_METADATA_PATH);
  if (!fs.existsSync(metadataPath)) {
    return { status: "not-installed", targetRoot, metadataPath };
  }

  try {
    const raw = fs.readFileSync(metadataPath, "utf8");
    const metadata = JSON.parse(raw);
    if (typeof metadata.version !== "string" || metadata.version.trim() === "") {
      return { status: "unknown", targetRoot, metadataPath, reason: "missing-version" };
    }

    const installedVersion = metadata.version.trim();
    const installedParsed = parseVersion(installedVersion);
    const currentParsed = parseVersion(currentVersion);
    if (!installedParsed || !currentParsed) {
      return { status: "unknown", targetRoot, metadataPath, installedVersion, reason: "invalid-version" };
    }

    const comparison = compareVersions(installedParsed, currentParsed);
    if (comparison === 0) {
      return { status: "same-version", targetRoot, metadataPath, installedVersion };
    }
    if (comparison < 0) {
      return { status: "update-available", targetRoot, metadataPath, installedVersion };
    }
    return { status: "newer-installed", targetRoot, metadataPath, installedVersion };
  } catch (_error) {
    return { status: "unknown", targetRoot, metadataPath, reason: "invalid-json" };
  }
}

function compareVersions(left, right) {
  if (left.major !== right.major) {
    return left.major - right.major;
  }
  if (left.minor !== right.minor) {
    return left.minor - right.minor;
  }
  return left.patch - right.patch;
}

function printInstallState(state, currentVersion) {
  switch (state.status) {
    case "not-installed":
      console.log(
        `skill-automation-package: target is not installed yet; proceeding with install of version ${currentVersion}.`,
      );
      return;
    case "same-version":
      console.log(
        `skill-automation-package: target is already at version ${state.installedVersion}; reinstalling anyway.`,
      );
      printReinstallSafety();
      return;
    case "update-available":
      console.log(
        `skill-automation-package: update available: ${state.installedVersion} -> ${currentVersion}`,
      );
      printReinstallSafety();
      return;
    case "newer-installed":
      console.log(
        `skill-automation-package: target reports version ${state.installedVersion}, which is newer than this package version ${currentVersion}.`,
      );
      console.log(
        `skill-automation-package: reinstalling will replace packaged files with version ${currentVersion}.`,
      );
      printReinstallSafety();
      return;
    default:
      console.log(describeUnknownMetadata(state, "install", currentVersion));
      printLifecycleSafety();
  }
}

function handleUpdateState(state, currentVersion) {
  switch (state.status) {
    case "not-installed":
      console.error("skill-automation-package: target is not installed; use install instead.");
      return "stop-failure";
    case "same-version":
      console.log(`skill-automation-package: already up to date (${currentVersion}).`);
      return "stop-success";
    case "update-available":
      console.log(`skill-automation-package: updating ${state.installedVersion} -> ${currentVersion}`);
      printLifecycleSafety();
      return "proceed";
    case "newer-installed":
      console.error(
        `skill-automation-package: target reports version ${state.installedVersion}, which is newer than this package version ${currentVersion}.`,
      );
      console.error(
        "skill-automation-package: update is blocked to avoid an implicit downgrade.",
      );
      return "stop-failure";
    default:
      console.error(describeUnknownMetadata(state, "update", currentVersion));
      return "stop-failure";
  }
}

function printReinstallSafety() {
  printLifecycleSafety();
}

function printLifecycleSafety() {
  console.log("skill-automation-package: packaged files will be overwritten.");
  console.log(
    "skill-automation-package: repo-local skills, usage tracking, and archived skills will be preserved.",
  );
}

function describeUnknownMetadata(state, mode, currentVersion) {
  const metadataPath = state?.metadataPath || INSTALL_METADATA_PATH;
  const reasonLabel = {
    "invalid-json": "could not be parsed as JSON",
    "missing-version": "does not contain a usable version",
    "invalid-version": "contains a version that could not be compared",
  };
  const detail = reasonLabel[state?.reason] || "could not be compared";

  if (mode === "install") {
    return `skill-automation-package: existing install metadata at ${metadataPath} ${detail}; reinstalling with version ${currentVersion}.`;
  }

  return `skill-automation-package: existing install metadata at ${metadataPath} ${detail}; use install to force a reinstall.`;
}

function printUsage(subcommand) {
  if (subcommand) {
    console.error(`skill-automation-package: unsupported subcommand "${subcommand}".`);
  }
  console.error(
    "Usage: skill-automation-package <install|update> --target <repo> [installer options]",
  );
  console.error("`install` always reinstalls. `update` is version-aware and may no-op.");
}

function findPython() {
  const candidates = [
    { command: "python3", args: [], display: "python3" },
    { command: "python", args: [], display: "python" },
  ];

  if (process.platform === "win32") {
    candidates.push({ command: "py", args: ["-3"], display: "py -3" });
  }

  const unsuitable = [];

  for (const candidate of candidates) {
    const probe = probePython(candidate);
    if (probe.ok) {
      return probe;
    }
    if (probe.reason === "version") {
      unsuitable.push(probe);
    }
  }

  if (unsuitable.length > 0) {
    return { ok: false, reason: "version", unsuitable };
  }

  return { ok: false, reason: "missing", attempted: candidates.map((candidate) => candidate.display) };
}

function probePython(candidate) {
  const versionScript =
    "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]}')";
  const result = spawnSync(candidate.command, [...candidate.args, "-c", versionScript], {
    encoding: "utf8",
  });

  if (result.error) {
    return { ok: false, reason: "missing", display: candidate.display };
  }

  if (typeof result.status !== "number" || result.status !== 0) {
    return {
      ok: false,
      reason: "missing",
      display: candidate.display,
      stderr: (result.stderr || "").trim(),
    };
  }

  const version = parseVersion(result.stdout);
  if (!version) {
    return {
      ok: false,
      reason: "missing",
      display: candidate.display,
      stderr: "Could not parse Python version output.",
    };
  }

  if (!meetsMinimum(version, MIN_PYTHON)) {
    return {
      ok: false,
      reason: "version",
      command: candidate.command,
      args: candidate.args,
      display: candidate.display,
      version,
    };
  }

  return {
    ok: true,
    command: candidate.command,
    args: candidate.args,
    display: candidate.display,
    version,
  };
}

function parseVersion(output) {
  const trimmed = (output || "").trim();
  const match = /^(\d+)\.(\d+)\.(\d+)$/.exec(trimmed);
  if (!match) {
    return null;
  }
  return {
    major: Number(match[1]),
    minor: Number(match[2]),
    patch: Number(match[3]),
    raw: trimmed,
  };
}

function meetsMinimum(version, minimum) {
  if (version.major !== minimum.major) {
    return version.major > minimum.major;
  }
  return version.minor >= minimum.minor;
}

function printPythonError(result) {
  console.error(
    `skill-automation-package: Python ${MIN_PYTHON.major}.${MIN_PYTHON.minor}+ is required to run the installer.`,
  );

  if (result.reason === "version") {
    for (const candidate of result.unsuitable) {
      console.error(`- Found ${candidate.display} (${candidate.version.raw}), but it is too old.`);
    }
    console.error(
      "Install Python 3.10 or newer, or make a compatible `python3` or `python` available on PATH, then rerun the install command.",
    );
    return;
  }

  console.error(
    "No supported Python launcher was found on PATH. Looked for `python3`, `python`, and on Windows `py -3`.",
  );
  console.error(
    "Install Python 3.10 or newer, or update your PATH so one of those commands is available, then rerun the install command.",
  );
}

main();
