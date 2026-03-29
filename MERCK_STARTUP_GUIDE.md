# Merck Startup Guide & Research Intelligence Workflow

This guide provides specialized instructions for Merck users to run the Agentic Platform and generate Research Intelligence reports using the unified Anthropic Claude infrastructure.

---

## 🚀 Quick Setup for Merck Users

### 1. Switch to the Fix Branch
Ensure you are on the `fix/merck-changes` branch which contains critical fixes for agent looping and BioMCP connectivity.

```bash
git fetch origin
git checkout fix/merck-changes
```

### 2. Configure Environment (`.env`)
Create or edit `streamlit-app/.env` and set the following:

```bash
# Unified Anthropic API Key (Standard for all research profiles)
# Note: You can also use AZURE_OPENAI_API_KEY or AZURE_API_KEY as a fallback 
# if you are routing through the Merck proxy.
ANTHROPIC_API_KEY=your_anthropic_key_here

# FIX: Enable BioMCP on corporate network
BIOMCP_DISABLE_SSL=true
```

### 3. Install Dependencies
```bash
cd streamlit-app
pip install -r requirements.txt
```

### 4. Launch the App
```bash
streamlit run app.py
```

---

## 🧬 Competitive Intelligence Workflow

Your advisor reported issues with reports not generating and agents going into infinite loops. We have implemented fixes for both.

### How to Generate a Report
In the sidebar, select **"Merck Enterprise Configuration"**. Then, use a high-level research query in the chat. The system is now optimized to recognize these as report requests and synthesize data from multiple agents (Chemical, Clinical, Literature, etc.).

**Example Report Queries:**
- `Generate a competitive intelligence report on PCSK9 inhibitors.`
- `Analyze the competitive landscape for GLP-1 receptor agonists in diabetes treatment.`
- `Summarize recent clinical trials and publications for pembrolizumab.`

### Why it's fixed now:
1.  **No more Event Loop Hangs:** The application no longer freezes during tool execution. A robust background event loop was implemented to handle continuous MCP tool calls properly, resolving the "technical issue with the event loop" error.
2.  **No more 90-minute hangs:** The agent now has an "Early Exit" trigger. If it gets a substantive answer from Claude but the model forgets the specific `FINAL ANSWER` tag, the agent will now recognize it and display it immediately.
3.  **BioMCP is Re-enabled:** By setting `BIOMCP_DISABLE_SSL=true`, the system can now reach NCBI/PubTator3 through the Merck corporate proxy without certificate errors.
4.  **Unified Infrastructure:** We have consolidated the system to support Anthropic Claude models seamlessly. You can now select Claude models directly within the Merck profile, and the system accepts either `ANTHROPIC_API_KEY` or `AZURE_OPENAI_API_KEY`.

---

## 🛠 Troubleshooting for Merck Network

| Issue | Resolution |
|-------|------------|
| **SSL/Certificate Errors** | Ensure `BIOMCP_DISABLE_SSL=true` is in your `.env`. |
| **"Anthropic Key Missing"** | Ensure you have selected "Merck Enterprise Configuration" in the sidebar. |
| **Connection Timeouts** | This is usually due to the RDS database being stopped (scheduled stops at 11 PM EST). If testing outside US business hours, connectivity to historical session data may be limited. |

---

## 📝 Documenting Fixes for Advisor
A full list of applied fixes and technical root cause analysis can be found in:
- `MERCK_CHANGES_FIXES.md` (Root directory)
- `docs/claude_fix_log.md` (Technical details)
