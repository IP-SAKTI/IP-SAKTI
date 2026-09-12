"""
scratch/test_multilingual_gemini_end_to_end.py

Automated test script for 4 language test cases (English, Kannada, Telugu, Hindi)
validating ASR -> Language Detection -> Query Translation -> RAG -> Answer Translation -> Script Validation.
"""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load env variables explicitly
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, Jurisdiction, FormulationCategory
from ip_sakti.multilingual.translator import QueryTranslator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multilingual_test")


def test_language_pipeline():
    srv = IPSAKTIService()
    
    test_cases = [
        {
            "name": "TEST 1 - ENGLISH",
            "query": "What permissions are required to manufacture Ayurvedic medicine?",
            "expected_lang": "en",
        },
        {
            "name": "TEST 2 - KANNADA",
            "query": "ಆಯುರ್ವೇದ ಔಷಧ ತಯಾರಿಸಲು ಯಾವ ಅನುಮತಿಗಳು ಬೇಕು?",
            "expected_lang": "kn",
        },
        {
            "name": "TEST 3 - TELUGU",
            "query": "ఆయుర్వేద ఔషధాన్ని తయారు చేయడానికి ఏ అనుమతులు అవసరం?",
            "expected_lang": "te",
        },
        {
            "name": "TEST 4 - HINDI",
            "query": "आयुर्वेदिक दवा बनाने के लिए कौन सी अनुमति आवश्यक है?",
            "expected_lang": "hi",
        },
    ]

    results = []

    for tc in test_cases:
        logger.info(f"\n==================================================")
        logger.info(f"=== {tc['name']} ===")
        logger.info(f"Raw Query: {tc['query']!r}")
        logger.info(f"Expected Language: {tc['expected_lang']}")
        
        req = QueryRequest(
            raw_query=tc["query"],
            jurisdiction=Jurisdiction.INDIA,
            formulation_category=FormulationCategory.CLASSICAL,
        )
        
        resp = srv.process_query(req)
        
        detected_lang = resp.detected_language
        resp_lang = resp.response_language
        norm_query = resp.normalized_english_query
        answer_text = resp.answer
        
        logger.info(f"Detected Language: {detected_lang}")
        logger.info(f"Response Language: {resp_lang}")
        logger.info(f"Normalized English Query: {norm_query!r}")
        logger.info(f"Answer Snippet: {answer_text[:120]!r}...")
        
        script_valid = QueryTranslator._validate_target_script(answer_text, tc["expected_lang"])
        logger.info(f"Target Script Validation ({tc['expected_lang']}): {script_valid}")
        
        results.append({
            "name": tc["name"],
            "detected_lang": detected_lang,
            "resp_lang": resp_lang,
            "norm_query": norm_query,
            "script_valid": script_valid,
            "success": (detected_lang == tc["expected_lang"] and script_valid),
        })

    logger.info("\n==================================================")
    logger.info("=== SUMMARY OF MULTILINGUAL END-TO-END TESTS ===")
    logger.info("==================================================")
    all_ok = True
    for r in results:
        status = "PASSED" if r["success"] else "FAILED"
        if not r["success"]:
            all_ok = False
        logger.info(f"{r['name']}: {status} | Detected: {r['detected_lang']} | Script Valid: {r['script_valid']}")

    return all_ok


if __name__ == "__main__":
    success = test_language_pipeline()
    if not success:
        sys.exit(1)
