const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

const root = path.resolve(__dirname, "..");
const demoPath = "meusEstudos/enterpise-knowledge-ai/app/static/";
const read = (file) => fs.readFileSync(path.join(root, file), "utf8");
const response = (status, body) => ({ status, ok: status < 400, json: async () => body });
const active = (extra = {}) => ({
  filename: "manual.pdf", questions_remaining: 4, busy: false,
  expires_at: "2030-01-01T12:30:00Z", ...extra,
});

function element() {
  return {
    value: "", hidden: false, disabled: false, textContent: "", children: [],
    listeners: {}, attributes: {}, classList: { toggle() {} },
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, listener) { this.listeners[name] = listener; },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
    focus() {},
  };
}

async function loadDemo(replies) {
  const elements = new Map();
  for (const match of read(`${demoPath}index.html`).matchAll(/id="([^"]+)"/g)) {
    elements.set(`#${match[1]}`, element());
  }
  elements.set(".example-choice", element());
  const get = (selector) => {
    assert.ok(elements.has(selector), `Missing element: ${selector}`);
    return elements.get(selector);
  };
  const requests = [];
  const context = vm.createContext({
    document: { querySelector: get, createElement: element },
    fetch: async (url, options) => {
      requests.push({ url, method: options.method || "GET" });
      assert.ok(replies.length, `Unexpected request: ${url}`);
      const reply = replies.shift();
      if (reply instanceof Error) throw reply;
      return reply;
    },
  });
  vm.runInContext(read(`${demoPath}app.js`), context);
  await new Promise(setImmediate);
  return { get, requests };
}

test("a page opened during a question can refresh and resume without resending it", async () => {
  const { get, requests } = await loadDemo([
    response(200, active({ busy: true })), response(200, active()),
  ]);
  assert.equal(get("#question").disabled, true);
  assert.equal(get("#refresh-session").hidden, false);
  await get("#refresh-session").listeners.click();
  assert.equal(get("#question").disabled, false);
  assert.equal(get("#refresh-session").hidden, true);
  assert.equal(get("#quota-text").textContent, "1 de 5 tentativas");
  assert.deepEqual(requests.map((r) => r.method), ["GET", "GET"]);
});

test("a failed recovery preserves the document and can synchronize the remaining attempts", async () => {
  const { get, requests } = await loadDemo([
    response(200, active()), response(503, { detail: "demo_provider_unavailable" }),
    new Error("Offline"), response(200, active({ questions_remaining: 3 })),
  ]);
  get("#question").value = "Qual é o prazo?";
  get("#question").listeners.input();
  await get("#question-form").listeners.submit({ preventDefault() {} });
  assert.equal(get("#selected-file").hidden, false);
  assert.equal(get("#remove-file").disabled, false);
  assert.equal(get("#refresh-session").hidden, false);
  assert.equal(get("#question").disabled, true);
  assert.equal(get("#use-example").disabled, true);
  await get("#refresh-session").listeners.click();
  assert.equal(get("#question").disabled, false);
  assert.equal(get("#question").value, "Qual é o prazo?");
  assert.equal(get("#quota-text").textContent, "2 de 5 tentativas");
  assert.equal(get("#question-error").hidden, true);
  assert.deepEqual(requests.map((r) => r.method), ["GET", "POST", "GET", "GET"]);
});

test("an initial connection failure can recover before enabling a new upload", async () => {
  const { get } = await loadDemo([new Error("Offline"), response(401, {})]);
  assert.equal(get("#choose-file").disabled, true);
  assert.equal(get("#refresh-session").hidden, false);
  await get("#refresh-session").listeners.click();
  assert.equal(get("#choose-file").disabled, false);
  assert.equal(get("#refresh-session").hidden, true);
  assert.equal(get("#file-error").hidden, true);
});

for (const status of [401, 410]) {
  test(`a confirmed ${status} clears the session and its displayed history`, async () => {
    const { get } = await loadDemo([
      response(200, active({ busy: true })), response(status, {}),
    ]);
    get("#history").append(element());
    await get("#refresh-session").listeners.click();
    assert.equal(get("#selected-file").hidden, true);
    assert.equal(get("#history").children.length, 0);
    assert.equal(get("#choose-file").disabled, false);
  });
}

test("refreshing a replacement session clears the old document's answers", async () => {
  const { get } = await loadDemo([
    response(200, active({ busy: true })),
    response(200, active({ expires_at: "2030-01-01T12:40:00Z" })),
  ]);
  get("#history").append(element());
  await get("#refresh-session").listeners.click();
  assert.equal(get("#history").children.length, 0);
  assert.equal(get("#question").disabled, false);
});

test("an uncertain session can still be removed explicitly", async () => {
  const { get, requests } = await loadDemo([
    response(200, active()), response(503, {}), new Error("Offline"), response(204, null),
  ]);
  get("#question").value = "Prazo?";
  get("#question").listeners.input();
  await get("#question-form").listeners.submit({ preventDefault() {} });
  await get("#remove-file").listeners.click();
  assert.equal(get("#selected-file").hidden, true);
  assert.equal(get("#refresh-session").hidden, true);
  assert.equal(get("#choose-file").disabled, false);
  assert.equal(requests.at(-1).method, "DELETE");
});

for (const page of ["index.html", "projects.html", "artigos.html", "contrate-me.html", "cv.html"]) {
  test(`${page}: theme still works when storage reads and writes fail`, () => {
    const toggle = element();
    const rootElement = { dataset: {} };
    const meta = {};
    const context = vm.createContext({
      document: {
        documentElement: rootElement,
        querySelector: (selector) => selector === ".theme-toggle" ? toggle : meta,
      },
      localStorage: {
        getItem() { throw new Error("Storage blocked"); },
        setItem() { throw new Error("Storage full"); },
      },
    });
    const inline = read(page).match(/<script>\s*([\s\S]*?)<\/script>/)[1];
    vm.runInContext(inline, context);
    vm.runInContext(read("js/script.js"), context);
    assert.equal(rootElement.dataset.theme, "light");
    toggle.listeners.click();
    assert.equal(rootElement.dataset.theme, "dark");
    assert.equal(toggle.attributes["aria-pressed"], "true");
    assert.equal(meta.content, "#0d1117");
    toggle.listeners.click();
    assert.equal(rootElement.dataset.theme, "light");
  });
}
