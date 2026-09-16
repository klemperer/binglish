from binglish.core.version import SemVer, is_newer


def test_semver_parse_basic():
    v = SemVer.parse("1.4.6")
    assert (v.major, v.minor, v.patch) == (1, 4, 6)


def test_semver_parse_v_prefix():
    v = SemVer.parse("v2.0.0")
    assert v.major == 2


def test_is_newer_true():
    assert is_newer("1.5.0", "1.4.6")


def test_is_newer_false_on_same():
    assert not is_newer("1.4.6", "1.4.6")


def test_is_newer_false_on_downgrade():
    # Original bug: any inequality treated as update
    assert not is_newer("1.4.0", "1.4.6")


def test_is_newer_false_on_empty_remote():
    assert not is_newer("", "1.4.6")
