import pathlib
import pytest
from src import parsing

SAMPLE_XLSX = pathlib.Path("samples/GT_Civil_Riverside_WWPS_Civil_ITP_Template.xlsx")

def test_doc_rejected_with_friendly_message():
    with pytest.raises(parsing.UnsupportedFormat) as e:
        parsing.parse("old.doc", b"\xd0\xcf\x11\xe0")
    assert "re-save" in str(e.value).lower() and "docx" in str(e.value).lower()

def test_unknown_extension_rejected():
    with pytest.raises(parsing.UnsupportedFormat):
        parsing.parse("x.txt", b"hi")

@pytest.mark.skipif(not SAMPLE_XLSX.exists(), reason="sample not present")
def test_xlsx_preserves_itp_columns():
    pd = parsing.parse(SAMPLE_XLSX.name, SAMPLE_XLSX.read_bytes())
    # All 12 ITP table column headers must survive parsing.
    for col in ["Acceptance Criteria", "Inspection Point", "Reference",
                "Witness / Release By", "QA Record / Evidence"]:
        assert col in pd.text, f"missing column: {col}"
    # A known data cell survives too (item numbering).
    assert "1.1" in pd.text
    assert pd.preview  # non-empty preview for UI
