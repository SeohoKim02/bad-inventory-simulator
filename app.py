import streamlit as st
from datetime import time

from calculator import calculate_inventory_analysis
from discount_analyzer import analyze_discount_options
from excel_loader import load_excel_file
from route_analyzer import analyze_dc_retailer_routes
from cutline_analyzer import analyze_product_distance_cutline
from time_window_analyzer import analyze_trade_time_windows
from transfer_path_analyzer import analyze_direct_vs_dc_transfer
from promotion_analyzer import analyze_promotion_vs_transfer
from network_path_analyzer import analyze_multi_store_network_paths
from kakao_map_viewer import show_kakao_map, show_kakao_map_with_highlights
from final_summary import build_final_recommendations


st.set_page_config(page_title="편의점 악성재고 계산기", layout="wide")

st.title("편의점 악성재고 처리 의사결정 프로그램")
st.write("엑셀 데이터를 기반으로 악성재고, 재배치, 프로모션, 이동 경로를 분석합니다.")


# =========================
# 사이드바 설정
# =========================
st.sidebar.header("지도 설정")

kakao_js_key = st.sidebar.text_input(
    "카카오맵 JavaScript 키 입력",
    type="password",
    help="카카오 개발자 사이트에서 복사한 JavaScript 키를 입력하세요."
)

st.sidebar.markdown("---")
st.sidebar.header("단일 상품 직접 계산")

store_name = st.sidebar.text_input("점포명", "강남점")
product_name = st.sidebar.text_input("상품명", "삼각김밥")

stock_qty = st.sidebar.number_input("현재 재고 수량", min_value=0, value=100)
sales_30d = st.sidebar.number_input("최근 30일 판매량", min_value=0, value=5)
inbound_days = st.sidebar.number_input("입고 후 지난 일수", min_value=0, value=50)

unit_cost = st.sidebar.number_input("상품 1개당 원가(원)", min_value=0, value=1500)
daily_holding_cost = st.sidebar.number_input("하루 보관비(원)", min_value=0, value=20)
disposal_cost_per_unit = st.sidebar.number_input("상품 1개당 폐기비용(원)", min_value=0, value=300)

discount_rate = st.sidebar.number_input("할인율(%)", min_value=0.0, max_value=100.0, value=20.0)
expected_sales_increase_rate = st.sidebar.number_input("할인 시 판매 증가율(%)", min_value=0.0, value=50.0)

transfer_possible = st.sidebar.selectbox("타점포 이동 가능 여부", ["가능", "불가능"])
distance_km = st.sidebar.number_input("점포 간 거리(km)", min_value=0.0, value=10.0)
cost_per_km = st.sidebar.number_input("km당 운송비(원)", min_value=0.0, value=500.0)
target_store_sales_30d = st.sidebar.number_input("이동 대상 점포 최근 30일 판매량", min_value=0, value=20)


# =========================
# 엑셀 업로드
# =========================
st.markdown("---")
st.subheader("엑셀 파일 입력")

uploaded_file = st.file_uploader(
    "편의점 재고 데이터 엑셀 파일을 업로드하세요",
    type=["xlsx"]
)

if uploaded_file is not None:
    excel_data, missing_sheets = load_excel_file(uploaded_file)

    if missing_sheets:
        st.error(f"엑셀 파일에 필요한 시트가 없습니다: {missing_sheets}")

    else:
        st.success("엑셀 파일을 성공적으로 불러왔습니다.")

        stores = excel_data["stores"]
        products = excel_data["products"]
        inventory = excel_data["inventory"]
        routes = excel_data["routes"]

        # =========================
        # 데이터 요약
        # =========================
        st.subheader("데이터 요약")

        total_stores = len(stores)
        total_products = len(products)
        total_inventory = len(inventory)
        total_routes = len(routes)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("점포/DC 수", f"{total_stores}개")
        col2.metric("상품 수", f"{total_products}개")
        col3.metric("재고 데이터", f"{total_inventory}건")
        col4.metric("경로 데이터", f"{total_routes}건")

        with st.expander("원본 엑셀 데이터 보기"):
            st.write("stores 시트")
            st.dataframe(stores)

            st.write("products 시트")
            st.dataframe(products)

            st.write("inventory 시트")
            st.dataframe(inventory)

            st.write("routes 시트")
            st.dataframe(routes)

        # =========================
        # 분석 조건
        # =========================
        st.markdown("---")
        st.subheader("분석 조건 설정")

        setting_col1, setting_col2, setting_col3 = st.columns(3)

        with setting_col1:
            departure_time = st.time_input(
                "DC/점포 출발 예정 시간",
                value=time(9, 0),
                key="departure_time_excel"
            )

        with setting_col2:
            promotion_type = st.selectbox(
                "프로모션 유형",
                ["할인 프로모션", "1+1 프로모션"],
                key="promotion_type_excel"
            )

        with setting_col3:
            promotion_discount_rate = st.number_input(
                "프로모션 할인율(%)",
                min_value=0.0,
                max_value=100.0,
                value=20.0,
                key="promotion_discount_rate_excel"
            )

        setting_col4, setting_col5 = st.columns(2)

        with setting_col4:
            promotion_sales_increase_rate = st.number_input(
                "프로모션 예상 판매 증가율(%)",
                min_value=0.0,
                max_value=500.0,
                value=80.0,
                key="promotion_sales_increase_rate_excel"
            )

        with setting_col5:
            promotion_fixed_cost = st.number_input(
                "프로모션 고정비(원)",
                min_value=0,
                value=0,
                key="promotion_fixed_cost_excel"
            )

        # =========================
        # 1. DC-점포 거리 및 운송비 계산
        # =========================
        dc_routes, best_dc_by_retailer = analyze_dc_retailer_routes(
            stores,
            routes
        )

        # =========================
        # 2. 제품별 거리 컷라인 계산 + 거래가능시간 계산
        # =========================
        if dc_routes.empty:
            cutline_result = None
            best_valid_routes = None
            no_valid_items = None
            time_result = None
            time_error = "DC와 점포를 연결하는 route 데이터가 없어 컷라인/시간 분석을 할 수 없습니다."
        else:
            cutline_result, best_valid_routes, no_valid_items = analyze_product_distance_cutline(
                products,
                inventory,
                dc_routes
            )

            time_result, time_error = analyze_trade_time_windows(
                cutline_result,
                stores,
                departure_time
            )

        # =========================
        # 3. 점포 간 직접 이동 vs DC 경유
        # =========================
        transfer_path_result = analyze_direct_vs_dc_transfer(
            stores,
            products,
            inventory,
            routes,
            departure_time
        )

        # =========================
        # 4. 프로모션 vs 재배치
        # =========================
        promotion_result = analyze_promotion_vs_transfer(
            stores,
            inventory,
            transfer_path_result,
            promotion_type,
            promotion_discount_rate,
            promotion_sales_increase_rate,
            promotion_fixed_cost
        )

        # =========================
        # 5. 여러 점포 연결 최저비용 경로
        # =========================
        network_path_result, network_error = analyze_multi_store_network_paths(
            stores,
            products,
            routes,
            transfer_path_result,
            departure_time
        )

        # =========================
        # 6. 최종 추천 모아보기
        # =========================
        final_recommendations, final_rec_summary = build_final_recommendations(
            promotion_result,
            network_path_result
        )

        st.markdown("---")
        st.subheader("최종 추천 모아보기")

        if final_recommendations.empty:
            st.info("최종 추천으로 정리할 결과가 없습니다.")
        else:
            summary_col1, summary_col2 = st.columns(2)

            summary_col1.metric("최종 추천 건수", f"{len(final_recommendations)}건")
            summary_col2.metric("추천 유형 수", f"{len(final_rec_summary)}개")

            st.write("추천 유형 요약")
            st.dataframe(final_rec_summary)

            st.bar_chart(
                final_rec_summary.set_index("final_recommendation")["count"]
            )

            st.write("최종 추천 상세")
            st.dataframe(
                final_recommendations[
                    [
                        "product_name",
                        "source_store",
                        "target_store",
                        "suggested_qty",
                        "final_recommendation",
                        "estimated_cost",
                        "reason",
                    ]
                ]
            )

        # =========================
        # 지도
        # =========================
        st.markdown("---")
        st.subheader("카카오맵 기반 점포 및 경로 시각화")

        if kakao_js_key:
            show_kakao_map(
                stores,
                routes,
                kakao_js_key
            )
        else:
            st.info("카카오맵을 보려면 왼쪽 사이드바에 JavaScript 키를 입력하세요.")

        # =========================
        # 추천 경로 강조 지도
        # =========================
        st.markdown("---")
        st.subheader("추천 경로 강조 지도")

        highlight_paths = []

        if not transfer_path_result.empty:
            recommended_transfer_paths = transfer_path_result[
                transfer_path_result["recommended_path"] != "이동 비추천"
            ]

            for _, path_row in recommended_transfer_paths.iterrows():
                if path_row["recommended_path"] == "직접 이동 추천":
                    path_names = [
                        path_row["source_store"],
                        path_row["target_store"],
                    ]

                elif path_row["recommended_path"] == "DC 경유 이동 추천":
                    path_names = [
                        path_row["source_store"],
                        path_row["via_dc"],
                        path_row["target_store"],
                    ]

                else:
                    continue

                highlight_paths.append(
                    {
                        "path_names": path_names,
                        "label": f"{path_row['product_name']} - {path_row['recommended_path']}",
                    }
                )

        if not network_path_result.empty:
            network_recommended_paths = network_path_result[
                network_path_result["network_recommendation"] == "다중 경로 추천"
            ]

            for _, network_row in network_recommended_paths.iterrows():
                path_names = str(network_row["network_path"]).split(" → ")

                highlight_paths.append(
                    {
                        "path_names": path_names,
                        "label": f"{network_row['product_name']} - 다중 경로 추천",
                    }
                )

        if kakao_js_key and highlight_paths:
            show_kakao_map_with_highlights(
                stores,
                routes,
                kakao_js_key,
                highlight_paths
            )
        elif not kakao_js_key:
            st.info("추천 경로 지도를 보려면 왼쪽 사이드바에 카카오맵 JavaScript 키를 입력하세요.")
        else:
            st.info("강조 표시할 추천 경로가 없습니다.")

        # =========================
        # DC-점포 분석
        # =========================
        st.markdown("---")
        st.subheader("DC-점포 거리 및 운송비 계산")

        if dc_routes.empty:
            st.warning("DC와 점포를 연결하는 route 데이터가 없습니다.")
        else:
            st.write("DC-점포 전체 경로 계산 결과")
            st.dataframe(dc_routes)

            st.write("점포별 최적 DC 추천")
            st.dataframe(best_dc_by_retailer)

            st.write("점포별 최저 운송비 그래프")
            chart_data = best_dc_by_retailer.set_index("retailer_name")["transport_cost"]
            st.bar_chart(chart_data)

        # =========================
        # 제품별 거리 컷라인
        # =========================
        st.markdown("---")
        st.subheader("제품별 거리 컷라인 판별")

        if cutline_result is None or cutline_result.empty:
            st.warning("제품별 거리 컷라인 분석 결과가 없습니다.")
        else:
            st.write("제품별 DC-점포 이동 가능 여부")
            st.dataframe(
                cutline_result[
                    [
                        "dc_name",
                        "retailer_name",
                        "product_name",
                        "category",
                        "distance_km",
                        "distance_cutline_km",
                        "transport_cost",
                        "cutline_status",
                    ]
                ]
            )

            st.write("제품별/점포별 컷라인 내 최적 DC")

            if best_valid_routes.empty:
                st.warning("거리 컷라인을 만족하는 이동 가능 경로가 없습니다.")
            else:
                st.dataframe(
                    best_valid_routes[
                        [
                            "store_id",
                            "product_id",
                            "product_name",
                            "category",
                            "dc_name",
                            "retailer_name",
                            "distance_km",
                            "distance_cutline_km",
                            "transport_cost",
                        ]
                    ]
                )

            st.write("거리 컷라인 때문에 이동 불가능한 품목")

            if no_valid_items.empty:
                st.success("모든 품목이 최소 1개 이상의 이동 가능 경로를 가지고 있습니다.")
            else:
                st.dataframe(no_valid_items)

            st.write("이동 가능 여부 요약")
            status_summary = (
                cutline_result.groupby("cutline_status")
                .size()
                .reset_index(name="count")
            )

            st.dataframe(status_summary)
            st.bar_chart(status_summary.set_index("cutline_status")["count"])

        # =========================
        # 거래가능시간
        # =========================
        st.markdown("---")
        st.subheader("거래가능시간 판별")

        if time_error:
            st.warning(time_error)
        elif time_result is None or time_result.empty:
            st.warning("거래가능시간 분석 결과가 없습니다.")
        else:
            st.write("거리 컷라인 + 거래가능시간 판별 결과")
            st.dataframe(time_result)

            st.write("최종 이동 가능 여부 요약")
            time_summary = (
                time_result.groupby("final_status")
                .size()
                .reset_index(name="count")
            )

            st.dataframe(time_summary)
            st.bar_chart(time_summary.set_index("final_status")["count"])

            st.write("최종 이동 가능한 경로만 보기")
            available_routes = time_result[time_result["final_status"] == "가능"]

            if available_routes.empty:
                st.warning("거리 컷라인과 거래가능시간을 모두 만족하는 경로가 없습니다.")
            else:
                st.dataframe(available_routes)

        # =========================
        # 점포 간 직접 이동 vs DC 경유
        # =========================
        st.markdown("---")
        st.subheader("점포 간 직접 이동 vs DC 경유 이동 비교")

        if transfer_path_result.empty:
            st.warning("점포 간 이동 비교가 가능한 후보가 없습니다.")
            st.info("조건: 같은 상품을 가진 점포 중, 한 점포는 재고가 많고 판매가 낮으며 다른 점포는 판매량이 더 높아야 합니다.")
        else:
            st.write("직접 이동과 DC 경유 이동 비교 결과")
            st.dataframe(transfer_path_result)

            st.write("추천 경로 요약")
            path_summary = (
                transfer_path_result.groupby("recommended_path")
                .size()
                .reset_index(name="count")
            )

            st.dataframe(path_summary)
            st.bar_chart(path_summary.set_index("recommended_path")["count"])

            st.write("이동 추천 결과만 보기")
            recommended_only = transfer_path_result[
                transfer_path_result["recommended_path"] != "이동 비추천"
            ]

            if recommended_only.empty:
                st.warning("조건을 만족하는 이동 추천 경로가 없습니다.")
            else:
                st.dataframe(
                    recommended_only[
                        [
                            "product_name",
                            "source_store",
                            "target_store",
                            "suggested_transfer_qty",
                            "recommended_path",
                            "recommendation_reason",
                            "direct_cost",
                            "via_cost",
                            "via_dc",
                        ]
                    ]
                )

        # =========================
        # 프로모션 vs 재배치
        # =========================
        st.markdown("---")
        st.subheader("프로모션 vs 재배치 비교")

        if promotion_result.empty:
            st.warning("프로모션과 비교할 수 있는 이동 후보가 없습니다.")
        else:
            st.write("프로모션과 재배치 비용 비교 결과")
            st.dataframe(promotion_result)

            st.write("최종 처리 방식 요약")
            promo_summary = (
                promotion_result.groupby("final_decision")
                .size()
                .reset_index(name="count")
            )

            st.dataframe(promo_summary)
            st.bar_chart(promo_summary.set_index("final_decision")["count"])

            st.write("프로모션/재배치 추천 결과")
            st.dataframe(
                promotion_result[
                    [
                        "product_name",
                        "source_store",
                        "target_store",
                        "suggested_qty",
                        "recommended_transfer_path",
                        "transfer_cost",
                        "promotion_type",
                        "promotion_net_cost",
                        "final_decision",
                        "decision_reason",
                    ]
                ]
            )

            with st.expander("프로모션 계산식 보기"):
                for _, promo_row in promotion_result.iterrows():
                    st.write(
                        f"{promo_row['product_name']} / "
                        f"{promo_row['source_store']} → {promo_row['target_store']}: "
                        f"{promo_row['promotion_formula']}"
                    )

        # =========================
        # 여러 점포 연결 최저비용 경로
        # =========================
        st.markdown("---")
        st.subheader("여러 점포 연결 최저비용 경로 계산")

        if network_error:
            st.warning(network_error)
        elif network_path_result.empty:
            st.warning("계산 가능한 다중 연결 경로가 없습니다.")
        else:
            st.write("다중 연결 경로 계산 결과")
            st.dataframe(network_path_result)

            st.write("다중 경로 추천 요약")
            network_summary = (
                network_path_result.groupby("network_recommendation")
                .size()
                .reset_index(name="count")
            )

            st.dataframe(network_summary)
            st.bar_chart(network_summary.set_index("network_recommendation")["count"])

            st.write("다중 경로 추천 결과만 보기")
            network_recommended_only = network_path_result[
                network_path_result["network_recommendation"] == "다중 경로 추천"
            ]

            if network_recommended_only.empty:
                st.info("기존 직접 이동 또는 DC 경유 방식이 더 적합합니다.")
            else:
                st.dataframe(
                    network_recommended_only[
                        [
                            "product_name",
                            "source_store",
                            "target_store",
                            "network_path",
                            "network_distance_km",
                            "network_time_min",
                            "network_cost",
                            "arrival_time",
                            "reason",
                        ]
                    ]
                )


# =========================
# 단일 상품 직접 계산
# =========================
st.markdown("---")
st.subheader("단일 상품 직접 계산")

if st.button("계산 시작"):
    result = calculate_inventory_analysis(
        stock_qty=stock_qty,
        sales_30d=sales_30d,
        inbound_days=inbound_days,
        unit_cost=unit_cost,
        daily_holding_cost=daily_holding_cost,
        discount_rate=discount_rate,
        expected_sales_increase_rate=expected_sales_increase_rate,
        transfer_possible=(transfer_possible == "가능"),
        distance_km=distance_km,
        cost_per_km=cost_per_km,
        target_store_sales_30d=target_store_sales_30d,
        disposal_cost_per_unit=disposal_cost_per_unit,
    )

    discount_comparison = analyze_discount_options(
        stock_qty=stock_qty,
        sales_30d=sales_30d,
        unit_cost=unit_cost,
        daily_holding_cost=daily_holding_cost,
        discount_rates=[10, 20, 30, 40],
        expected_sales_increase_rate=expected_sales_increase_rate,
    )

    st.success("계산이 완료되었습니다.")

    st.subheader("입력 정보")
    st.write(f"점포명: {store_name}")
    st.write(f"상품명: {product_name}")

    col1, col2, col3 = st.columns(3)

    col1.metric("재고소진 예상일수", f"{result['stock_cover_days']}일")
    col2.metric("위험점수", f"{result['risk_score']}점")
    col3.metric("악성재고 여부", "예" if result["is_bad_stock"] else "아니오")

    st.subheader("판단 이유")

    if result["reasons"]:
        for reason in result["reasons"]:
            st.write(f"- {reason}")
    else:
        st.write("위험 요소가 크지 않습니다.")

    st.subheader("비용 비교")

    st.write(f"유지 비용: {result['keep_cost']}원")
    st.write(f"할인 전략 순비용: {result['discount_net_cost']}원")
    st.write(f"폐기 비용: {result['disposal_cost']}원")

    if result["transfer_net_cost"] is not None:
        st.write(f"자동 계산된 이동비: {result['transfer_cost']}원")
        st.write(f"타점포 이동 순비용: {result['transfer_net_cost']}원")

        cost_data = {
            "전략": ["유지", "할인", "타점포 이동", "폐기"],
            "비용": [
                result["keep_cost"],
                result["discount_net_cost"],
                result["transfer_net_cost"],
                result["disposal_cost"],
            ],
        }

    else:
        st.write("타점포 이동 순비용: 이동 불가능")

        cost_data = {
            "전략": ["유지", "할인", "폐기"],
            "비용": [
                result["keep_cost"],
                result["discount_net_cost"],
                result["disposal_cost"],
            ],
        }

    st.bar_chart(data=cost_data, x="전략", y="비용")

    st.subheader("최종 추천")
    st.write(f"추천 전략: **{result['best_action']}**")
    st.write(f"추천 이유: {result['recommendation_reason']}")
    st.write(f"발주 조언: **{result['order_advice']}**")

    st.subheader("할인율별 비교")
    st.dataframe(discount_comparison)

    discount_chart_data = {
        "할인율": [f"{item['discount_rate']}%" for item in discount_comparison],
        "순비용": [item["net_cost"] for item in discount_comparison],
    }

    st.bar_chart(discount_chart_data, x="할인율", y="순비용")

    st.subheader("계산 방식")
    st.write(result["formula_text"]["stock_cover_days_formula"])
    st.write(result["formula_text"]["risk_formula"])
    st.write(result["formula_text"]["keep_cost_formula"])
    st.write(result["formula_text"]["discount_formula"])
    st.write(result["formula_text"]["transfer_formula"])
    st.write(result["formula_text"]["disposal_formula"])


st.markdown("---")
st.caption("© 2026 김서호. All rights reserved.")