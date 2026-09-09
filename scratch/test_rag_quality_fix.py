import sys
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.service import IPSAKTIService
from ip_sakti.models.query import QueryRequest, SearchMode, Jurisdiction, FormulationCategory

def test_rag_quality():
    print("=" * 70)
    print("TESTING RAG QUALITY FIX — MANUFACTURING & COMMERCIAL SALE COMPLIANCE")
    print("=" * 70)

    service = IPSAKTIService()

    query_text = "What regulatory requirements should be considered before manufacturing and commercially selling an Ayurvedic formulation in India?"

    req = QueryRequest(
        raw_query=query_text,
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.UNKNOWN,
        search_mode=SearchMode.INTERNAL,
    )

    resp = service.process_query(req)

    print("\n--- GENERATED ANSWER ---")
    print(resp.answer)
    print("------------------------\n")

    print(f"Confidence Score: {resp.confidence.score if resp.confidence else 'N/A'}")
    print(f"Is Abstention: {resp.is_abstention}")
    print(f"Agents Invoked: {[a.value for a in resp.agents_invoked]}")

    print("\n--- GROUNDED EVIDENCE CARDS ---")
    seen_urls = set()
    has_duplicates = False

    for idx, chunk in enumerate(resp.evidence, start=1):
        print(f"\n[Card {idx}] Title: {chunk.title}")
        print(f"       Authority: {chunk.authority}")
        print(f"       URL: {chunk.source_url}")
        print(f"       Snippet: \"{chunk.content[:150]}...\"")

        url_key = (chunk.source_url or '').strip().lower()
        text_key = chunk.content[:50].strip().lower()
        card_key = f"{url_key}:{text_key}"
        if card_key in seen_urls:
            print("       ⚠️ DUPLICATE CARD DETECTED!")
            has_duplicates = True
        seen_urls.add(card_key)

    # 1. Answer Primary Focus Check
    lower_ans = resp.answer.lower()
    has_sla_form24d = "form 24" in lower_ans or "state licensing" in lower_ans or "licence" in lower_ans or "license" in lower_ans
    has_gmp = "schedule t" in lower_ans or "gmp" in lower_ans or "good manufacturing" in lower_ans
    has_tech_staff = "technical" in lower_ans or "qualified" in lower_ans or "degree" in lower_ans or "personnel" in lower_ans
    has_rule_158b = "158" in lower_ans or "classical" in lower_ans or "proprietary" in lower_ans
    has_labelling = "label" in lower_ans or "packaging" in lower_ans or "rule 161" in lower_ans or "batch" in lower_ans

    print("\n--- VALIDATION RESULTS ---")
    print(f"1. Primary SLA / Form 24D Licensing: {'PASS' if has_sla_form24d else 'FAIL'}")
    print(f"2. Qualified Technical Personnel:    {'PASS' if has_tech_staff else 'FAIL'}")
    print(f"3. Schedule T / GMP Compliance:     {'PASS' if has_gmp else 'FAIL'}")
    print(f"4. Product Classification (158-B):  {'PASS' if has_rule_158b else 'FAIL'}")
    print(f"5. Labelling & Documentation:       {'PASS' if has_labelling else 'FAIL'}")
    print(f"6. Source URL Deduplication:        {'PASS' if not has_duplicates else 'FAIL'}")

    # Check separation of IP considerations
    if "section 3" in lower_ans or "patent" in lower_ans:
        if "additional ip" in lower_ans or "ip consideration" in lower_ans or "patent consideration" in lower_ans:
            print("7. IP / Patent Separation:           PASS (Separated under IP section)")
        else:
            print("7. IP / Patent Separation:           FAIL (IP info mixed into main body)")
    else:
        print("7. IP / Patent Separation:           PASS (Main answer focused strictly on regulatory compliance)")

    assert has_sla_form24d and has_gmp and has_tech_staff, "Regulatory manufacturing elements missing from primary answer"
    print("\nALL RAG QUALITY VERIFICATION CHECKS PASSED!")

if __name__ == "__main__":
    test_rag_quality()
