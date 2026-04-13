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

def _verify_nct(nct_id: str) -> Tuple[bool, str]:
    url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/json"}), timeout=REQUEST_TIMEOUT) as resp:
            if resp.status == 200:
                return True, "verified on ClinicalTrials.gov"
    except HTTPError as e:
        if e.code == 404:
            return False, "not found on ClinicalTrials.gov"
        return False, f"HTTP {e.code}"
    except URLError as e:
        return False, f"network error: {e.reason}"
    except Exception as e:
        return False, f"error: {e}"
    return False, "unexpected response"


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

def verify_report(report_md: str, max_workers: int = 8) -> Dict[str, Dict]:
    """
    Extract and verify all identifiers in report_md in parallel.

    Returns:
        {
            "NCT04523584": {"type": "nct",  "valid": True,  "details": "verified on ClinicalTrials.gov"},
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
            pool.submit(_VERIFIERS[id_type], id_val): (id_val, id_type)
            for id_val, id_type in tasks
        }
        for future in as_completed(future_map):
            id_val, id_type = future_map[future]
            try:
                valid, details = future.result()
            except Exception as e:
                valid, details = False, f"check failed: {e}"
            results[id_val] = {"type": id_type, "valid": valid, "details": details}

    return results
