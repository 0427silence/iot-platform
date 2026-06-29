const API_BASE = "http://localhost:8000/api/v1";

async function apiGet(path) {
    const res = await fetch(`${API_BASE}${path}`);
    if (!res.ok) {
        throw new Error(`请求失败: ${res.status} ${res.statusText}`);
    }
    const json = await res.json();
    if (json.code !== 0) {
        throw new Error(json.message || "接口异常");
    }
    return json.data;
}

const API = {
    getDashboardSummary: () => apiGet("/dashboard/summary"),
    getOnlineDevices: () => apiGet("/dashboard/devices/online"),
    getDeviceList: () => apiGet("/devices"),
    getDeviceLatest: (deviceId) => apiGet(`/dashboard/devices/${deviceId}/latest`),
};
