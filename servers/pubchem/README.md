# PubChem MCP Server (Local)

Minimal MCP server exposing:
- `search_compounds_by_name` → returns CIDs
- `get_compound_properties` → returns identifiers/properties for a CID

### Requirements
- Node 18+ (`node -v`)
- `npm i` in repo root or in `servers/pubchem` to install `@modelcontextprotocol/sdk`

### Run (manual test)
```bash
npm install
npm run start
```
