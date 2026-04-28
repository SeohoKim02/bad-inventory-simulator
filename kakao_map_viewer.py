import re
import streamlit.components.v1 as components


def _safe_js_name(value):
    return re.sub(r"\W", "_", str(value))


def _escape_js_text(value):
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def create_kakao_map_html(stores, routes, kakao_js_key, highlight_paths=None):
    stores_data = stores.copy()
    routes_data = routes.copy()

    kakao_js_key = str(kakao_js_key).strip()
    highlight_paths = highlight_paths or []

    stores_data = stores_data.dropna(subset=["latitude", "longitude"])

    if stores_data.empty:
        return "<p>지도에 표시할 위치 데이터가 없습니다.</p>"

    center_lat = float(stores_data["latitude"].mean())
    center_lng = float(stores_data["longitude"].mean())

    markers_js = ""

    for _, row in stores_data.iterrows():
        raw_store_id = str(row["store_id"])
        safe_store_id = _safe_js_name(raw_store_id)

        store_name = _escape_js_text(row["store_name"])
        store_type = _escape_js_text(row["type"])
        lat = float(row["latitude"])
        lng = float(row["longitude"])

        markers_js += f"""
        var markerPosition_{safe_store_id} = new kakao.maps.LatLng({lat}, {lng});

        var marker_{safe_store_id} = new kakao.maps.Marker({{
            position: markerPosition_{safe_store_id},
            map: map
        }});

        var infowindow_{safe_store_id} = new kakao.maps.InfoWindow({{
            content: '<div style="padding:8px;font-size:13px;white-space:nowrap;">'
                     + '<b>{store_name}</b><br>'
                     + '유형: {store_type}'
                     + '</div>'
        }});

        kakao.maps.event.addListener(marker_{safe_store_id}, 'mouseover', function() {{
            infowindow_{safe_store_id}.open(map, marker_{safe_store_id});
        }});

        kakao.maps.event.addListener(marker_{safe_store_id}, 'mouseout', function() {{
            infowindow_{safe_store_id}.close();
        }});
        """

    store_coord_map = {
        str(row["store_id"]): (float(row["latitude"]), float(row["longitude"]))
        for _, row in stores_data.iterrows()
    }

    store_name_coord_map = {
        str(row["store_name"]): (float(row["latitude"]), float(row["longitude"]))
        for _, row in stores_data.iterrows()
    }

    base_lines_js = ""

    for i, row in routes_data.iterrows():
        from_id = str(row["from_id"])
        to_id = str(row["to_id"])

        if from_id not in store_coord_map or to_id not in store_coord_map:
            continue

        from_lat, from_lng = store_coord_map[from_id]
        to_lat, to_lng = store_coord_map[to_id]

        base_lines_js += f"""
        var baseLinePath_{i} = [
            new kakao.maps.LatLng({from_lat}, {from_lng}),
            new kakao.maps.LatLng({to_lat}, {to_lng})
        ];

        var basePolyline_{i} = new kakao.maps.Polyline({{
            path: baseLinePath_{i},
            strokeWeight: 2,
            strokeColor: '#C9CDD2',
            strokeOpacity: 0.55,
            strokeStyle: 'solid'
        }});

        basePolyline_{i}.setMap(map);
        """

    highlight_lines_js = ""

    for idx, path_info in enumerate(highlight_paths):
        path_names = path_info.get("path_names", [])
        label = _escape_js_text(path_info.get("label", "추천 경로"))

        coords = []

        for name in path_names:
            if name in store_name_coord_map:
                coords.append(store_name_coord_map[name])

        if len(coords) < 2:
            continue

        coord_js = ",\n".join(
            [f"new kakao.maps.LatLng({lat}, {lng})" for lat, lng in coords]
        )

        highlight_lines_js += f"""
        var highlightPath_{idx} = [
            {coord_js}
        ];

        var highlightPolyline_{idx} = new kakao.maps.Polyline({{
            path: highlightPath_{idx},
            strokeWeight: 7,
            strokeColor: '#FFD43B',
            strokeOpacity: 0.95,
            strokeStyle: 'solid'
        }});

        highlightPolyline_{idx}.setMap(map);

        var highlightInfo_{idx} = new kakao.maps.InfoWindow({{
            content: '<div style="padding:8px;font-size:13px;white-space:nowrap;background:#FFF8CC;">'
                     + '<b>{label}</b>'
                     + '</div>'
        }});

        kakao.maps.event.addListener(highlightPolyline_{idx}, 'mouseover', function(mouseEvent) {{
            highlightInfo_{idx}.setPosition(mouseEvent.latLng);
            highlightInfo_{idx}.open(map);
        }});

        kakao.maps.event.addListener(highlightPolyline_{idx}, 'mouseout', function() {{
            highlightInfo_{idx}.close();
        }});
        """

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="Content-Security-Policy" content="upgrade-insecure-requests">
        <style>
            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
            }

            #map {
                width: 100%;
                height: 650px;
                border-radius: 14px;
                border: 1px solid #dddddd;
            }

            #debug {
                margin-top: 10px;
                color: #444;
                font-size: 14px;
            }
        </style>
    </head>

    <body>
        <div id="map"></div>
        <div id="debug">1단계: 지도 스크립트 실행 시작</div>

        <script>
            var debugBox = document.getElementById('debug');

            function initMap() {
                try {
                    debugBox.innerHTML = '2단계: 카카오 SDK 로드 성공';

                    var mapContainer = document.getElementById('map');

                    var mapOption = {
                        center: new kakao.maps.LatLng(__CENTER_LAT__, __CENTER_LNG__),
                        level: 8
                    };

                    var map = new kakao.maps.Map(mapContainer, mapOption);

                    __BASE_LINES_JS__

                    __MARKERS_JS__

                    __HIGHLIGHT_LINES_JS__

                    debugBox.innerHTML = '3단계: 카카오맵 표시 완료';
                } catch (error) {
                    debugBox.innerHTML = '지도 생성 중 오류: ' + error.message;
                }
            }

            var script = document.createElement('script');
            script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=__KAKAO_KEY__&autoload=false';

            script.onload = function() {
                if (typeof kakao === 'undefined') {
                    debugBox.innerHTML = '카카오 SDK 객체를 찾을 수 없습니다. JavaScript 키 또는 도메인을 확인하세요.';
                    return;
                }

                kakao.maps.load(function() {
                    initMap();
                });
            };

            script.onerror = function() {
                debugBox.innerHTML = '카카오 SDK 파일 로드 실패. JavaScript 키 또는 도메인 등록을 확인하세요.';
            };

            document.head.appendChild(script);
        </script>
    </body>
    </html>
    """

    html = html.replace("__KAKAO_KEY__", kakao_js_key)
    html = html.replace("__CENTER_LAT__", str(center_lat))
    html = html.replace("__CENTER_LNG__", str(center_lng))
    html = html.replace("__BASE_LINES_JS__", base_lines_js)
    html = html.replace("__MARKERS_JS__", markers_js)
    html = html.replace("__HIGHLIGHT_LINES_JS__", highlight_lines_js)

    return html


def show_kakao_map(stores, routes, kakao_js_key):
    html = create_kakao_map_html(stores, routes, kakao_js_key)
    components.html(html, height=720, scrolling=False)


def show_kakao_map_with_highlights(stores, routes, kakao_js_key, highlight_paths):
    html = create_kakao_map_html(stores, routes, kakao_js_key, highlight_paths)
    components.html(html, height=720, scrolling=False)
