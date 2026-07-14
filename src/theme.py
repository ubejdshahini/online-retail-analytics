"""Single source of truth for dashboard, chart, and export colors."""

THEME = {
    "page_bg": "#FFFFFF",
    "card_bg": "#F8FAFC",
    "border": "#E2E8F0",
    "text_muted": "#94A3B8",
    "text_secondary": "#475569",
    "text_primary": "#0F172A",
    "accent": "#2563EB",
    "accent_tint": "#DBEAFE",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
}

CHART_COLORS = (
    THEME["accent"],
    THEME["warning"],
    THEME["success"],
    "#8B5CF6",
    "#EC4899",
    "#6B7280",
)


def css_variables() -> str:
    """Return theme values as CSS custom properties."""
    return "\n".join(
        f"--color-{name.replace('_', '-')}: {value};"
        for name, value in THEME.items()
    )
