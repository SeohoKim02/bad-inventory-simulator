import pandas as pd
from datetime import time


def time_to_minutes(value):
    if pd.isna(value):
        return None

    if isinstance(value, time):
        return value.hour * 60 + value.minute

    value_str = str(value).strip()

    # 엑셀에서 "06:00:00"처럼 들어오는 경우 처리
    parts = value_str.split(":")
    if len(parts) >= 2:
        hour = int(parts[0])
        minute = int(parts[1])
        return hour * 60 + minute

    return None


def minutes_to_time_text(minutes):
    minutes = int(minutes)
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"


def is_within_window(target_min, start_min, end_min):
    if start_min is None or end_min is None:
        return False

    # 일단 같은 날 기준으로 계산
    return start_min <= target_min <= end_min


def analyze_trade_time_windows(cutline_result, stores, departure_time):
    stores_data = stores.copy()
    route_data = cutline_result.copy()

    required_columns = ["available_start", "available_end"]

    for col in required_columns:
        if col not in stores_data.columns:
            return None, f"stores 시트에 '{col}' 열이 없습니다."

    departure_min = departure_time.hour * 60 + departure_time.minute

    time_info = stores_data[
        ["store_id", "available_start", "available_end"]
    ].copy()

    time_info["available_start_min"] = time_info["available_start"].apply(time_to_minutes)
    time_info["available_end_min"] = time_info["available_end"].apply(time_to_minutes)

    start_map = dict(zip(time_info["store_id"], time_info["available_start_min"]))
    end_map = dict(zip(time_info["store_id"], time_info["available_end_min"]))

    result_rows = []

    for _, row in route_data.iterrows():
        dc_id = row["dc_id"]
        retailer_id = row["retailer_id"]

        dc_start = start_map.get(dc_id)
        dc_end = end_map.get(dc_id)

        retailer_start = start_map.get(retailer_id)
        retailer_end = end_map.get(retailer_id)

        travel_time_min = row["travel_time_min"]
        arrival_min = departure_min + travel_time_min

        depart_possible = is_within_window(departure_min, dc_start, dc_end)
        arrival_same_day = arrival_min <= 24 * 60
        arrival_possible = (
            arrival_same_day
            and is_within_window(arrival_min, retailer_start, retailer_end)
        )

        if depart_possible and arrival_possible:
            time_status = "가능"
            time_reason = "DC 출고시간과 점포 입고시간을 모두 만족"
        elif not depart_possible:
            time_status = "불가능"
            time_reason = "DC 출고 가능 시간이 아님"
        elif not arrival_same_day:
            time_status = "불가능"
            time_reason = "도착 시간이 당일 범위를 초과"
        else:
            time_status = "불가능"
            time_reason = "점포 입고 가능 시간이 아님"

        cutline_status = row.get("cutline_status", "확인불가")

        final_status = (
            "가능"
            if cutline_status == "가능" and time_status == "가능"
            else "불가능"
        )

        result_rows.append(
            {
                "dc_name": row["dc_name"],
                "retailer_name": row["retailer_name"],
                "product_name": row["product_name"],
                "category": row["category"],
                "distance_km": row["distance_km"],
                "distance_cutline_km": row["distance_cutline_km"],
                "travel_time_min": travel_time_min,
                "departure_time": minutes_to_time_text(departure_min),
                "arrival_time": minutes_to_time_text(arrival_min),
                "cutline_status": cutline_status,
                "time_status": time_status,
                "final_status": final_status,
                "time_reason": time_reason,
            }
        )

    result = pd.DataFrame(result_rows)

    return result, None