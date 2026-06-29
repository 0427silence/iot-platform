const STATUS_MAP = { 0: "离线", 1: "在线", 2: "故障" };
const STATUS_CLASS = { 0: "status-offline", 1: "status-online", 2: "status-fault" };

function updateTime() {
    const now = new Date();
    document.getElementById("headerTime").textContent = now.toLocaleString("zh-CN");
}

function formatValue(val, unit) {
    if (val == null || val === "") return "--";
    return `${val}${unit}`;
}

async function refreshSummary() {
    try {
        const data = await API.getDashboardSummary();
        document.getElementById("totalDevices").textContent = data.total_devices;
        document.getElementById("onlineCount").textContent = data.online_count;
        document.getElementById("offlineCount").textContent = data.offline_count;
        document.getElementById("faultCount").textContent = data.fault_count;
        document.getElementById("onlineRateFill").style.width = `${data.online_rate}%`;
        document.getElementById("onlineRateValue").textContent = `${data.online_rate}%`;
    } catch (e) {
        console.error("获取看板汇总失败:", e);
    }
}

async function refreshDeviceTable() {
    const tbody = document.getElementById("deviceTableBody");
    try {
        const devices = await API.getDeviceList();
        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-msg">暂无设备，请先注册设备</td></tr>';
            return;
        }

        const rows = await Promise.all(
            devices.map(async (d) => {
                let temp = "--", hum = "--", batt = "--";
                try {
                    const latest = await API.getDeviceLatest(d.device_id);
                    temp = formatValue(latest.temperature, "℃");
                    hum = formatValue(latest.humidity, "%");
                    batt = formatValue(latest.battery_level, "%");
                } catch (_) {}

                const lastOnline = d.last_online_at
                    ? new Date(d.last_online_at).toLocaleString("zh-CN")
                    : "--";

                return `<tr>
                    <td><code>${d.device_id}</code></td>
                    <td>${d.device_name}</td>
                    <td>${d.device_type}</td>
                    <td>${d.location || "--"}</td>
                    <td><span class="status-badge ${STATUS_CLASS[d.status] || "status-offline"}">${STATUS_MAP[d.status] ?? "未知"}</span></td>
                    <td>${temp}</td>
                    <td>${hum}</td>
                    <td>${batt}</td>
                    <td>${lastOnline}</td>
                </tr>`;
            })
        );

        tbody.innerHTML = rows.join("");
    } catch (e) {
        console.error("获取设备列表失败:", e);
        tbody.innerHTML = '<tr><td colspan="9" class="empty-msg">加载失败，请确认后端服务已启动</td></tr>';
    }
}

async function refreshAll() {
    updateTime();
    await Promise.all([refreshSummary(), refreshDeviceTable()]);
}

// 初始化
refreshAll();
setInterval(refreshAll, 30_000);
setInterval(updateTime, 1_000);
