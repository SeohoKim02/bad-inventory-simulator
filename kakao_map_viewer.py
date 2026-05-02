import json
import streamlit.components.v1 as components


def _records_json(df):
    return df.to_json(orient="records", force_ascii=False)


def create_kakao_map_html(stores, routes, kakao_js_key, highlight_paths=None):
    stores_data = stores.copy().dropna(subset=["latitude", "longitude"])
    routes_data = routes.copy()
    highlight_paths = highlight_paths or []

    if stores_data.empty:
        return "<p>지도에 표시할 위치 데이터가 없습니다.</p>"

    kakao_js_key = str(kakao_js_key).strip()

    center_lat = float(stores_data["latitude"].mean())
    center_lng = float(stores_data["longitude"].mean())

    stores_json = _records_json(stores_data)
    routes_json = _records_json(routes_data)
    highlight_paths_json = json.dumps(highlight_paths, ensure_ascii=False)

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
                font-family: Arial, sans-serif;
            }

            #map {
                width: 100%;
                height: 650px;
                border-radius: 14px;
                border: 1px solid #dddddd;
            }
        </style>
    </head>

    <body>
        <div id="map"></div>

        <script>
            var stores = __STORES_JSON__;
            var routes = __ROUTES_JSON__;
            var highlightPaths = __HIGHLIGHT_PATHS_JSON__;

            var script = document.createElement('script');
            script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=__KAKAO_KEY__&autoload=false';

            script.onload = function() {
                kakao.maps.load(function() {
                    initMap();
                });
            };

            document.head.appendChild(script);

            function initMap() {
                var mapContainer = document.getElementById('map');

                var mapOption = {
                    center: new kakao.maps.LatLng(__CENTER_LAT__, __CENTER_LNG__),
                    level: 8
                };

                var map = new kakao.maps.Map(mapContainer, mapOption);

                var storeById = {};
                var storeByName = {};
                var bounds = new kakao.maps.LatLngBounds();

                stores.forEach(function(store) {
                    if (store.latitude == null || store.longitude == null) {
                        return;
                    }

                    var position = new kakao.maps.LatLng(store.latitude, store.longitude);

                    storeById[String(store.store_id)] = store;
                    storeByName[String(store.store_name)] = store;

                    bounds.extend(position);

                    var marker = new kakao.maps.Marker({
                        map: map,
                        position: position
                    });

                    var storeName = store.store_name || "점포";
                    var storeType = store.type || "unknown";

                    var info = new kakao.maps.InfoWindow({
                        content:
                            '<div style="padding:10px 14px;font-size:15px;white-space:nowrap;">' +
                            '<b>' + storeName + '</b><br>' +
                            '유형: <b>' + storeType + '</b>' +
                            '</div>'
                    });

                    kakao.maps.event.addListener(marker, 'mouseover', function() {
                        info.open(map, marker);
                    });

                    kakao.maps.event.addListener(marker, 'mouseout', function() {
                        info.close();
                    });
                });

                if (stores.length > 0) {
                    map.setBounds(bounds);
                }

                routes.forEach(function(route) {
                    var fromStore = storeById[String(route.from_id)];
                    var toStore = storeById[String(route.to_id)];

                    if (!fromStore || !toStore) {
                        return;
                    }

                    var path = [
                        new kakao.maps.LatLng(fromStore.latitude, fromStore.longitude),
                        new kakao.maps.LatLng(toStore.latitude, toStore.longitude)
                    ];

                    var polyline = new kakao.maps.Polyline({
                        path: path,
                        strokeWeight: 2,
                        strokeColor: '#C9CDD2',
                        strokeOpacity: 0.55,
                        strokeStyle: 'solid'
                    });

                    polyline.setMap(map);
                });

                highlightPaths.forEach(function(pathInfo, idx) {
                    var pathNames = pathInfo.path_names || [];
                    var label = pathInfo.label || "추천 경로";

                    var coords = [];

                    pathNames.forEach(function(name) {
                        var store = storeByName[String(name)];

                        if (store) {
                            coords.push(
                                new kakao.maps.LatLng(store.latitude, store.longitude)
                            );
                        }
                    });

                    if (coords.length < 2) {
                        return;
                    }

                    var highlightLine = new kakao.maps.Polyline({
                        path: coords,
                        strokeWeight: 7,
                        strokeColor: '#FFD43B',
                        strokeOpacity: 0.95,
                        strokeStyle: 'solid'
                    });

                    highlightLine.setMap(map);

                    var info = new kakao.maps.InfoWindow({
                        content:
                            '<div style="padding:8px;font-size:13px;white-space:nowrap;background:#FFF8CC;">' +
                            '<b>' + label + '</b>' +
                            '</div>'
                    });

                    kakao.maps.event.addListener(highlightLine, 'mouseover', function(mouseEvent) {
                        info.setPosition(mouseEvent.latLng);
                        info.open(map);
                    });

                    kakao.maps.event.addListener(highlightLine, 'mouseout', function() {
                        info.close();
                    });
                });
            }
        </script>
    </body>
    </html>
    """

    html = html.replace("__KAKAO_KEY__", kakao_js_key)
    html = html.replace("__CENTER_LAT__", str(center_lat))
    html = html.replace("__CENTER_LNG__", str(center_lng))
    html = html.replace("__STORES_JSON__", stores_json)
    html = html.replace("__ROUTES_JSON__", routes_json)
    html = html.replace("__HIGHLIGHT_PATHS_JSON__", highlight_paths_json)

    return html


def show_kakao_map(stores, routes, kakao_js_key):
    html = create_kakao_map_html(stores, routes, kakao_js_key)
    components.html(html, height=720, scrolling=False)


def show_kakao_map_with_highlights(stores, routes, kakao_js_key, highlight_paths):
    html = create_kakao_map_html(stores, routes, kakao_js_key, highlight_paths)
    components.html(html, height=720, scrolling=False)


def show_kakao_map_with_truck(
    stores,
    routes,
    kakao_js_key,
    truck_path,
    speed_multiplier=1.0,
    inventory_changes=None,
):
    stores_data = stores.copy().dropna(subset=["latitude", "longitude"])
    routes_data = routes.copy()

    if stores_data.empty:
        components.html("<p>지도에 표시할 위치 데이터가 없습니다.</p>", height=200)
        return

    kakao_js_key = str(kakao_js_key).strip()
    speed_multiplier = float(speed_multiplier)
    inventory_changes = inventory_changes or {}

    center_lat = float(stores_data["latitude"].mean())
    center_lng = float(stores_data["longitude"].mean())

    stores_json = _records_json(stores_data)
    routes_json = _records_json(routes_data)
    truck_path_json = json.dumps(truck_path, ensure_ascii=False)
    inventory_changes_json = json.dumps(inventory_changes, ensure_ascii=False)

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
                font-family: Arial, sans-serif;
                color: #222;
            }

            #map {
                width: 100%;
                height: 580px;
                border-radius: 16px;
                border: 1px solid #dddddd;
            }

            #control-panel {
                margin-top: 12px;
                padding: 14px 16px;
                border: 1px solid #eadfba;
                border-radius: 16px;
                background: linear-gradient(135deg, #fffbea, #fff3bf);
                font-size: 15px;
            }

            #inventory-panel {
                margin-top: 14px;
                padding: 16px;
                border: 1px solid #e5e5e5;
                border-radius: 18px;
                background: #ffffff;
                box-shadow: 0 4px 14px rgba(0,0,0,0.06);
            }

            .truck-marker {
                width: 52px;
                height: 52px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                background: #fff3bf;
                border: 4px solid #ffd43b;
                box-shadow: 0 4px 12px rgba(0,0,0,0.28);
                font-size: 32px;
                transform: translate(-26px, -26px);
            }

            .dashboard-header {
                display: flex;
                justify-content: space-between;
                gap: 12px;
                align-items: center;
                margin-bottom: 14px;
                flex-wrap: wrap;
            }

            .dashboard-title {
                font-size: 20px;
                font-weight: 800;
            }

            .status-badge {
                padding: 8px 12px;
                border-radius: 999px;
                background: #fff3bf;
                border: 1px solid #ffd43b;
                font-weight: 700;
                font-size: 14px;
            }

            .inventory-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 14px;
            }

            .inventory-card {
                border: 1px solid #e9ecef;
                border-radius: 16px;
                padding: 16px;
                background: #fafafa;
            }

            .inventory-card.selected {
                border: 2px solid #ffd43b;
                background: #fffbea;
            }

            .store-name {
                font-size: 18px;
                font-weight: 800;
                margin-bottom: 4px;
            }

            .store-role {
                color: #666;
                font-size: 14px;
                margin-bottom: 12px;
            }

            .metric-row {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin-bottom: 14px;
            }

            .mini-metric {
                border-radius: 12px;
                background: white;
                padding: 10px;
                border: 1px solid #eeeeee;
                text-align: center;
            }

            .mini-label {
                font-size: 12px;
                color: #777;
                margin-bottom: 4px;
            }

            .mini-value {
                font-size: 18px;
                font-weight: 800;
            }

            .change-plus {
                color: #2b8a3e;
            }

            .change-minus {
                color: #c92a2a;
            }

            .bar-section {
                margin-top: 10px;
            }

            .bar-label {
                display: flex;
                justify-content: space-between;
                font-size: 13px;
                margin-bottom: 5px;
                color: #555;
            }

            .bar-track {
                width: 100%;
                height: 16px;
                border-radius: 999px;
                background: #e9ecef;
                overflow: hidden;
                margin-bottom: 10px;
            }

            .bar-before {
                height: 100%;
                background: #adb5bd;
                border-radius: 999px;
            }

            .bar-after {
                height: 100%;
                background: #228be6;
                border-radius: 999px;
            }

            .bar-current {
                height: 100%;
                background: #ffd43b;
                border-radius: 999px;
            }

            .summary-box {
                margin-top: 14px;
                padding: 12px;
                background: #f8f9fa;
                border-radius: 14px;
                border: 1px solid #e9ecef;
                line-height: 1.6;
            }

            button {
                padding: 8px 12px;
                margin-right: 6px;
                border: 1px solid #ddd;
                border-radius: 10px;
                background: white;
                cursor: pointer;
                font-weight: 600;
            }

            button:hover {
                background: #fff3bf;
            }
        </style>
    </head>

    <body>
        <div id="map"></div>

        <div id="control-panel">
            <b>🚚 Truck 이동 시뮬레이션</b><br>
            상태: <span id="truck-status">준비 중</span><br>
            현재 배속: <b><span id="speed-text">__SPEED__</span>x</b>
            <div style="margin-top:10px;">
                <button onclick="restartTruck()">처음부터 재생</button>
                <button onclick="pauseTruck()">일시정지</button>
                <button onclick="resumeTruck()">다시 재생</button>
            </div>
        </div>

        <div id="inventory-panel"></div>

        <script>
            var stores = __STORES_JSON__;
            var routes = __ROUTES_JSON__;
            var truckPath = __TRUCK_PATH_JSON__;
            var inventoryChanges = __INVENTORY_CHANGES_JSON__;
            var speedMultiplier = Number(__SPEED__);

            var map = null;
            var truckOverlay = null;
            var linePath = [];

            var segmentIndex = 0;
            var progress = 0;
            var animationTimer = null;
            var isPaused = false;
            var truckArrived = false;
            var selectedStoreName = null;

            var script = document.createElement('script');
            script.src = 'https://dapi.kakao.com/v2/maps/sdk.js?appkey=__KAKAO_KEY__&autoload=false';

            script.onload = function() {
                kakao.maps.load(function() {
                    initMap();
                });
            };

            script.onerror = function() {
                document.getElementById('truck-status').innerHTML = '카카오 SDK 로드 실패';
            };

            document.head.appendChild(script);

            function initMap() {
                var mapContainer = document.getElementById('map');

                var mapOption = {
                    center: new kakao.maps.LatLng(__CENTER_LAT__, __CENTER_LNG__),
                    level: 8
                };

                map = new kakao.maps.Map(mapContainer, mapOption);

                drawStoreMarkers();
                drawBaseRoutes();
                prepareTruckPath();
                renderInventoryDashboard();
            }

            function drawStoreMarkers() {
                stores.forEach(function(store) {
                    if (store.latitude == null || store.longitude == null) {
                        return;
                    }

                    var position = new kakao.maps.LatLng(store.latitude, store.longitude);

                    var marker = new kakao.maps.Marker({
                        map: map,
                        position: position
                    });

                    var storeName = store.store_name || store.name || "점포";
                    var storeType = store.type || "unknown";

                    var info = new kakao.maps.InfoWindow({
                        content:
                            '<div style="padding:10px 14px;font-size:15px;white-space:nowrap;">' +
                            '<b>' + storeName + '</b><br>' +
                            '유형: <b>' + storeType + '</b>' +
                            '</div>'
                    });

                    kakao.maps.event.addListener(marker, 'click', function() {
                        selectedStoreName = storeName;
                        info.open(map, marker);
                        renderInventoryDashboard();
                    });
                });
            }

            function drawBaseRoutes() {
                var storeCoord = {};

                stores.forEach(function(store) {
                    storeCoord[String(store.store_id)] = {
                        lat: store.latitude,
                        lng: store.longitude
                    };
                });

                routes.forEach(function(route) {
                    var fromId = String(route.from_id);
                    var toId = String(route.to_id);

                    if (!(fromId in storeCoord) || !(toId in storeCoord)) {
                        return;
                    }

                    var path = [
                        new kakao.maps.LatLng(storeCoord[fromId].lat, storeCoord[fromId].lng),
                        new kakao.maps.LatLng(storeCoord[toId].lat, storeCoord[toId].lng)
                    ];

                    var polyline = new kakao.maps.Polyline({
                        path: path,
                        strokeWeight: 2,
                        strokeColor: '#C9CDD2',
                        strokeOpacity: 0.45,
                        strokeStyle: 'solid'
                    });

                    polyline.setMap(map);
                });
            }

            function prepareTruckPath() {
                if (!truckPath || truckPath.length < 2) {
                    document.getElementById('truck-status').innerHTML = '추천 경로가 부족합니다.';
                    return;
                }

                linePath = truckPath.map(function(p) {
                    return new kakao.maps.LatLng(p.lat, p.lng);
                });

                var highlightLine = new kakao.maps.Polyline({
                    path: linePath,
                    strokeWeight: 7,
                    strokeColor: '#FFD43B',
                    strokeOpacity: 0.95,
                    strokeStyle: 'solid'
                });

                highlightLine.setMap(map);

                var bounds = new kakao.maps.LatLngBounds();

                linePath.forEach(function(pos) {
                    bounds.extend(pos);
                });

                map.setBounds(bounds);

                truckOverlay = new kakao.maps.CustomOverlay({
                    position: linePath[0],
                    content: '<div class="truck-marker">🚚</div>',
                    yAnchor: 0.5,
                    xAnchor: 0.5,
                    zIndex: 10
                });

                truckOverlay.setMap(map);

                truckArrived = false;
                document.getElementById('truck-status').innerHTML = '이동 중';

                startTruck();
            }

            function interpolate(start, end, ratio) {
                var lat = start.getLat() + (end.getLat() - start.getLat()) * ratio;
                var lng = start.getLng() + (end.getLng() - start.getLng()) * ratio;

                return new kakao.maps.LatLng(lat, lng);
            }

            function startTruck() {
                stopTruck();

                segmentIndex = 0;
                progress = 0;
                isPaused = false;
                truckArrived = false;

                if (truckOverlay && linePath.length > 0) {
                    truckOverlay.setPosition(linePath[0]);
                }

                renderInventoryDashboard();

                animationTimer = setInterval(function() {
                    if (isPaused) {
                        return;
                    }

                    if (segmentIndex >= linePath.length - 1) {
                        finishTruck();
                        return;
                    }

                    progress += 0.005 * speedMultiplier;

                    if (progress >= 1) {
                        progress = 0;
                        segmentIndex += 1;

                        if (segmentIndex >= linePath.length - 1) {
                            finishTruck();
                            return;
                        }
                    }

                    var nextPosition = interpolate(
                        linePath[segmentIndex],
                        linePath[segmentIndex + 1],
                        progress
                    );

                    truckOverlay.setPosition(nextPosition);
                }, 20);
            }

            function finishTruck() {
                stopTruck();

                if (truckOverlay && linePath.length > 0) {
                    truckOverlay.setPosition(linePath[linePath.length - 1]);
                }

                truckArrived = true;
                document.getElementById('truck-status').innerHTML = '도착 완료 - Inventory 반영됨';
                renderInventoryDashboard();
            }

            function stopTruck() {
                if (animationTimer !== null) {
                    clearInterval(animationTimer);
                    animationTimer = null;
                }
            }

            function restartTruck() {
                if (!truckOverlay || linePath.length < 2) {
                    return;
                }

                truckArrived = false;
                document.getElementById('truck-status').innerHTML = '이동 중';
                startTruck();
            }

            function pauseTruck() {
                isPaused = true;
                document.getElementById('truck-status').innerHTML = '일시정지';
            }

            function resumeTruck() {
                isPaused = false;
                document.getElementById('truck-status').innerHTML = '이동 중';
            }

            function getInventoryItems() {
                if (!inventoryChanges || !inventoryChanges.store_inventory) {
                    return [];
                }

                return Object.keys(inventoryChanges.store_inventory).map(function(storeName) {
                    var item = inventoryChanges.store_inventory[storeName];
                    item.store_name = storeName;
                    return item;
                });
            }

            function getMaxQty(items) {
                var maxQty = 1;

                items.forEach(function(item) {
                    maxQty = Math.max(maxQty, Number(item.before || 0));
                    maxQty = Math.max(maxQty, Number(item.after || 0));
                });

                return maxQty;
            }

            function pct(value, maxQty) {
                if (!maxQty || maxQty <= 0) {
                    return 0;
                }

                return Math.max(4, Math.min(100, (Number(value || 0) / maxQty) * 100));
            }

            function renderInventoryDashboard() {
                var panel = document.getElementById('inventory-panel');
                var items = getInventoryItems();

                if (items.length === 0) {
                    panel.innerHTML =
                        '<div class="dashboard-header">' +
                            '<div class="dashboard-title">📦 Inventory 변화 대시보드</div>' +
                        '</div>' +
                        '<div class="summary-box">Inventory 변화 데이터가 없습니다.</div>';
                    return;
                }

                var maxQty = getMaxQty(items);
                var truckStatusText = truckArrived ? 'Truck 도착 완료 / 이동 후 재고 반영' : 'Truck 이동 전 또는 이동 중 / 이동 전 재고 기준';

                var html = '';

                html += '<div class="dashboard-header">';
                html += '<div class="dashboard-title">📦 Inventory 변화 대시보드</div>';
                html += '<div class="status-badge">' + truckStatusText + '</div>';
                html += '</div>';

                html += '<div class="summary-box">';
                html += '상품명: <b>' + (inventoryChanges.product_name || '-') + '</b><br>';
                html += '이동 수량: <b>' + (inventoryChanges.move_qty || 0) + '개</b><br>';
                html += '경로: <b>' + (inventoryChanges.source_store || '-') + ' → ' + (inventoryChanges.target_store || '-') + '</b><br>';
                html += '추천 방식: <b>' + (inventoryChanges.recommended_path || '-') + '</b>';
                html += '</div>';

                html += '<div style="height:14px;"></div>';
                html += '<div class="inventory-grid">';

                items.forEach(function(item) {
                    var beforeQty = Number(item.before || 0);
                    var afterQty = Number(item.after || 0);
                    var changeQty = Number(item.change || 0);
                    var currentQty = truckArrived ? afterQty : beforeQty;

                    var changeClass = changeQty >= 0 ? 'change-plus' : 'change-minus';
                    var changeText = changeQty >= 0 ? '+' + changeQty : String(changeQty);

                    var selectedClass = selectedStoreName === item.store_name ? ' selected' : '';

                    html += '<div class="inventory-card' + selectedClass + '">';
                    html += '<div class="store-name">' + item.store_name + '</div>';
                    html += '<div class="store-role">' + item.role + ' / ' + item.product_name + '</div>';

                    html += '<div class="metric-row">';
                    html += '<div class="mini-metric">';
                    html += '<div class="mini-label">이동 전</div>';
                    html += '<div class="mini-value">' + beforeQty + '개</div>';
                    html += '</div>';

                    html += '<div class="mini-metric">';
                    html += '<div class="mini-label">이동 후</div>';
                    html += '<div class="mini-value">' + afterQty + '개</div>';
                    html += '</div>';

                    html += '<div class="mini-metric">';
                    html += '<div class="mini-label">변화량</div>';
                    html += '<div class="mini-value ' + changeClass + '">' + changeText + '개</div>';
                    html += '</div>';
                    html += '</div>';

                    html += '<div class="bar-section">';

                    html += '<div class="bar-label"><span>이동 전 재고</span><b>' + beforeQty + '개</b></div>';
                    html += '<div class="bar-track">';
                    html += '<div class="bar-before" style="width:' + pct(beforeQty, maxQty) + '%;"></div>';
                    html += '</div>';

                    html += '<div class="bar-label"><span>이동 후 재고</span><b>' + afterQty + '개</b></div>';
                    html += '<div class="bar-track">';
                    html += '<div class="bar-after" style="width:' + pct(afterQty, maxQty) + '%;"></div>';
                    html += '</div>';

                    html += '<div class="bar-label"><span>현재 반영 재고</span><b>' + currentQty + '개</b></div>';
                    html += '<div class="bar-track">';
                    html += '<div class="bar-current" style="width:' + pct(currentQty, maxQty) + '%;"></div>';
                    html += '</div>';

                    html += '</div>';
                    html += '</div>';
                });

                html += '</div>';

                html += '<div class="summary-box">';
                html += '마커를 클릭하면 해당 점포 카드가 노란색 테두리로 강조됩니다. ';
                html += 'Truck이 도착하면 현재 반영 재고가 이동 후 재고로 바뀝니다.';
                html += '</div>';

                panel.innerHTML = html;
            }
        </script>
    </body>
    </html>
    """

    html = html.replace("__KAKAO_KEY__", kakao_js_key)
    html = html.replace("__CENTER_LAT__", str(center_lat))
    html = html.replace("__CENTER_LNG__", str(center_lng))
    html = html.replace("__STORES_JSON__", stores_json)
    html = html.replace("__ROUTES_JSON__", routes_json)
    html = html.replace("__TRUCK_PATH_JSON__", truck_path_json)
    html = html.replace("__INVENTORY_CHANGES_JSON__", inventory_changes_json)
    html = html.replace("__SPEED__", str(speed_multiplier))

    components.html(html, height=1050, scrolling=True)