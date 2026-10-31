#!/usr/bin/env node

import process from "node:process";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 1) {
  const value = process.argv[i];
  if (value.startsWith("--")) {
    const next = process.argv[i + 1];
    args.set(value.slice(2), next && !next.startsWith("--") ? next : true);
    if (next && !next.startsWith("--")) i += 1;
  }
}

const port = Number(args.get("port"));
if (!Number.isInteger(port)) throw new Error("--port is required");

const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const targets = Array.isArray(list) ? list : [];
const target = targets.find((entry) => {
  const url = String(entry.url || "");
  const title = String(entry.title || "");
  return entry.type === "page" && (
    url.includes("codex") ||
    url.startsWith("http://tauri.localhost/") ||
    title.includes("Codex Flow") ||
    title.includes("Codex")
  );
});
if (!target?.webSocketDebuggerUrl) {
  throw new Error(`No Codex Flow WebView2 page target found; targets=${JSON.stringify(targets.map(({type, url, title}) => ({type, url, title})))}`);
}

let nextId = 1;
const pending = new Map();
const events = {console: [], network: [], websocket: []};
const ws = new WebSocket(target.webSocketDebuggerUrl);
const opened = new Promise((resolve, reject) => {
  ws.addEventListener("open", resolve, {once: true});
  ws.addEventListener("error", reject, {once: true});
});
await opened;
ws.addEventListener("message", (event) => {
  const message = JSON.parse(String(event.data));
  if (message.id && pending.has(message.id)) {
    pending.get(message.id)(message);
    pending.delete(message.id);
    return;
  }
  if (message.method === "Runtime.consoleAPICalled") events.console.push(message.params);
  if (message.method === "Network.requestWillBeSent" || message.method === "Network.responseReceived") events.network.push({method: message.method, params: message.params});
  if (message.method.startsWith("Network.webSocket")) events.websocket.push({method: message.method, params: message.params});
});

function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = nextId++;
    pending.set(id, (message) => message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result || {}));
    ws.send(JSON.stringify({id, method, params}));
  });
}

await call("Runtime.enable");
await call("Network.enable");
await call("Log.enable");
if (args.get("reload")) {
  await call("Runtime.evaluate", {expression: "location.reload(); true", returnByValue: true});
  await new Promise((resolve) => setTimeout(resolve, Number(args.get("wait-ms") || 1000)));
}
const evaluation = await call("Runtime.evaluate", {
  expression: `({url: location.href, title: document.title, readyState: document.readyState, root: Boolean(document.querySelector('#root')), text: document.body?.innerText?.slice(0, 4000) || '', buttons: [...document.querySelectorAll('button')].map((b) => ({text: b.innerText, aria: b.getAttribute('aria-label')}))})`,
  returnByValue: true,
  awaitPromise: true,
});

let clicked = false;
const selector = args.get("selector");
const text = args.get("text");
const customExpression = args.get("expression");
if (selector || text || customExpression) {
  const expression = customExpression
    ? String(customExpression)
    : selector
    ? `document.querySelector(${JSON.stringify(selector)})?.click(); true`
    : `([...document.querySelectorAll('button,a,[role="button"],[data-testid],[tabindex]')].find((el) => (el.innerText || '').trim().includes(${JSON.stringify(text)})))?.click(); true`;
  await call("Runtime.evaluate", {expression, returnByValue: true, awaitPromise: true});
  clicked = true;
  await new Promise((resolve) => setTimeout(resolve, Number(args.get("wait-ms") || 1000)));
}

const after = await call("Runtime.evaluate", {
  expression: `({url: location.href, title: document.title, readyState: document.readyState, root: Boolean(document.querySelector('#root')), text: document.body?.innerText?.slice(0, 4000) || ''})`,
  returnByValue: true,
  awaitPromise: true,
});
console.log(JSON.stringify({target: {url: target.url, title: target.title}, clicked, before: evaluation.result?.value, after: after.result?.value, console: events.console.slice(-50), network: events.network.slice(-100), websocket: events.websocket.slice(-100)}, null, 2));
ws.close();
