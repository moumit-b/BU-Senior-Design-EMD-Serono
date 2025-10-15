async function getJSON(url) {
  const res = await fetch(url, { headers: { "User-Agent": "pubchem-test/0.1" }});
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return res.json();
}

async function main() {
  // Step 1: Search for caffeine with max_results=3
  const searchUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/${encodeURIComponent('caffeine')}/cids/JSON`;
  const searchData = await getJSON(searchUrl);
  const cids = searchData?.IdentifierList?.CID ?? [];
  const firstThreeCids = cids.slice(0, 3);

  console.log('Search results (first 3 CIDs):', firstThreeCids);

  // Step 2: Get properties for the first CID
  const firstCid = firstThreeCids[0];
  const props = ["MolecularFormula","MolecularWeight","IUPACName","IsomericSMILES","InChIKey"].join(",");
  const propsUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${firstCid}/property/${props}/JSON`;
  const propsData = await getJSON(propsUrl);
  const p = propsData?.PropertyTable?.Properties?.[0] ?? {};

  // Step 3: Build compact JSON result
  const result = {
    cid: firstCid,
    MolecularFormula: p.MolecularFormula,
    MolecularWeight: p.MolecularWeight,
    IUPACName: p.IUPACName,
    IsomericSMILES: p.IsomericSMILES,
    InChIKey: p.InChIKey,
    link: `https://pubchem.ncbi.nlm.nih.gov/compound/${firstCid}`
  };

  console.log('\nCompact JSON result:');
  console.log(JSON.stringify(result, null, 2));
}

main().catch(console.error);
