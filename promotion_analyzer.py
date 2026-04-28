import pandas as pd


def safe_float(value, default=0):
    if pd.isna(value):
        return default
    return float(value)


def analyze_promotion_vs_transfer(
    stores,
    inventory,
    transfer_path_result,
    promotion_type,
    promotion_discount_rate,
    promotion_sales_increase_rate,
    promotion_fixed_cost,
):
    stores_data = stores.copy()
    inventory_data = inventory.copy()
    transfer_data = transfer_path_result.copy()

    if transfer_data.empty:
        return pd.DataFrame()

    store_name_to_id = dict(zip(stores_data["store_name"], stores_data["store_id"]))

    result_rows = []

    for _, row in transfer_data.iterrows():
        product_id = row["product_id"]
        product_name = row["product_name"]
        source_store_name = row["source_store"]
        target_store_name = row["target_store"]

        source_store_id = store_name_to_id.get(source_store_name)

        if source_store_id is None:
            continue

        inv_match = inventory_data[
            (inventory_data["store_id"] == source_store_id)
            & (inventory_data["product_id"] == product_id)
        ]

        if inv_match.empty:
            continue

        source_inv = inv_match.iloc[0]

        suggested_qty = int(row["suggested_transfer_qty"])
        unit_cost = safe_float(source_inv["unit_cost"])
        daily_holding_cost = safe_float(source_inv["daily_holding_cost"])
        sales_30d = safe_float(source_inv["sales_30d"])

        # 현재 상태로 유지했을 때 보관비
        if sales_30d > 0:
            current_cover_days = suggested_qty / (sales_30d / 30)
        else:
            current_cover_days = 999

        current_holding_cost = (
            suggested_qty * daily_holding_cost * min(current_cover_days, 30)
        )

        # 프로모션 후 예상 판매량
        improved_sales_30d = sales_30d * (1 + promotion_sales_increase_rate / 100)

        if improved_sales_30d > 0:
            promotion_cover_days = suggested_qty / (improved_sales_30d / 30)
        else:
            promotion_cover_days = 999

        promotion_holding_cost = (
            suggested_qty * daily_holding_cost * min(promotion_cover_days, 30)
        )

        saved_holding_cost = max(0, current_holding_cost - promotion_holding_cost)

        # 프로모션 비용 계산
        if promotion_type == "1+1 프로모션":
            promotion_loss = suggested_qty * unit_cost * 0.5
        else:
            promotion_loss = suggested_qty * unit_cost * (promotion_discount_rate / 100)

        promotion_total_cost = promotion_loss + promotion_fixed_cost
        promotion_net_cost = promotion_total_cost - saved_holding_cost

        # 재배치 비용 선택
        recommended_path = row["recommended_path"]

        if recommended_path == "직접 이동 추천":
            transfer_cost = row["direct_cost"]
        elif recommended_path == "DC 경유 이동 추천":
            transfer_cost = row["via_cost"]
        else:
            transfer_cost = None

        if transfer_cost is None or pd.isna(transfer_cost):
            final_decision = "프로모션 추천"
            decision_reason = "이동 가능한 경로가 없어 프로모션 처리가 더 적합합니다."
        elif promotion_net_cost <= transfer_cost:
            final_decision = "프로모션 추천"
            decision_reason = "프로모션 순비용이 재배치 비용보다 낮습니다."
        else:
            final_decision = "재배치 추천"
            decision_reason = "재배치 비용이 프로모션 순비용보다 낮습니다."

        formula = (
            f"프로모션 순비용 = "
            f"프로모션 손실 {round(promotion_total_cost, 1)}원 "
            f"- 절감 보관비 {round(saved_holding_cost, 1)}원 "
            f"= {round(promotion_net_cost, 1)}원"
        )

        result_rows.append(
            {
                "product_name": product_name,
                "source_store": source_store_name,
                "target_store": target_store_name,
                "suggested_qty": suggested_qty,
                "recommended_transfer_path": recommended_path,
                "transfer_cost": round(transfer_cost, 1)
                if transfer_cost is not None and not pd.isna(transfer_cost)
                else None,
                "promotion_type": promotion_type,
                "promotion_net_cost": round(promotion_net_cost, 1),
                "saved_holding_cost": round(saved_holding_cost, 1),
                "final_decision": final_decision,
                "decision_reason": decision_reason,
                "promotion_formula": formula,
            }
        )

    return pd.DataFrame(result_rows)
