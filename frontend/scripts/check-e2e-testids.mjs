import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
);
const e2ePath = path.join(frontendRoot, "e2e", "demo-flow.spec.ts");
const sourceRoots = ["app", "components", "hooks", "lib", "types"].map(
  (directory) => path.join(frontendRoot, directory),
);

function sourceFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return sourceFiles(entryPath);
    return /\.(ts|tsx)$/.test(entry.name) && !/\.(test|spec)\./.test(entry.name)
      ? [entryPath]
      : [];
  });
}

function escapePattern(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function templatePatterns(source) {
  return [...source.matchAll(/data-testid=\{`([^`]+)`\}/g)].map((match) => {
    const parts = match[1].split(/\$\{[^}]+\}/g).map(escapePattern);
    return new RegExp(`^${parts.join("(.+)")}$`);
  });
}

function matchesTemplate(testId, pattern, source) {
  const match = pattern.exec(testId);
  return (
    match !== null && match.slice(1).every((value) => source.includes(value))
  );
}

function e2eTestIds(source) {
  const calls = [...source.matchAll(/getByTestId\(\s*([^\n)]+)\)/g)];
  const ids = calls.map((match) => {
    const argument = match[1].trim();
    const literal = argument.match(/^(["'])([^"']+)\1$/);
    if (!literal) {
      throw new Error(`getByTestId must use a string literal: ${argument}`);
    }
    return literal[2];
  });
  return [...new Set(ids)].sort();
}

const e2eSource = readFileSync(e2ePath, "utf8");
const applicationSource = sourceRoots
  .flatMap(sourceFiles)
  .map((file) => readFileSync(file, "utf8"))
  .join("\n");
const patterns = templatePatterns(applicationSource);
const missing = e2eTestIds(e2eSource).filter(
  (testId) =>
    !applicationSource.includes(testId) &&
    !patterns.some((pattern) =>
      matchesTemplate(testId, pattern, applicationSource),
    ),
);

if (missing.length > 0) {
  process.stderr.write(
    `E2E test IDs missing from application source:\n${missing.map((id) => `- ${id}`).join("\n")}\n`,
  );
  process.exitCode = 1;
} else {
  process.stdout.write(
    "All demo-flow getByTestId selectors exist in application source.\n",
  );
}
