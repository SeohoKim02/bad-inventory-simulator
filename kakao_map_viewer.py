import streamlit.components.v1 as components


def create_kakao_map_html(stores, routes, kakao_js_key):
    stores_data = stores.copy()
    routes_data = routes.copy()

    kakao_js_key = str(kakao_js_key).strip()

    stores_data = stores_data.dropna(subset=["latitude", "longitude"])

    if stores_data.empty:
        return "<p>지도에 표시할 위치 데이터가 없습니다.</p>"

    center_lat = float(stores_data["latitude"].mean())
    center_lng = float(stores_data["longitude"].mean())

    markers_js = ""

    for _, row in stores_data.iterrows():
        raw_store_id = str(row["store_id"])
        safe_store_id = raw_store_id.replace("-", "_").replace(" ", "_")

        store_name = str(row["store_name"])
        store_type = str(row["type"])
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

    lines_js = ""

    for i, row in routes_data.iterrows():
        from_id = str(row["from_id"])
        to_id = str(row["to_id"])

        if from_id not in store_coord_map or to_id not in store_coord_map:
            continue

        from_lat, from_lng = store_coord_map[from_id]
        to_lat, to_lng = store_coord_map[to_id]

        lines_js += f"""
        var linePath_{i} = [
            new kakao.maps.LatLng({from_lat}, {from_lng}),
            new kakao.maps.LatLng({to_lat}, {to_lng})
        ];

        var polyline_{i} = new kakao.maps.Polyline({{
            path: linePath_{i},
            strokeWeight: 3,
            strokeColor: '#FFCC33',
            strokeOpacity: 0.8,
            strokeStyle: 'solid'
        }});

        polyline_{i}.setMap(map);
        """

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
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
        <script type="text/javascript" src="https://dapi.kakao.com/v2/maps/sdk.js?appkey=__KAKAO_KEY__&autoload=false"></script>
    </head>
    <body>
        <div id="map"></div>
        <div id="debug">지도 로딩 준비 중...</div>

        <script>
            var debugBox = document.getElementById('debug');

            if (typeof kakao === 'undefined') {
                debugBox.innerHTML = '카카오 SDK가 로드되지 않았습니다. JavaScript 키 또는 도메인 등록을 확인하세요.';
            } else {
                kakao.maps.load(function() {
                    debugBox.innerHTML = '카카오맵 SDK 로드 성공';

                    var mapContainer = document.getElementById('map');

                    var mapOption = {
                        center: new kakao.maps.LatLng(__CENTER_LAT__, __CENTER_LNG__),
                        level: 8
                    };

                    var map = new kakao.maps.Map(mapContainer, mapOption);

                    __MARKERS_JS__

                    __LINES_JS__
                });
            }
        </script>
    </body>
    </html>
    """

    html = html.replace("__KAKAO_KEY__", kakao_js_key)
    html = html.replace("__CENTER_LAT__", str(center_lat))
    html = html.replace("__CENTER_LNG__", str(center_lng))
    html = html.replace("__MARKERS_JS__", markers_js)
    html = html.replace("__LINES_JS__", lines_js)

    return html


def show_kakao_map(stores, routes, kakao_js_key):
    html = create_kakao_map_html(stores, routes, kakao_js_key)
    components.html(html, height=720, scrolling=False)
    