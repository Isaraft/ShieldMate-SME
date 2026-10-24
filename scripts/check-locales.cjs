const fs = require("node:fs"),
  path = require("node:path"),
  ts = require("../frontend/node_modules/typescript");
const catalog = JSON.parse(
  fs.readFileSync(
    path.join(__dirname, "../backend/app/locales/ru.json"),
    "utf8",
  ),
);
const missing = new Set();
let checked = 0;
function message(value) {
  const key = value.replace(/\s+/g, " ").trim();
  if (!key || !/[A-Za-z]/.test(key)) return;
  checked++;
  if (!catalog[key]) missing.add(key);
}
function literals(n) {
  if (ts.isStringLiteral(n)) message(n.text);
  else if (ts.isConditionalExpression(n)) {
    literals(n.whenTrue);
    literals(n.whenFalse);
  }
}
function scan(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const f = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name !== "i18n") scan(f);
      continue;
    }
    if (!f.endsWith(".tsx")) continue;
    const s = fs.readFileSync(f, "utf8"),
      a = ts.createSourceFile(
        f,
        s,
        ts.ScriptTarget.Latest,
        true,
        ts.ScriptKind.TSX,
      );
    function walk(n) {
      if (
        ts.isCallExpression(n) &&
        n.expression.getText(a) === "tr" &&
        n.arguments[0]
      )
        literals(n.arguments[0]);
      if (ts.isJsxSelfClosingElement(n) && n.tagName.getText(a) === "T") {
        const item = n.attributes.properties.find(
          (p) => p.name?.getText(a) === "text",
        );
        if (item?.initializer?.expression)
          literals(item.initializer.expression);
      }
      ts.forEachChild(n, walk);
    }
    walk(a);
  }
}
scan(path.join(__dirname, "../frontend/src"));
if (missing.size) {
  console.error("Missing Russian catalog keys:\n" + [...missing].join("\n"));
  process.exitCode = 1;
} else
  console.log(
    `Localization coverage: ${checked} explicit static references, no missing keys.`,
  );
