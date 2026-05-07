def generate_plan(query: str, sector: str):

    steps = []

    if sector == "IT":

        steps = [
            "Analyze revenue growth",
            "Analyze operating profit",
            "Study AI and cloud business",
            "Compare with competitors",
            "Identify risks and outlook"
        ]

    elif sector == "PHARMA":

        steps = [
            "Analyze drug portfolio",
            "Study revenue growth",
            "Check regulatory approvals",
            "Compare competitors",
            "Identify risks"
        ]

    return {
        "dimensions": [
            "financials",
            "competition",
            "risks"
        ],
        "planned_steps": steps,
        "sources_to_use": [
            "annual reports",
            "news",
            "market analysis"
        ],
        "estimated_depth": "standard"
    }