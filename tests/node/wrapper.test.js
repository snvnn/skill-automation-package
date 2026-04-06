const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const WRAPPER_SOURCE = path.join(REPO_ROOT, "bin", "skill-automation-package.js");
const FIXTURE_PACKAGE_VERSION = "1.2.3";

function makeTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function createFixturePackage(t) {
  const root = makeTempDir("skill-wrapper-package-");
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));

  fs.mkdirSync(path.join(root, "bin"), { recursive: true });
  fs.mkdirSync(path.join(root, "scripts"), { recursive: true });
  fs.copyFileSync(WRAPPER_SOURCE, path.join(root, "bin", "skill-automation-package.js"));
  fs.chmodSync(path.join(root, "bin", "skill-automation-package.js"), 0o755);
  fs.writeFileSync(path.join(root, "scripts", "install.py"), "# fixture installer\n", "utf8");
  fs.writeFileSync(
    path.join(root, "package.json"),
    JSON.stringify({ name: "skill-automation-package", version: FIXTURE_PACKAGE_VERSION }) + "\n",
    "utf8",
  );

  return root;
}

function writeInstalledMetadata(targetRoot, version) {
  const metadataDir = path.join(targetRoot, ".claude");
  fs.mkdirSync(metadataDir, { recursive: true });
  fs.writeFileSync(
    path.join(metadataDir, "skill-automation-package.json"),
    JSON.stringify(
      {
        name: "skill-automation-package",
        version,
        installed_at: "2026-04-06T00:00:00+00:00",
        assets: [],
      },
      null,
      2,
    ) + "\n",
    "utf8",
  );
}

function writeMalformedMetadata(targetRoot, raw) {
  const metadataDir = path.join(targetRoot, ".claude");
  fs.mkdirSync(metadataDir, { recursive: true });
  fs.writeFileSync(path.join(metadataDir, "skill-automation-package.json"), raw, "utf8");
}

function writeLauncher(launcherDir, name) {
  const script = `#!/bin/sh
if [ "$1" = "-c" ]; then
  printf '%s\\n' "\${WRAPPER_TEST_PYTHON_VERSION:-3.12.0}"
  exit 0
fi
log_file="\${WRAPPER_TEST_LOG:?}"
{
  printf 'launcher=%s\\n' "\${0##*/}"
  index=1
  for arg in "$@"; do
    printf 'arg%s=%s\\n' "$index" "$arg"
    index=$((index + 1))
  done
} > "$log_file"
exit "\${WRAPPER_TEST_INSTALL_EXIT_CODE:-0}"
`;

  const launcherPath = path.join(launcherDir, name);
  fs.writeFileSync(launcherPath, script, "utf8");
  fs.chmodSync(launcherPath, 0o755);
}

function runWrapper({
  packageRoot,
  cwd,
  launcherDir,
  subcommand = "install",
  args,
  pythonVersion = "3.12.0",
  installExitCode = "0",
  logFile,
}) {
  return spawnSync(
    process.execPath,
    [path.join(packageRoot, "bin", "skill-automation-package.js"), subcommand, ...args],
    {
      cwd,
      encoding: "utf8",
      env: {
        ...process.env,
        PATH: launcherDir,
        WRAPPER_TEST_PYTHON_VERSION: pythonVersion,
        WRAPPER_TEST_INSTALL_EXIT_CODE: installExitCode,
        WRAPPER_TEST_LOG: logFile,
      },
    },
  );
}

function parseLog(logFile) {
  const raw = fs.readFileSync(logFile, "utf8").trim().split("\n");
  return Object.fromEntries(
    raw.map((line) => {
      const index = line.indexOf("=");
      return [line.slice(0, index), line.slice(index + 1)];
    }),
  );
}

test("uses python3 when available and forwards installer args from any cwd", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const outsideCwd = makeTempDir("skill-wrapper-cwd-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "python3.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(outsideCwd, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");
  writeLauncher(launcherDir, "python");

  const target = path.join(outsideCwd, "target-repo");
  const result = runWrapper({
    packageRoot,
    cwd: outsideCwd,
    launcherDir,
    args: ["--target", target, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(
    result.stdout,
    new RegExp(`target is not installed yet; proceeding with install of version ${FIXTURE_PACKAGE_VERSION}`),
  );
  const invocation = parseLog(logFile);
  assert.equal(invocation.launcher, "python3");
  assert.equal(
    fs.realpathSync(invocation.arg1),
    fs.realpathSync(path.join(packageRoot, "scripts", "install.py")),
  );
  assert.equal(invocation.arg2, "--target");
  assert.equal(invocation.arg3, target);
  assert.equal(invocation.arg4, "--dry-run");
});

test("accepts --target=<path> form and forwards it unchanged", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "target-equals.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: [`--target=${targetRoot}`, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  const invocation = parseLog(logFile);
  assert.equal(invocation.arg2, `--target=${targetRoot}`);
  assert.equal(invocation.arg3, "--dry-run");
});

test("treats an existing repo without install metadata as not installed", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "no-metadata.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /target is not installed yet; proceeding with install/);
});

test("falls back to python when python3 is unavailable", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "python.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", path.join(packageRoot, "target"), "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  const invocation = parseLog(logFile);
  assert.equal(invocation.launcher, "python");
});

test("fails clearly when no supported Python launcher is available", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-empty-launchers-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "missing.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", path.join(packageRoot, "target"), "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Python 3\.10\+ is required/);
  assert.match(result.stderr, /No supported Python launcher was found on PATH/);
});

test("returns a clear error when only unsupported Python versions are found", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "old-python.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");
  writeLauncher(launcherDir, "python");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", path.join(packageRoot, "target"), "--dry-run"],
    pythonVersion: "3.9.18",
    logFile,
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /Found python3 \(3\.9\.18\), but it is too old/);
  assert.match(result.stderr, /Found python \(3\.9\.18\), but it is too old/);
});

test("propagates the installer exit code", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "exit-code.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", path.join(packageRoot, "target"), "--dry-run"],
    installExitCode: "7",
    logFile,
  });

  assert.equal(result.status, 7);
});

test("warns when the target is already at the current version", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "same-version.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");
  writeInstalledMetadata(targetRoot, FIXTURE_PACKAGE_VERSION);

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, new RegExp(`already at version ${FIXTURE_PACKAGE_VERSION}`));
  assert.match(result.stdout, /packaged files will be overwritten/);
  assert.match(
    result.stdout,
    /repo-local skills, usage tracking, and archived skills will be preserved/,
  );
});

test("install proceeds with a warning when existing metadata is malformed", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "install-malformed.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");
  writeMalformedMetadata(targetRoot, "{not-json");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /existing install metadata .* could not be parsed as JSON/);
  const invocation = parseLog(logFile);
  assert.equal(invocation.launcher, "python3");
});

test("update fails when the target is not installed", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-empty-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "update-not-installed.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    subcommand: "update",
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /target is not installed; use install instead/);
  assert.equal(fs.existsSync(logFile), false);
});

test("update is a no-op when the target is already current", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-empty-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "update-noop.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeInstalledMetadata(targetRoot, FIXTURE_PACKAGE_VERSION);

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    subcommand: "update",
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, new RegExp(`already up to date \\(${FIXTURE_PACKAGE_VERSION}\\)`));
  assert.equal(fs.existsSync(logFile), false);
});

test("update reinstalls when the target is on an older version", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "update-reinstall.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");
  writeInstalledMetadata(targetRoot, "1.1.0");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    subcommand: "update",
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, new RegExp(`updating 1.1.0 -> ${FIXTURE_PACKAGE_VERSION}`));
  assert.match(result.stdout, /packaged files will be overwritten/);
  assert.match(
    result.stdout,
    /repo-local skills, usage tracking, and archived skills will be preserved/,
  );
  const invocation = parseLog(logFile);
  assert.equal(invocation.launcher, "python3");
});

test("update blocks downgrade attempts", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-empty-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "update-downgrade.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeInstalledMetadata(targetRoot, "1.3.0");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    subcommand: "update",
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /newer than this package version/);
  assert.match(result.stderr, /update is blocked to avoid an implicit downgrade/);
  assert.equal(fs.existsSync(logFile), false);
});

test("update blocks when existing metadata is malformed", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-empty-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "update-malformed.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeMalformedMetadata(targetRoot, "{not-json");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    subcommand: "update",
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 1);
  assert.match(result.stderr, /existing install metadata .* could not be parsed as JSON/);
  assert.match(result.stderr, /use install to force a reinstall/);
  assert.equal(fs.existsSync(logFile), false);
});

test("reports when a lower installed version can be updated", (t) => {
  const packageRoot = createFixturePackage(t);
  const launcherDir = makeTempDir("skill-wrapper-launchers-");
  const targetRoot = makeTempDir("skill-wrapper-target-");
  const logFile = path.join(makeTempDir("skill-wrapper-log-"), "update-available.log");

  t.after(() => fs.rmSync(launcherDir, { recursive: true, force: true }));
  t.after(() => fs.rmSync(targetRoot, { recursive: true, force: true }));
  t.after(() => fs.rmSync(path.dirname(logFile), { recursive: true, force: true }));

  writeLauncher(launcherDir, "python3");
  writeInstalledMetadata(targetRoot, "1.1.0");

  const result = runWrapper({
    packageRoot,
    cwd: packageRoot,
    launcherDir,
    args: ["--target", targetRoot, "--dry-run"],
    logFile,
  });

  assert.equal(result.status, 0, result.stderr);
  assert.match(
    result.stdout,
    new RegExp(`update available: 1.1.0 -> ${FIXTURE_PACKAGE_VERSION}`),
  );
  assert.match(result.stdout, /packaged files will be overwritten/);
  assert.match(
    result.stdout,
    /repo-local skills, usage tracking, and archived skills will be preserved/,
  );
});
