"""T11 mirror — "Research claims are grounded before credited": FACADE (engine) / PROSE (step).

Live shape: ``grounding_gate.grounding_verdict:56`` / ``grounding_gate.build_verdict:111`` have
TEST-ONLY callers. This is the row the tests-path filter exists for: without the filter the
engine looks wired; with it, the facade is visible.
"""


def grounding_verdict(finding, source_supports):
    if finding.get("groundsToPlan") == "NO":
        return "ESCALATE"
    if not source_supports:
        return "REJECT"
    return "GROUND"


def build_verdict(finding, source_supports, evidence):
    return {"evidence": evidence, "verdict": grounding_verdict(finding, source_supports)}
