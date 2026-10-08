#!/usr/bin/env python3
"""Render faithful dark-theme canvas SVGs from live n8n workflow JSON exports.

Reads /tmp/wf0N.json (fetched from the live instance), draws every node at its
real canvas position with its real display name, node-type label and the real
wiring. Renders NOTHING from node parameters: no credentials, URLs, hostnames.
"""
import json
import html
import re
import os

BG = "#0c1210"
PANEL = "#0f1513"
ACCENT = "#5fd08a"   # triggers
WIRE = "#3a4653"
TEXT = "#e9f2ec"
MUTED = "#93a89a"

# category -> accent color
CAT_COLORS = {
    "trigger": "#5fd08a",
    "ai": "#e0b45c",
    "logic": "#7fb3d8",
    "data": "#8a9a93",
    " Comms": "#8a9a93",
    "other": "#5a6a62",
}

TYPE_LABEL_OVERRIDES = {
    "n8n-nodes-base.webhook": "Webhook",
    "n8n-nodes-base.cron": "Schedule Trigger",
    "n8n-nodes-base.manualTrigger": "Manual Trigger",
    "n8n-nodes-base.googleSheetsTrigger": "Sheets Trigger",
    "n8n-nodes-base.googleSheets": "Google Sheets",
    "n8n-nodes-base.googleDocs": "Google Docs",
    "n8n-nodes-base.gmail": "Gmail",
    "n8n-nodes-base.supabase": "Supabase",
    "n8n-nodes-base.httpRequest": "HTTP Request",
    "n8n-nodes-base.executeWorkflow": "Run Workflow",
    "n8n-nodes-base.respondToWebhook": "Webhook Reply",
    "n8n-nodes-base.code": "Code",
    "n8n-nodes-base.if": "IF",
    "n8n-nodes-base.switch": "Switch",
    "n8n-nodes-base.merge": "Merge",
    "n8n-nodes-base.splitInBatches": "Loop",
    "n8n-nodes-base.set": "Set",
    "n8n-nodes-base.filter": "Filter",
    "n8n-nodes-base.wait": "Wait",
    "n8n-nodes-base.trello": "Trello",
    "n8n-nodes-base.noOp": "No-op",
    "@n8n/n8n-nodes-langchain.lmChatGoogleGemini": "Gemini Chat Model",
    "@n8n/n8n-nodes-langchain.agent": "AI Agent",
    "@n8n/n8n-nodes-langchain.chainLlm": "LLM Chain",
}


def pretty_type(t):
    if t in TYPE_LABEL_OVERRIDES:
        return TYPE_LABEL_OVERRIDES[t]
    base = t.split(".")[-1]
    words = re.sub(r"(?<!^)(?=[A-Z])", " ", base)
    words = words.replace("Lm Chat", "Chat").replace("Ai ", "AI ")
    return words[:28]


def category(t):
    b = t.split(".")[-1].lower()
    if "trigger" in b or b in ("webhook", "cron"):
        return "trigger"
    if t.startswith("@n8n/n8n-nodes-langchain") or "gemini" in b or "agent" in b:
        return "ai"
    if b in ("if", "switch", "merge", "code", "filter", "splitinbatches",
             "set", "sort", "limit", "noop", "datetime", "wait"):
        return "logic"
    if b in ("supabase", "googlesheets", "googledocs", "gmail", "trello",
             "httprequest", "airtable"):
        return "data"
    return "other"


def wrap(name, width=20, lines=2):
    # hard-break words longer than the line width (e.g. Update_Call_Classification)
    words = []
    for w in name.split():
        while len(w) > width:
            words.append(w[:width])
            w = w[width:]
        words.append(w)
    out, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) <= width:
            cur = t
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    if len(out) > lines:
        out = out[: lines - 1] + [" ".join(out[lines - 1 :])]
        if len(out[-1]) > width:
            out[-1] = out[-1][: width - 1].rstrip() + "…"
    return [ln for ln in out if ln] or [name[:width]]


NODE_W, NODE_H = 170, 64
PAD = 46
HEADER_H = 64

TITLES = {
    "wf01": "WF01 — Call Intake",
    "wf02": "WF02 — Call Classification",
    "wf03": "WF03 — QA Evaluation",
    "wf04": "WF04 — Notifications and Actions",
    "wf05": "WF05 — Sales Intelligence",
    "wf06": "WF06 — CSR Performance",
    "wf07": "WF07 — Coaching",
    "wf08": "WF08 — Reporting",
}


def render(key, src, dst):
    d = json.load(open(src))
    nodes = d.get("nodes", [])
    conns = d.get("connections", {})
    by_name = {n["name"]: n for n in nodes}

    xs = [n["position"][0] for n in nodes]
    ys = [n["position"][1] for n in nodes]
    min_x, min_y = min(xs), min(ys)
    span_w = max(xs) - min_x + NODE_W
    span_h = max(ys) - min_y + NODE_H

    def px(n):
        return n["position"][0] - min_x + PAD

    def py(n):
        return n["position"][1] - min_y + PAD + HEADER_H

    node_max_y = max(py(n) + NODE_H for n in nodes)

    # first pass: collect wires, find how far loop-backs dip
    wires = []
    back_counts = {}
    for src_name, outs in conns.items():
        s = by_name.get(src_name)
        if not s:
            continue
        s_type = s["type"].split(".")[-1]
        sx, sy = px(s) + NODE_W, py(s) + NODE_H / 2
        for ctype, outputs in outs.items():
            for oi, targets in enumerate(outputs):
                for t in targets:
                    tgt = by_name.get(t["node"])
                    if not tgt:
                        continue
                    tx, ty = px(tgt), py(tgt) + NODE_H / 2
                    backwards = tx < sx and ctype == "main"
                    drop = 0
                    if backwards:
                        k = back_counts.get(t["node"], 0)
                        back_counts[t["node"]] = k + 1
                        drop = (node_max_y + 56 + k * 20) - max(sy, ty)
                    wires.append(dict(sx=sx, sy=sy, tx=tx, ty=ty, drop=drop,
                                      dashed=ctype != "main", oi=oi,
                                      if_lbl=(s_type == "if" and ctype == "main")))

    bottom = node_max_y
    for w in wires:
        if w["drop"]:
            bottom = max(bottom, max(w["sy"], w["ty"]) + w["drop"])
    W = span_w + PAD * 2
    H = bottom + PAD

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="100%" role="img" aria-label="{html.escape(TITLES[key])} — live n8n canvas render">'
    )
    parts.append(f'<rect width="{W}" height="{H}" fill="{BG}"/>')
    parts.append(
        "<style>text{font-family:ui-monospace,'SF Mono',Menlo,Consolas,monospace}"
        f".t{{font-size:12px;font-weight:700;fill:{TEXT};letter-spacing:.04em}}"
        f".ty{{font-size:10.5px;fill:{MUTED};letter-spacing:.05em}}"
        f".cap{{font-size:12px;font-weight:700;fill:{TEXT};letter-spacing:.08em}}"
        f".sub{{font-size:10.5px;fill:{MUTED};letter-spacing:.06em}}</style>"
    )
    # header
    parts.append(f'<text x="{PAD}" y="30" class="cap">{html.escape(TITLES[key].upper())}</text>')
    parts.append(
        f'<text x="{W - PAD}" y="30" text-anchor="end" class="sub">'
        f"LIVE CANVAS RENDER · {len(nodes)} NODES</text>"
    )
    parts.append(
        f'<line x1="{PAD}" y1="44" x2="{W - PAD}" y2="44" stroke="{WIRE}" stroke-width="1"/>'
    )

    # wires (under nodes)
    for w in wires:
        sx, sy, tx, ty = w["sx"], w["sy"], w["tx"], w["ty"]
        dashed = ' stroke-dasharray="5 4"' if w["dashed"] else ""
        if w["drop"]:
            parts.append(
                f'<path d="M{sx},{sy:.1f} C{sx},{sy + w["drop"]:.1f} '
                f'{tx},{ty + w["drop"]:.1f} {tx},{ty:.1f}" fill="none" '
                f'stroke="{WIRE}" stroke-width="2"/>'
            )
            parts.append(
                f'<circle cx="{(sx + tx) / 2:.1f}" '
                f'cy="{max(sy, ty) + w["drop"]:.1f}" r="3" fill="{ACCENT}"/>'
            )
        else:
            dx = max(36, abs(tx - sx) / 2)
            parts.append(
                f'<path d="M{sx},{sy:.1f} C{sx + dx:.1f},{sy:.1f} '
                f'{tx - dx:.1f},{ty:.1f} {tx},{ty:.1f}" fill="none" '
                f'stroke="{WIRE}" stroke-width="2"{dashed}/>'
            )
            parts.append(
                f'<circle cx="{(sx + tx) / 2:.1f}" cy="{(sy + ty) / 2:.1f}" '
                f'r="3" fill="{ACCENT}"/>'
            )
        # IF branch labels (n8n: output 0 = true, 1 = false)
        if w["if_lbl"]:
            lbl = "true" if w["oi"] == 0 else "false"
            parts.append(
                f'<text x="{sx + 8}" y="{sy - 8}" class="ty">{lbl}</text>'
            )

    # nodes
    for n in nodes:
        x, y = px(n), py(n)
        cat = category(n["type"])
        col = CAT_COLORS.get(cat, CAT_COLORS["other"])
        disabled = n.get("disabled", False)
        dash = ' stroke-dasharray="6 4"' if disabled else ""
        parts.append(
            f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" rx="7" '
            f'fill="{PANEL}" stroke="{col}" stroke-width="1.5" opacity="0.98"{dash}/>'
        )
        parts.append(
            f'<rect x="{x}" y="{y + 10}" width="4" height="{NODE_H - 20}" rx="2" fill="{col}"/>'
        )
        lines = wrap(n["name"])
        ty0 = y + 28 if len(lines) == 1 else y + 22
        for i, ln in enumerate(lines):
            parts.append(
                f'<text x="{x + 16}" y="{ty0 + i * 16}" class="t">'
                f"{html.escape(ln)}</text>"
            )
        parts.append(
            f'<text x="{x + 16}" y="{y + NODE_H - 12}" class="ty">'
            f"{html.escape(pretty_type(n['type']).upper())}</text>"
        )

    parts.append("</svg>")
    open(dst, "w").write("\n".join(parts))
    print(f"{key}: {len(nodes)} nodes -> {dst} ({W}x{H})")


if __name__ == "__main__":
    outdir = os.path.expanduser("~/workspace/portfolio-site/assets/call-qa")
    for key in [f"wf0{i}" for i in range(1, 9)]:
        render(key, f"/tmp/{key}.json", os.path.join(outdir, f"{key}.svg"))
