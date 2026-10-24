// Catalog parity and named-template parity are independent of UI runtime fallback.
const fs = require("node:fs"),
  path = require("node:path"),
  ts = require("../frontend/node_modules/typescript");
const catalogs = Object.fromEntries(
  ["en", "ru", "kk"].map((locale) => [
    locale,
    JSON.parse(
      fs.readFileSync(
        path.join(__dirname, `../backend/app/locales/${locale}.json`),
        "utf8",
      ),
    ),
  ]),
);
const keys = Object.keys(catalogs.en),
  issues = new Set();
const fields = (value) =>
  [...value.matchAll(/\{([a-zA-Z_]+)\}/g)]
    .map((m) => m[1])
    .sort()
    .join(",");
for (const [locale, catalog] of Object.entries(catalogs)) {
  for (const key of keys) {
    if (typeof catalog[key] !== "string" || !catalog[key].trim())
      issues.add(`${locale}: missing ${key}`);
    else if (fields(catalog[key]) !== fields(catalogs.en[key]))
      issues.add(`${locale}: placeholder mismatch ${key}`);
  }
  for (const key of Object.keys(catalog))
    if (!(key in catalogs.en)) issues.add(`${locale}: unexpected ${key}`);
}
let checked = 0;
function message(value) {
  const key = value.replace(/\s+/g, " ").trim();
  if (!key || !/[A-Za-z]/.test(key)) return;
  checked++;
  if (!(key in catalogs.en)) issues.add("UI: " + key);
}
function literals(node) {
  if (ts.isStringLiteral(node)) message(node.text);
  else if (ts.isConditionalExpression(node)) {
    literals(node.whenTrue);
    literals(node.whenFalse);
  }
}
function scan(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const file = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== "i18n") scan(file);
      continue;
    }
    if (!/\.tsx?$/.test(file)) continue;
    const ast = ts.createSourceFile(
      file,
      fs.readFileSync(file, "utf8"),
      ts.ScriptTarget.Latest,
      true,
      file.endsWith("tsx") ? ts.ScriptKind.TSX : ts.ScriptKind.TS,
    );
    function walk(node) {
      if (
        ts.isCallExpression(node) &&
        ["tr", "format"].includes(node.expression.getText(ast)) &&
        node.arguments[0]
      )
        literals(node.arguments[0]);
      if (
        ts.isJsxSelfClosingElement(node) &&
        node.tagName.getText(ast) === "T"
      ) {
        const text = node.attributes.properties.find(
          (p) => p.name?.getText(ast) === "text",
        );
        if (text?.initializer) {
          const initializer = text.initializer;
          literals(
            ts.isJsxExpression(initializer)
              ? initializer.expression
              : initializer,
          );
        }
      }
      ts.forEachChild(node, walk);
    }
    walk(ast);
  }
}
scan(path.join(__dirname, "../frontend/src"));
if (issues.size) {
  console.error([...issues].join("\n"));
  process.exitCode = 1;
} else
  console.log(
    `Localization: ${keys.length} keys × 3 locales; ${checked} UI references; no missing keys or placeholder mismatches.`,
  );
