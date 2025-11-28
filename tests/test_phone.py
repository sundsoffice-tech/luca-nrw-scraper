from scriptname import normalize_phone
def T(x,y): assert normalize_phone(x)==y
def test_normals():
    T("0211 123456", "+49211123456")
    T("+49 (0) 211-123456", "+49211123456")
    T("0049 (0)176 123 45 67", "+491761234567")
