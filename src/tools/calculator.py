def calculate_growth(old_value: float, new_value: float) -> dict:
    if old_value == 0: 
        return {
            "success": False, "error": "Old value cannot be zero", "growth_pct": None, "direction": None 
            }
    growth = ((new_value - old_value) / old_value) * 100
    return { 
        "success": True, "old_value": old_value, "new_value": new_value, "growth_pct": round(growth, 2), "direction": "up" if growth > 0 else "down"
          }
def calculate_margin(profit: float, revenue: float) -> dict:
    if revenue == 0: return {
         "success": False, "error": "Revenue cannot be zero", "margin_pct": None
           }
    margin = (profit / revenue) * 100
    # Rate the margin
    if margin > 20: 
        rating = "excellent" 
    elif margin > 10: 
        rating = "good" 
    elif margin > 5: 
        rating = "average" 
    else: 
        rating = "low"
    return { 
            "success": True, "profit": profit, "revenue": revenue, "margin_pct": round(margin, 2), "rating": rating 
            }
def compare_pe_ratio(company_pe: float, sector_avg_pe: float) -> dict:
    if sector_avg_pe == 0: 
        return { 
            "success": False, 
            "error": "Sector average cannot be zero"
              }
    difference = company_pe - sector_avg_pe 
    premium_pct = (difference / sector_avg_pe) * 100
    if premium_pct > 10: 
        verdict = "overvalued" 
    elif premium_pct < -10: 
        verdict = "undervalued" 
    else: 
        verdict = "fairly valued"
    return { 
        "success": True, 
        "company_pe": company_pe, 
        "sector_avg_pe": sector_avg_pe, 
        "difference": round(difference, 2), 
        "premium_pct": round(premium_pct, 2), 
        "verdict": verdict 
        }
def calculate_cagr(start_value: float, end_value: float, years: int) -> dict:
    if start_value <= 0: 
        return { 
            "success": False, "error": "Start value must be greater than zero" 
            }
    if years <= 0: 
        return { 
            "success": False, 
            "error": "Years must be greater than zero" 
            }
    cagr = ((end_value / start_value) ** (1 / years) - 1) * 100
    return { 
        "success": True, "start_value": start_value, "end_value": end_value, "years": years, "cagr_pct": round(cagr, 2) 
        }
def calculate_debt_ratio(total_debt: float, total_assets: float) -> dict:
    if total_assets == 0: 
        return {"success": False, "error": "Assets cannot be zero"}
    ratio = total_debt / total_assets
    if ratio < 0.3: 
        risk = "low risk" 
    elif ratio < 0.5: 
        risk = "moderate risk" 
    else: 
        risk = "high risk"
        return { 
            "success": True, 
            "total_debt": total_debt, 
            "total_assets": total_assets, 
            "debt_ratio": round(ratio, 3),
              "risk_level": risk 
              }
if __name__ == "__main__":
    # Example usage
    print("=" * 50) 
    print("Testing Calculator") 
    print("=" * 50)

    print("\n1. Growth Test:") 
    print(calculate_growth(100, 120))

    print("\n2. Margin Test:") 
    print(calculate_margin(20, 100))

    print("\n3. P/E Ratio Test:") 
    print(compare_pe_ratio(24.3, 22.0))
    print("\n4. CAGR Test:") 
    print(calculate_cagr(100, 200, 5))
    print("\n5. Debt Ratio Test:") 
    print(calculate_debt_ratio(30, 100))

    print("\n All tests done!")
