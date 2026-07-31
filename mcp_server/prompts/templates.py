from __future__ import annotations


def draft_lease_notice(
    tenant_name: str,
    property_name: str,
    unit_number: str,
    start_date: str,
    end_date: str,
    monthly_rent: float,
    additional_terms: str = "",
) -> str:
    """Build a professional lease notice for a tenant.

    Args:
        tenant_name: Full name of the tenant.
        property_name: Name of the property.
        unit_number: Unit or apartment identifier.
        start_date: Lease start date in ISO format.
        end_date: Lease end date in ISO format.
        monthly_rent: Monthly rent amount.
        additional_terms: Optional extra terms or notes.

    Returns:
        A formatted lease notice prompt.
    """
    lines = [
        f"Draft a professional lease notice for {tenant_name}.",
        f"Property: {property_name}",
        f"Unit: {unit_number}",
        f"Lease period: {start_date} to {end_date}",
        f"Monthly rent: {monthly_rent:.2f} EGP",
    ]

    if additional_terms:
        lines.append(f"Additional terms: {additional_terms}")

    lines.append(
        "Include a polite summary of expectations and the next steps for signing the lease."
    )

    return "\n".join(lines)
