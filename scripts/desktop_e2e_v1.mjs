#!/usr/bin/env node

import process from 'node:process'
import { writeFile } from 'node:fs/promises'

const args = new Map()
for (let index = 2; index < process.argv.length; index += 1) {
  const key = process.argv[index]
  if (!key.startsWith('--')) continue
  const value = process.argv[index + 1]
  args.set(key.slice(2), value && !value.startsWith('--') ? value : true)
  if (value && !value.startsWith('--')) index += 1
}

const port = Number(args.get('port'))
const workflowId = String(args.get('workflow-id') || '')
const timeoutMs = Number(args.get('timeout-ms') || 240000)
const reportPath = args.get('report-path') ? String(args.get('report-path')) : null
if (!Number.isInteger(port) || port < 1) throw new Error('--port is required')
if (!workflowId) throw new Error('--workflow-id is required')

let ws
let phase = 'initializing'

async function record(payload) {
  if (reportPath) await writeFile(reportPath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8')
}

async function main() {
const pages = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()
const page = Array.isArray(pages) && pages.find((entry) => entry.type === 'page' && entry.webSocketDebuggerUrl && (
  String(entry.url || '').startsWith('http://tauri.localhost/') || String(entry.title || '').includes('Codex Flow')
))
if (!page) throw new Error('Codex Flow WebView2 page target was not found')

let messageId = 1
const pending = new Map()
const websocketEvents = []
ws = new WebSocket(page.webSocketDebuggerUrl)
await new Promise((resolve, reject) => {
  ws.addEventListener('open', resolve, { once: true })
  ws.addEventListener('error', reject, { once: true })
})
ws.addEventListener('message', (event) => {
  const message = JSON.parse(String(event.data))
  if (message.id && pending.has(message.id)) {
    pending.get(message.id)(message)
    pending.delete(message.id)
    return
  }
  if (message.method?.startsWith('Network.webSocket')) websocketEvents.push(message.method)
})

function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = messageId++
    const timeout = setTimeout(() => {
      pending.delete(id)
      reject(new Error(`CDP command timed out: ${method}`))
    }, 15000)
    pending.set(id, (message) => {
      clearTimeout(timeout)
      message.error ? reject(new Error(JSON.stringify(message.error))) : resolve(message.result || {})
    })
    ws.send(JSON.stringify({ id, method, params }))
  })
}

async function evaluate(expression) {
  const result = await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })
  if (result.exceptionDetails) throw new Error(`CDP evaluation failed: ${result.exceptionDetails.text || 'unknown exception'}`)
  return result.result?.value
}

const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds))

async function waitFor(label, expression, expected = (value) => Boolean(value), limit = timeoutMs) {
  const deadline = Date.now() + limit
  let last
  while (Date.now() < deadline) {
    last = await evaluate(expression)
    if (expected(last)) return last
    await sleep(250)
  }
  throw new Error(`Timed out waiting for ${label}; last=${JSON.stringify(last)}`)
}

async function clickText(text) {
  const clicked = await evaluate(`(() => {
    const value = ${JSON.stringify(text)}
    const elements = [...document.querySelectorAll('button,a,[role="button"]')]
    const element = elements.find((candidate) => (candidate.innerText || '').trim() === value)
      || elements.find((candidate) => (candidate.innerText || '').trim().includes(value))
    if (!element) return false
    element.click()
    return true
  })()`)
  if (!clicked) throw new Error(`UI control not found: ${text}`)
}

async function clickSelector(selector) {
  const clicked = await evaluate(`(() => {
    const element = document.querySelector(${JSON.stringify(selector)})
    if (!element) return false
    element.click()
    return true
  })()`)
  if (!clicked) throw new Error(`UI selector not found: ${selector}`)
}

async function setControl(selector, value) {
  const kind = await evaluate(`(() => {
    const element = document.querySelector(${JSON.stringify(selector)})
    if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement)) return false
    if (element instanceof HTMLSelectElement) {
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set
      setter?.call(element, ${JSON.stringify(value)})
      element.dispatchEvent(new Event('input', { bubbles: true }))
      element.dispatchEvent(new Event('change', { bubbles: true }))
      return 'select'
    }
    element.focus()
    return 'text'
  })()`)
  if (!kind) throw new Error(`Unable to set UI control: ${selector}`)
  if (kind === 'text') {
    await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 17, key: 'Control', code: 'ControlLeft' })
    await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 65, key: 'a', code: 'KeyA', modifiers: 2 })
    await call('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 65, key: 'a', code: 'KeyA', modifiers: 2 })
    await call('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 17, key: 'Control', code: 'ControlLeft' })
    await call('Input.insertText', { text: value })
    await sleep(120)
  }
  await evaluate(`document.querySelector(${JSON.stringify(selector)})?.blur(); true`)
  await sleep(120)
}

async function setControlAt(selector, index, value) {
  const focused = await evaluate(`(() => {
    const element = document.querySelectorAll(${JSON.stringify(selector)})[${index}]
    if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) return false
    element.focus()
    return true
  })()`)
  if (!focused) throw new Error(`Unable to set UI control ${selector} at index ${index}`)
  await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 17, key: 'Control', code: 'ControlLeft' })
  await call('Input.dispatchKeyEvent', { type: 'rawKeyDown', windowsVirtualKeyCode: 65, key: 'a', code: 'KeyA', modifiers: 2 })
  await call('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 65, key: 'a', code: 'KeyA', modifiers: 2 })
  await call('Input.dispatchKeyEvent', { type: 'keyUp', windowsVirtualKeyCode: 17, key: 'Control', code: 'ControlLeft' })
  await call('Input.insertText', { text: value })
  await sleep(120)
  await evaluate(`document.querySelectorAll(${JSON.stringify(selector)})[${index}]?.blur(); true`)
  await sleep(120)
}

async function selectTask(taskId) {
  await clickSelector(`[data-testid="rf__node-${taskId}"]`)
  await waitFor(`Task inspector for ${taskId}`, `document.querySelector('[aria-label="Task inspector"]')?.innerText?.includes(${JSON.stringify(taskId)})`)
}

async function configureTask(currentId, nextId, name, prompt) {
  await selectTask(currentId)
  await setControl('[aria-label="Task ID"]', nextId)
  await waitFor(`renamed task ${nextId}`, `Boolean(document.querySelector('[data-testid="rf__node-${nextId}"]'))`)
  await selectTask(nextId)
  await setControl('[aria-label="Task name"]', name)
  await setControl('[aria-label="Working directory"]', 'D:\\codex-flow-smoke')
  await setControl('[aria-label="Task prompt"]', prompt)
  await setControl('[aria-label="Sandbox"]', 'workspace_write')
}

async function dragConnection(sourceId, targetId) {
  const points = await evaluate(`(() => {
    const source = document.querySelector('[data-testid="rf__node-${sourceId}"] .react-flow__handle.source')
    const target = document.querySelector('[data-testid="rf__node-${targetId}"] .react-flow__handle.target')
    if (!source || !target) return null
    const from = source.getBoundingClientRect()
    const to = target.getBoundingClientRect()
    return { from: { x: from.left + from.width / 2, y: from.top + from.height / 2 }, to: { x: to.left + to.width / 2, y: to.top + to.height / 2 } }
  })()`)
  if (!points) throw new Error(`Graph connection handles unavailable: ${sourceId} -> ${targetId}`)
  await call('Input.dispatchMouseEvent', { type: 'mousePressed', x: points.from.x, y: points.from.y, button: 'left', clickCount: 1 })
  await call('Input.dispatchMouseEvent', { type: 'mouseMoved', x: (points.from.x + points.to.x) / 2, y: (points.from.y + points.to.y) / 2, buttons: 1 })
  await call('Input.dispatchMouseEvent', { type: 'mouseMoved', x: points.to.x, y: points.to.y, buttons: 1 })
  await call('Input.dispatchMouseEvent', { type: 'mouseReleased', x: points.to.x, y: points.to.y, button: 'left', clickCount: 1 })
  await sleep(300)
}

await call('Runtime.enable')
await call('Network.enable')
const initial = await waitFor('installed UI root', '({ title: document.title, root: Boolean(document.querySelector("#root")), url: location.href })', (value) => value?.root && value.title === 'Codex Flow', 30000)

phase = 'workflow-create'
await evaluate(`location.assign('http://tauri.localhost/'); true`)
await waitFor('workflow list navigation', 'Boolean([...document.querySelectorAll("button,a,[role=button]")].find((element) => (element.innerText || "").trim() === "New workflow"))', Boolean, 15000)
await clickText('New workflow')
await waitFor('new workflow form', 'Boolean(document.querySelector(".new-workflow-form"))', Boolean, 10000)
await setControlAt('.new-workflow-form input', 0, workflowId)
await setControlAt('.new-workflow-form input', 1, `Desktop E2E ${workflowId}`)
await setControl('.new-workflow-form textarea', 'Installed Tauri WebView2 regression workflow.')
await clickText('Create workflow')
await waitFor('workflow editor', `location.pathname.includes(${JSON.stringify(`/workflows/${encodeURIComponent(workflowId)}`)})`, Boolean, 15000)

await clickText('Add task')
await clickText('Add task')
await clickText('Add task')
await waitFor('three editor nodes', 'document.querySelectorAll(".workflow-canvas .react-flow__node").length', (count) => count === 3, 10000)

await configureTask('new-task-1', 'A', 'Create A', 'Create task_a.txt in the current working directory with exactly TASK_A_DONE, then finish successfully.')
await configureTask('new-task-2', 'B', 'Verify B', 'Read task_a.txt and verify it contains TASK_A_DONE. Create task_b.txt with exactly TASK_B_DONE, then finish successfully.')
await configureTask('new-task-3', 'C', 'Verify C', 'Read task_a.txt and task_b.txt and verify their markers. Create task_c.txt with exactly TASK_C_DONE, then finish successfully.')

await dragConnection('A', 'B')
await dragConnection('B', 'C')
await waitFor('two dependency edges', 'document.querySelectorAll(".workflow-canvas .react-flow__edge").length', (count) => count === 2, 10000)
await clickText('Save workflow')
await waitFor('saved editor', 'Boolean([...document.querySelectorAll("button")].find((button) => button.innerText.trim() === "Start run" && !button.disabled))', Boolean, 15000)

const duplicateStart = await evaluate(`(() => {
  const button = [...document.querySelectorAll('button')].find((candidate) => candidate.innerText.trim() === 'Start run')
  if (!button || button.disabled) return false
  button.click()
  button.click()
  return true
})()`)
if (!duplicateStart) throw new Error('Start run button was unavailable')

phase = 'run-execution'
const runPath = await waitFor('run detail navigation', 'location.pathname', (value) => typeof value === 'string' && value.startsWith('/runs/'), 15000)
const runId = decodeURIComponent(runPath.split('/').at(-1))
await waitFor('pause control', 'Boolean(document.querySelector("[data-testid=run-control-pause]"))', Boolean, 10000)
await clickSelector('[data-testid="run-control-pause"]')
await waitFor('resume control', 'Boolean(document.querySelector("[data-testid=run-control-resume]"))', Boolean, 10000)
await clickSelector('[data-testid="run-control-resume"]')

const statusHistory = []
const deadline = Date.now() + timeoutMs
let terminalText = ''
while (Date.now() < deadline) {
  const state = await evaluate(`({ status: document.querySelector('[data-testid="run-status"]')?.textContent?.trim() || '', text: document.body?.innerText || '' })`)
  if (state.status && statusHistory.at(-1) !== state.status) statusHistory.push(state.status)
  terminalText = state.text
  if (state.status === 'SUCCESS') break
  if (['FAILED', 'CANCELLED', 'INTERRUPTED', 'NEEDS_ATTENTION'].includes(state.status)) throw new Error(`A→B→C run terminal failure: ${state.status}`)
  await sleep(500)
}
if (!terminalText.includes('Run result: SUCCESS')) throw new Error('A→B→C run did not reach SUCCESS in the installed UI')

await clickText('View details')
await waitFor('task detail drawer from list', '({ open: Boolean(document.querySelector("[data-testid=task-run-drawer]")), text: document.querySelector("[data-testid=task-run-drawer]")?.innerText || "" })', (value) => value?.open && value.text.includes('Thread ID') && value.text.includes('Turn ID') && value.text.includes('Attempts'), 15000)
await clickSelector('[aria-label="Close task details"]')
await clickSelector('[data-testid="rf__node-A"]')
await waitFor('task detail drawer from graph', 'Boolean(document.querySelector("[data-testid=task-run-drawer]"))', Boolean, 10000)
await clickSelector('[aria-label="Close task details"]')

await evaluate('location.reload(); true')
phase = 'historical-events'
await waitFor('historical event log after reload', 'document.body?.innerText?.includes("TURN_STARTED") && document.body?.innerText?.includes("TOOL_COMPLETED")', Boolean, 30000)

const finalUi = await evaluate(`({
  title: document.title,
  url: location.href,
  status: document.querySelector('[data-testid="run-status"]')?.textContent?.trim() || '',
  taskRows: [...document.querySelectorAll('.run-detail__tasks li')].map((row) => row.innerText),
  eventLog: document.body?.innerText?.includes('TURN_STARTED') && document.body?.innerText?.includes('TOOL_COMPLETED'),
})`)

const report = {
  installedStartup: initial,
  workflowId,
  runId,
  graphEdges: 2,
  pauseResume: true,
  statusHistory,
  runDetailFromList: true,
  runDetailFromGraph: true,
  historicalEvents: true,
  websocketObserved: websocketEvents.length > 0,
  finalUi,
}
await record({ result: 'PASS', phase: 'complete', ...report })
console.log(JSON.stringify(report))
}

try {
  await main()
} catch (error) {
  await record({ result: 'FAIL', phase, error: error instanceof Error ? error.message : String(error) })
  console.error(error instanceof Error ? error.stack : String(error))
  process.exitCode = 1
} finally {
  ws?.close()
}
