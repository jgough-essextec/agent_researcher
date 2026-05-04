import pytest
from osint.services.risk_assessor import calculate_risk_score, classify_severity, RiskLevel, assess_email_security_risk, RiskAssessment


def test_high_likelihood_high_impact_is_critical():
    score = calculate_risk_score(likelihood=5, impact=5)
    assert score == 25
    assert classify_severity(score) == RiskLevel.CRITICAL


def test_low_likelihood_low_impact_is_low():
    score = calculate_risk_score(likelihood=1, impact=1)
    assert score == 1
    assert classify_severity(score) == RiskLevel.LOW


def test_medium_risk():
    score = calculate_risk_score(likelihood=3, impact=3)
    assert score == 9
    assert classify_severity(score) == RiskLevel.HIGH


def test_likelihood_must_be_1_to_5():
    with pytest.raises(ValueError):
        calculate_risk_score(likelihood=0, impact=3)


def test_impact_must_be_1_to_5():
    with pytest.raises(ValueError):
        calculate_risk_score(likelihood=3, impact=6)


def test_dmarc_missing_is_critical_or_high():
    result = assess_email_security_risk(dmarc_policy="missing", spf_assessment="missing")
    assert result.severity in (RiskLevel.CRITICAL, RiskLevel.HIGH)
    assert isinstance(result, RiskAssessment)


def test_full_enforcement_is_low_or_medium():
    result = assess_email_security_risk(dmarc_policy="reject", spf_assessment="present")
    assert result.severity in (RiskLevel.LOW, RiskLevel.MEDIUM)
