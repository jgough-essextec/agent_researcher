from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass(frozen=True)
class RiskAssessment:
    finding: str
    likelihood: int
    impact: int
    score: int
    severity: RiskLevel
    remediation_phase: int


def calculate_risk_score(likelihood: int, impact: int) -> int:
    if not (1 <= likelihood <= 5):
        raise ValueError(f"likelihood must be 1-5, got {likelihood}")
    if not (1 <= impact <= 5):
        raise ValueError(f"impact must be 1-5, got {impact}")
    return likelihood * impact


def classify_severity(score: int) -> RiskLevel:
    if score >= 15:
        return RiskLevel.CRITICAL
    if score >= 9:
        return RiskLevel.HIGH
    if score >= 4:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def assess_email_security_risk(dmarc_policy: str, spf_assessment: str) -> RiskAssessment:
    if dmarc_policy == "missing" or spf_assessment == "missing":
        likelihood, impact = 5, 4
    elif dmarc_policy == "none":
        likelihood, impact = 4, 4
    elif dmarc_policy == "quarantine":
        likelihood, impact = 2, 3
    elif dmarc_policy == "reject" and spf_assessment == "present":
        likelihood, impact = 1, 2
    else:
        likelihood, impact = 3, 3

    score = calculate_risk_score(likelihood, impact)
    return RiskAssessment(
        finding="Email Security (SPF/DMARC)",
        likelihood=likelihood,
        impact=impact,
        score=score,
        severity=classify_severity(score),
        remediation_phase=1 if score >= 15 else 2,
    )
