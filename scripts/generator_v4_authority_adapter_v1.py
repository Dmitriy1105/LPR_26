"""Bridge canonical Generator v4 organization records to evidence-backed authority engines."""
from __future__ import annotations

from delegation_authority_v1 import authorize_delegated_at, validate_delegations
from financial_authority_v1 import evaluate_financial_authority, validate_bands
from temporal_authority_v1 import authorize_at, validate_grants


def to_legacy_org(canonical: dict) -> dict:
    """Translate identifiers only; never infer authority from position or hierarchy."""
    return {
        "id": canonical["organization_id"],
        "units": [
            {"id": u["unit_id"], "department": u["unit_code"],
             "parent": u["parent_unit_id"]}
            for u in canonical["units"]
        ],
        "people": [
            {"id": p["contact_id"], "unit": p["unit_id"],
             "manager": p["manager_contact_id"]}
            for p in canonical["people"]
        ],
    }


def validate_bundle(canonical_org: dict, grants: list, financial_bands: list,
                    delegations: list) -> bool:
    legacy = to_legacy_org(canonical_org)
    validate_grants(legacy, grants)
    validate_bands(legacy, financial_bands)
    validate_delegations(legacy, grants, delegations)
    grant_ids = {g["grant_id"] for g in grants}
    band_ids = {b["band_id"] for b in financial_bands}
    delegation_ids = {d["delegation_id"] for d in delegations}
    if len(grant_ids) != len(grants) or len(band_ids) != len(financial_bands):
        raise ValueError("authority identifiers must be unique")
    if len(delegation_ids) != len(delegations):
        raise ValueError("delegation identifiers must be unique")
    return True


def evaluate(canonical_org: dict, grants: list, financial_bands: list,
             delegations: list, *, actor_id: str, action: str, permission: str,
             as_of: str, amount: float | None = None, currency: str | None = None,
             delegated: bool = False) -> dict:
    """Return an auditable authorization result for one decision instant."""
    validate_bundle(canonical_org, grants, financial_bands, delegations)
    legacy = to_legacy_org(canonical_org)
    if delegated:
        result = authorize_delegated_at(
            legacy, grants, delegations, actor_id, action, permission, as_of, amount
        )
    elif amount is not None:
        if currency is None:
            raise ValueError("currency is required for financial authority evaluation")
        result = evaluate_financial_authority(
            legacy, financial_bands, actor_id, action, permission, amount, currency, as_of
        )
    else:
        result = authorize_at(
            legacy, grants, actor_id, action, permission, as_of, amount
        )
    return {
        **result,
        "organization_id": canonical_org["organization_id"],
        "actor_id": actor_id,
        "action": action,
        "evaluated_at": as_of,
        "authority_source": (
            result.get("delegation_id") or result.get("band_id") or result.get("grant_id")
        ),
        "currency": currency,
        "amount": amount,
        "delegated": delegated,
    }
