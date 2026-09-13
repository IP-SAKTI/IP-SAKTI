"""
tests/test_multilingual_voice_refinement.py — Unit & Integration Tests for Multilingual Detection,
Script Validation, TTS Language Mapping, and RAG Pipeline Integrity.
"""

import pytest
from ip_sakti.multilingual.detector import LanguageDetector, _detect_script
from ip_sakti.multilingual.translator import QueryTranslator


def test_unicode_script_detection():
    """Verify deterministic script detection for Indic languages."""
    hi_query = "क्या भारत में हल्दी और नीम से बनी औषधीय संरचना का पेटेंट कराया जा सकता है?"
    te_query = "పసుపు మరియు వేపతో తయారు చేసిన ఔషధ సూత్రీకరణలోని ఔషధ గుణాలు సాంప్రదాయ జ్ఞానంలో ఇప్పటికే ఉన్నట్లయితే, భారతదేశంలో దానికి పేటెంట్ పొందవచ్చా?"
    kn_query = "ಅರಿಶಿನ ಮತ್ತು ಬೇವಿನಿಂದ ತಯಾರಿಸಿದ ಔಷಧೀಯ ಸಂಯೋಜನೆಯ ಔಷಧೀಯ ಗುಣಗಳು ಈಗಾಗಲೇ ಸಾಂಪ್ರದಾಯಿಕ ಜ್ಞಾನದ ಭಾಗವಾಗಿದ್ದರೆ, ಭಾರತದಲ್ಲಿ ಅದಕ್ಕೆ ಪೇಟೆಂಟ್ ಪಡೆಯಬಹುದೇ?"
    ml_query = "മഞ്ഞളും വേപ്പിലയും ഉപയോഗിച്ച് തയ്യാറാക്കുന്ന ഒരു ഔഷധ ഫോർമുലേഷനിലെ ഔഷധഗുണങ്ങൾ പരമ്പരാഗത അറിവിന്റെ ഭാഗമാണെങ്കിൽ, ഇന്ത്യയിൽ അതിന് പേറ്റന്റ് നേടാനാകുമോ?"

    assert _detect_script(hi_query) == "hi"
    assert _detect_script(te_query) == "te"
    assert _detect_script(kn_query) == "kn"
    assert _detect_script(ml_query) == "ml"


def test_language_detector_script_override():
    """Verify LanguageDetector uses script validation to accurately detect Indic queries."""
    detector = LanguageDetector()

    hi_res = detector.detect("क्या भारत में हल्दी और नीम से बनी औषधीय संरचना का पेटेंट कराया जा सकता है?")
    assert hi_res.language == "hi"
    assert hi_res.confidence == 1.0

    te_res = detector.detect("పసుపు మరియు వేపతో తయారు చేసిన ఔషధ సూత్రీకరణలోని ఔషధ గుణాలు సాంప్రదాయ జ్ఞానంలో ఇప్పటికే ఉన్నట్లయితే, భారతదేశంలో దానికి పేటెంట్ పొందవచ్చా?")
    assert te_res.language == "te"
    assert te_res.confidence == 1.0

    kn_res = detector.detect("ಅರಿಶಿನ ಮತ್ತು ಬೇವಿನಿಂದ ತಯಾರಿಸಿದ ಔಷಧೀಯ ಸಂಯೋಜನೆಯ ಔಷಧೀಯ ಗುಣಗಳು ಈಗಾಗಲೇ ಸಾಂಪ್ರದಾಯಿಕ ಜ್ಞಾನದ ಭಾಗವಾಗಿದ್ದರೆ, ಭಾರತದಲ್ಲಿ ಅದಕ್ಕೆ ಪೇಟೆಂಟ್ ಪಡೆಯಬಹುದೇ?")
    assert kn_res.language == "kn"
    assert kn_res.confidence == 1.0

    ml_res = detector.detect("മഞ്ഞളും വേപ്പിലയും ഉപയോഗിച്ച് തയ്യാറാക്കുന്ന ഒരു ഔഷധ ഫോർമുലേഷനിലെ ഔഷധഗുണങ്ങൾ പരമ്പരാഗത അറിവിന്റെ ഭാഗമാണെങ്കിൽ, ഇന്ത്യയിൽ അതിന് പേറ്റന്റ് നേടാനാകുമോ?")
    assert ml_res.language == "ml"
    assert ml_res.confidence == 1.0


def test_target_script_validation():
    """Verify QueryTranslator script validation logic across supported languages."""
    translator = QueryTranslator()

    assert translator._validate_target_script("क्या भारत में पेटेंट कराया जा सकता है?", "hi") is True
    assert translator._validate_target_script("భారతదేశంలో దానికి పేటెంట్ పొందవచ్చా?", "te") is True
    assert translator._validate_target_script("ಭಾರತದಲ್ಲಿ ಅದಕ್ಕೆ ಪೇಟೆಂಟ್ ಪಡೆಯಬಹುದೇ?", "kn") is True
    assert translator._validate_target_script("ഇന്ത്യയിൽ അതിന് പേറ്റന്റ് നേടാനാകുമോ?", "ml") is True
    assert translator._validate_target_script("English answer text", "en") is True
