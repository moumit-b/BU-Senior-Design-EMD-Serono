"""
Identifier Verification

Extracts structured identifiers from report markdown and verifies each one
against its authoritative public API using parallel HTTP requests.

Identifiers checked:
  - NCT numbers  → ClinicalTrials.gov API v2
  - PMIDs        → NCBI eutils
  - DOIs         → doi.org handle API
"""

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 5  # seconds per HTTP request

_NCT_RE  = re.compile(r'\bNCT\d{8}\b')
_PMID_RE = re.compile(r'\bPMID[:\s#]*(\d{7,8})\b', re.IGNORECASE)
_DOI_RE  = re.compile(r'\b(10\.\d{4,}/[^\s\)\]>,"\']+)')


def extract_identifiers(report_md: str) -> Dict[str, List[str]]:
    """Return deduplicated NCT numbers, PMIDs, and DOIs found in report_md."""
    ncts  = list(dict.fromkeys(_NCT_RE.findall(report_md)))
    pmids = list(dict.fromkeys(_PMID_RE.findall(report_md)))
    dois  = list(dict.fromkeys(
        d.rstrip('.,;:)]}') for d in _DOI_RE.findall(report_md)
    ))
    return {"nct": ncts, "pmid": pmids, "doi": dois}


# ---------------------------------------------------------------------------
# Per-type verifiers
# ---------------------------------------------------------------------------

def _check_drug_in_trial(data: dict, drug_name: str) -> bool:
    """Return True if drug_name appears in the trial title or interventions."""
    protocol = data.get("protocolSection", {})
    title = protocol.get("identificationModule", {}).get("briefTitle", "")
    interventions = [
        i.get("name", "")
        for i in protocol.get("armsInterventionsModule", {}).get("interventions", [])
    ]
    all_text = (title + " " + " ".join(interventions)).lower()
    drug_lower = drug_name.lower()
    if drug_lower in all_text:
        return True
    # Also check individual words (skip short words to avoid false matches)
    words = [w for w in drug_lower.split() if len(w) > 3]
    return any(w in all_text for w in words) if words else False


def _verify_nct(nct_id: str, drug_name: str = None) -> Tuple:
    """Verify NCT number. Returns (valid, details, drug_match) where drug_match
    is True/False if drug_name provided, None otherwise."""
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=REQUEST_TIMEOUT) as resp:
            if resp.status == 200:
                if drug_name:
                    data = json.loads(resp.read())
                    drug_match = _check_drug_in_trial(data, drug_name)
                    if drug_match:
                        return True, "verified on ClinicalTrials.gov", True
                    return True, "verified — drug not found in this trial", False
                return True, "verified on ClinicalTrials.gov", None
    except HTTPError as e:
        if e.code == 404:
            return False, "not found on ClinicalTrials.gov", None
        return False, f"HTTP {e.code}", None
    except URLError as e:
        return False, f"network error: {e.reason}", None
    except Exception as e:
        return False, f"error: {e}", None
    return False, "unexpected response", None


def _verify_pmid(pmid: str) -> Tuple[bool, str]:
    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        f"?db=pubmed&id={pmid}&retmode=json"
    )
    try:
        with urlopen(Request(url), timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            result = data.get("result", {})
            entry = result.get(pmid, {})
            if pmid in result and "error" not in entry:
                title = entry.get("title", "")[:60]
                return True, f'verified: "{title}"' if title else "verified on PubMed"
            return False, "ID not found in PubMed"
    except HTTPError as e:
        return False, f"HTTP {e.code}"
    except URLError as e:
        return False, f"network error: {e.reason}"
    except Exception as e:
        return False, f"error: {e}"


def _verify_doi(doi: str) -> Tuple[bool, str]:
    url = f"https://doi.org/api/handles/{doi}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            if data.get("responseCode") == 1:
                return True, "verified on doi.org"
            return False, f"unresolvable (responseCode {data.get('responseCode')})"
    except HTTPError as e:
        return False, f"HTTP {e.code}"
    except URLError as e:
        return False, f"network error: {e.reason}"
    except Exception as e:
        return False, f"error: {e}"


_VERIFIERS = {"nct": _verify_nct, "pmid": _verify_pmid, "doi": _verify_doi}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify_report(report_md: str, drug_name: str = None, max_workers: int = 8) -> Dict[str, Dict]:
    """
    Extract and verify all identifiers in report_md in parallel.

    Args:
        report_md:  Report markdown content.
        drug_name:  If provided, NCT numbers are cross-checked to confirm
                    the trial actually involves this drug.

    Returns:
        {
            "NCT04523584": {"type": "nct",  "valid": True,  "details": "...", "drug_match": True},
            "NCT99999999": {"type": "nct",  "valid": False, "details": "not found", "drug_match": None},
            "99999999":    {"type": "pmid", "valid": False, "details": "ID not found in PubMed"},
            ...
        }
    """
    identifiers = extract_identifiers(report_md)
    tasks = [
        (id_val, id_type)
        for id_type, id_list in identifiers.items()
        for id_val in id_list
    ]

    if not tasks:
        return {}

    results: Dict[str, Dict] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {
            pool.submit(_verify_nct, id_val, drug_name) if id_type == "nct"
            else pool.submit(_VERIFIERS[id_type], id_val): (id_val, id_type)
            for id_val, id_type in tasks
        }
        for future in as_completed(future_map):
            id_val, id_type = future_map[future]
            try:
                result = future.result()
                if id_type == "nct":
                    valid, details, drug_match = result
                    results[id_val] = {"type": id_type, "valid": valid, "details": details, "drug_match": drug_match}
                else:
                    valid, details = result
                    results[id_val] = {"type": id_type, "valid": valid, "details": details}
            except Exception as e:
                results[id_val] = {"type": id_type, "valid": False, "details": f"check failed: {e}"}

    return results
