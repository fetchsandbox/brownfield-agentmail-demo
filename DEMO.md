# AgentMail demo — dev brief

A guided 60–90s screencap showing an agent integrate AgentMail
end-to-end into this brownfield Next.js + FastAPI app, using the
FetchSandbox MCP server, without burning a real AgentMail API key.

---

## Setup (2 min)

```bash
cd ~/brownfield-agentmail-demo
# repo is already scaffolded. open in your AI IDE (Cursor or Claude Code).
```

The `.mcp.json` at the repo root is already configured for the
`fetchsandbox` MCP server. No AgentMail API key, no AgentMail account,
no signup. The first time the agent calls a `mcp__fetchsandbox__*`
tool, npx will fetch the server automatically.

---

## What this demo is supposed to prove

> An agent can integrate AgentMail end-to-end into a real Next.js +
> FastAPI codebase — provision a per-customer inbox, subscribe a
> scoped webhook, reconcile the scope — in one shot, without burning
> a real API key, with a shareable receipt URL anyone can replay.

That sentence is the whole story. Everything in the recording should
make it visible.

---

## The exact prompt to give the agent

Paste this verbatim into Cursor / Claude Code chat:

```
Read README.md. Then wire the three "What's NOT wired yet" items in
server/main.py using AgentMail via the fetchsandbox MCP server.

Run the curated workflows first to confirm the integration shape,
then mirror that shape into our codebase.
```

That's it. One prompt. Don't help the agent — the recording is more
compelling if it lands without intervention.

---

## What the agent will do (in this order)

| Step | Tool call | What you'll see on screen |
|---|---|---|
| 1 | Reads `README.md` | Lists the three documented gaps |
| 2 | Reads `server/main.py` | Sees the `AGENT TASK` block with the exact MCP commands to use |
| 3 | `mcp__fetchsandbox__list_specs` filter="agentmail" | Finds the bundled AgentMail spec |
| 4 | `mcp__fetchsandbox__list_workflows` | Returns the curated AgentMail workflows |
| 5 | `mcp__fetchsandbox__run_workflow` id=`inbox_create_and_subscribe_webhook` | 4 steps all green, `terminal_state=success`, returns a **receipt URL** |
| 6 | Writes 3 new handlers into `server/main.py` | Per-inbox provision, AgentMail webhook receiver, teardown |

The receipt URL is the credibility line. Pause on it for ~2s during
the recording.

---

## Recording guidelines

- **Length:** 60–90 seconds, single take, no audio (caption overlays
  only — easier to subtitle, easier to embed in X)
- **Frame:** IDE + Claude Code chat panel split-screen. Terminal panel
  optional but useful for showing the receipt URL
- **Beats to hit on camera:**
  1. README.md scrolling — show the "What's NOT wired yet" section
  2. The prompt going in
  3. The MCP tool calls appearing inline in the chat
  4. The receipt URL the workflow run returns — **pause on it ~2 seconds**
  5. The new handlers being written into `server/main.py`
- **Captions to overlay** (suggested):
  - "no AgentMail API key"
  - "no signup"
  - "fully verified end-to-end"
  - "shareable receipt URL"

---

## After the recording

The MCP run produces a public receipt URL — share that as proof.
Reference shape:

```
https://fetchsandbox.com/runs/<run_id>?flow=<flow_id>
```

This is the link to drop into the X post — it's the credibility line.

---

## Known sharp edges (warn the dev before they hit them)

- **`/send`, `/reply`, `/drafts/{id}/send`, `/domains/{id}/verify`
  sub-actions are not yet supported in the sandbox.** The curated
  workflows route around this (CRUD + GETs + DELETEs only). If the
  agent tries to add a "send the welcome email" step, the run will
  fail with 404. Tell the agent: **stick to provision + subscribe +
  reconcile**, not send.

- **The `web/` frontend is a stub.** The demo is entirely server-side.
  Don't waste recording time on the UI — the agent's work is all in
  `server/main.py`.

- **Spec slug is `agentmail`** — if the agent calls
  `mcp__fetchsandbox__import_spec` with a URL instead of using the
  bundled spec, it'll create a NEW spec id and lose the curated
  workflows. The bundled version is what surfaces the 2 (or more)
  curated brain-grade workflows. Tell the agent to call
  `list_specs filter="agentmail"` first and use the returned spec_id.

---

## What "good" looks like in the recording

- ≤ 90 seconds
- Zero manual code edits by the dev — everything written by the agent
- At least one MCP `run_workflow` call visible with green status
- The receipt URL visible on screen, ideally clicked open in a second
  browser tab to show the live run timeline
- Final state: `server/main.py` has the three new handlers, ready to
  ship

That's the whole demo. The repo + the prompt do the work; the dev
just records.
