/**
 * Planning Lab Frontend Logic (web/static/js/planning.js)
 * Supports Markdown Rendering (marked.js), Interactive Tabs, Dynamic Preset Prompts,
 * Metric Summary Cards, and Animated DAG Visualizations.
 */

let lastPlanningExecutionData = null;
let currentPlanningTab = 'trace';

function setPresetPrompt(index) {
    const input = document.getElementById("planningRequestInput");
    if (index === 1) {
        input.value = "Emergency plumbing burst at Nile Tower Cairo. Re-plan contractor schedules under Egyptian Law 4/1996 SLAs.";
    } else if (index === 2) {
        input.value = "Audit Egyptian Law 4/1996 emergency repair compliance for 6 residential units at Nile Tower.";
    } else if (index === 3) {
        input.value = "Draft temporary tenant relocation plan and rank vendor emergency dispatch priorities.";
    }
}

function clearPlanningInput() {
    document.getElementById("planningRequestInput").value = "";
}

function switchPlanningTab(tabName) {
    currentPlanningTab = tabName;
    document.querySelectorAll(".tab-btn").forEach(btn => btn.classList.remove("active"));
    
    if (tabName === 'trace') document.getElementById("tabBtnTrace").classList.add("active");
    if (tabName === 'markdown') document.getElementById("tabBtnMarkdown").classList.add("active");
    if (tabName === 'dag') document.getElementById("tabBtnDag").classList.add("active");

    if (lastPlanningExecutionData) {
        renderPlanningOutput(lastPlanningExecutionData);
    }
}

async function runPlanningAgentUI() {
    const requestText = document.getElementById("planningRequestInput").value.trim();
    const mode = document.getElementById("planningModeSelect").value;
    const envMode = document.getElementById("planningEnvModeSelect").value;
    const btn = document.getElementById("btnExecutePlanning");
    const container = document.getElementById("planningOutputContainer");

    if (!requestText) {
        alert("Please enter a planning request prompt.");
        return;
    }

    btn.disabled = true;
    btn.innerHTML = `<span class="pulse-ring" style="width:16px; height:16px; border-width:2px; display:inline-block; vertical-align:middle; margin-right:8px;"></span> Executing Autonomous Planning Agent...`;
    
    container.innerHTML = `
        <div class="pulse-loading">
            <div class="pulse-ring"></div>
            <div style="color: #818cf8; font-weight: 600;">Executing Autonomous Planning Agent Loop</div>
            <div style="color: #94a3b8; font-size: 0.82rem;">Decomposition: <strong>${mode.toUpperCase()}</strong> | Grounding: <strong>${envMode.toUpperCase()}</strong></div>
        </div>
    `;

    const startTime = performance.now();

    try {
        const response = await fetch("/api/planning/execute", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                request: requestText,
                mode: mode,
                env_mode: envMode
            })
        });

        const endTime = performance.now();
        const latencySec = ((endTime - startTime) / 1000).toFixed(2);

        const data = await response.json();
        data.latencySec = latencySec;
        lastPlanningExecutionData = data;

        btn.disabled = false;
        btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg><span>Execute Autonomous Planning Agent</span>`;

        if (data.status === "success") {
            renderPlanningOutput(data);
        } else {
            container.innerHTML = `
                <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); padding: 16px; border-radius: 10px; color: #fb7185;">
                    <div style="font-weight: 700; margin-bottom: 6px;">❌ Agent Execution Failed</div>
                    <div>${escapeHtml(data.summary || data.error)}</div>
                </div>
            `;
        }
    } catch (err) {
        btn.disabled = false;
        btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg><span>Execute Autonomous Planning Agent</span>`;
        container.innerHTML = `<div style="color: #fb7185; padding: 20px;">❌ Network/API Error: ${escapeHtml(err.message)}</div>`;
    }
}

function renderPlanningOutput(data) {
    const container = document.getElementById("planningOutputContainer");
    
    // Header Stats Banner
    let statsHeader = `
        <div style="display: flex; gap: 12px; margin-bottom: 18px; background: rgba(30, 41, 59, 0.6); padding: 12px 16px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06); flex-wrap: wrap;">
            <div style="flex: 1;"><span style="color:#94a3b8; font-size:0.75rem;">DECOMPOSITION</span><br><strong style="color:#818cf8;">${data.mode.toUpperCase()}</strong></div>
            <div style="flex: 1;"><span style="color:#94a3b8; font-size:0.75rem;">GROUNDING</span><br><strong style="color:#34d399;">${data.env_mode.toUpperCase()}</strong></div>
            <div style="flex: 1;"><span style="color:#94a3b8; font-size:0.75rem;">LATENCY</span><br><strong style="color:#f43f5e;">${data.latencySec || "3.5"}s</strong></div>
            <div style="flex: 1;"><span style="color:#94a3b8; font-size:0.75rem;">STATUS</span><br><strong style="color:#4ade80;">100% SUCCESS</strong></div>
        </div>
    `;

    if (currentPlanningTab === 'markdown') {
        let markdownContent = data.summary || "No summary output returned.";
        let parsedHtml = "";
        if (window.marked && typeof window.marked.parse === 'function') {
            parsedHtml = window.marked.parse(markdownContent);
        } else {
            parsedHtml = `<pre>${escapeHtml(markdownContent)}</pre>`;
        }
        container.innerHTML = statsHeader + `<div class="markdown-body">${parsedHtml}</div>`;
        return;
    }

    if (currentPlanningTab === 'dag') {
        container.innerHTML = statsHeader + renderDagFlow(data);
        return;
    }

    // Default: 'trace' Tab
    let traceHtml = statsHeader;
    
    // Summary Banner
    traceHtml += `
        <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 10px; padding: 14px; margin-bottom: 16px;">
            <div style="color: #a5b4fc; font-weight: 700; font-size: 0.85rem; margin-bottom: 4px;">🎯 Final Synthesis Summary</div>
            <div style="color: #f8fafc; font-size: 0.9rem; line-height: 1.5;">${escapeHtml(data.summary)}</div>
        </div>
    `;

    // Sub-tasks Breakdown
    if (data.trace && data.trace.subtasks && data.trace.subtasks.length > 0) {
        traceHtml += `<div style="color: #94a3b8; font-size: 0.8rem; font-weight: 700; margin-bottom: 10px; letter-spacing: 0.5px; text-transform: uppercase;">Executed Sub-Task DAG Steps (${data.trace.subtasks.length}):</div>`;
        
        data.trace.subtasks.forEach((st, idx) => {
            const routing = st.routing || {};
            const method = routing.method || st.method || "PS";
            let badgeClass = "badge-ps";
            let badgeLabelClass = "ps";

            if (method === "ToT") { badgeClass = "badge-tot"; badgeLabelClass = "tot"; }
            if (method === "LATS") { badgeClass = "badge-lats"; badgeLabelClass = "lats"; }

            traceHtml += `
                <div class="subtask-card ${badgeClass}">
                    <div class="subtask-header">
                        <span class="algo-badge ${badgeLabelClass}">${method} ROUTED</span>
                        <span style="color: #64748b; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">Step #${idx + 1}</span>
                    </div>
                    <div class="subtask-title">${escapeHtml(st.instruction)}</div>
                    ${routing.output ? `<div class="subtask-output">${escapeHtml(routing.output)}</div>` : ''}
                </div>
            `;
        });
    }

    container.innerHTML = traceHtml;
}

function renderDagFlow(data) {
    if (!data.trace || !data.trace.subtasks || data.trace.subtasks.length === 0) {
        return `<div style="color:#94a3b8; text-align:center; padding:20px;">No active DAG subtasks generated for this run.</div>`;
    }

    let dagHtml = `<div class="dag-container">`;
    data.trace.subtasks.forEach((st, idx) => {
        const method = st.routing?.method || st.method || "PS";
        dagHtml += `
            <div class="dag-node">
                <div>
                    <span class="dag-node-id">Task_0${idx+1}</span>
                    <strong style="color:#f8fafc; margin-left:8px; font-size:0.88rem;">${escapeHtml(st.instruction)}</strong>
                </div>
                <span class="algo-badge ${method.toLowerCase()}">${method}</span>
            </div>
        `;
        if (idx < data.trace.subtasks.length - 1) {
            dagHtml += `<div class="dag-arrow"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg></div>`;
        }
    });
    dagHtml += `</div>`;
    return dagHtml;
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
