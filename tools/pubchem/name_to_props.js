"use strict";

const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, "").split("=")));
const name = args.name || args.n;

if (!name) {
  console.error('Usage: node tools/pubchem/name_to_props.js --name="caffeine"');
  process.exit(1);
}

async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "pubchem-cli/0.1" } });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

(async () => {
  try {
    const props = [
      "MolecularFormula","MolecularWeight","IUPACName","IsomericSMILES","InChI","InChIKey"
    ].join(",");

    const searchUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent(name)}/cids/JSON`;
    const s = await getJSON(searchUrl);
    const cid = (s?.IdentifierList?.CID ?? [])[0];

    if (!cid) {
      console.error(`No CID found for "${name}"`);
      process.exit(2);
    }

    const propUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/property/${props}/JSON`;
    const d = await getJSON(propUrl);
    const p = d?.PropertyTable?.Properties?.[0] ?? {};

    const out = {
      query: name,
      cid,
      MolecularFormula: p.MolecularFormula,
      MolecularWeight: p.MolecularWeight,
      IUPACName: p.IUPACName,
      IsomericSMILES: p.IsomericSMILES,
      InChIKey: p.InChIKey,
      link: `https://pubchem.ncbi.nlm.nih.gov/compound/${cid}`,
      provenance: { searchUrl, propUrl }
    };

    console.log(JSON.stringify(out, null, 2));
  } catch (err) {
    console.error(err.message || String(err));
    process.exit(1);
  }
})();
