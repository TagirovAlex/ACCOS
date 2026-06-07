import { getToken } from "./api";

const API_BASE = "/api/v1/admin";

async function httpClient(url: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, { ...options, headers: { ...headers, "Content-Type": "application/json", ...(options.headers as Record<string, string>) } });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
  return data;
}

function mapSettings(settings: any[]) {
  return (settings || []).map((s: any) => ({ id: s.key, ...s }));
}

export const dataProvider: any = {
  getList: async (resource: string) => {
    const json: any = await httpClient(`${API_BASE}/${resource}`);
    let data = json[resource] || [];
    if (resource === "settings") data = mapSettings(data);
    data = data.map((item: any) => ({ ...item, id: item.id ?? item.key }));
    return { data, total: data.length };
  },
  getOne: async (resource: string, params: any) => {
    if (resource === "settings") {
      const json = await httpClient(`${API_BASE}/settings`);
      const item = (json.settings || []).find((s: any) => s.key === params.id);
      if (!item) throw new Error("Setting not found");
      return { data: { id: item.key, ...item } };
    }
    const json = await httpClient(`${API_BASE}/${resource}/${params.id}`);
    return { data: { ...json, id: json.id } };
  },
  create: async (resource: string, params: any) => {
    const json = await httpClient(`${API_BASE}/${resource}`, { method: "POST", body: JSON.stringify(params.data) });
    const id = json.group?.id || json.id || params.data.id;
    return { data: { ...json, ...params.data, id } };
  },
  update: async (resource: string, params: any) => {
    await httpClient(`${API_BASE}/${resource}/${params.id}`, { method: "PUT", body: JSON.stringify(params.data) });
    return { data: { ...params.data, id: params.id } };
  },
  delete: async (resource: string, params: any) => {
    await httpClient(`${API_BASE}/${resource}/${params.id}`, { method: "DELETE" });
    return { data: { id: params.id } };
  },
  getMany: async (resource: string, params: any) => {
    const { data } = await dataProvider.getList(resource);
    return { data: data.filter((item: any) => params.ids.includes(item.id)) };
  },
  getManyReference: async (resource: string) => dataProvider.getList(resource),
  updateMany: async (resource: string, params: any) => {
    await Promise.all(params.ids.map((id: string) => httpClient(`${API_BASE}/${resource}/${id}`, { method: "PUT", body: JSON.stringify(params.data) })));
    return { data: params.ids };
  },
  deleteMany: async (resource: string, params: any) => {
    await Promise.all(params.ids.map((id: string) => httpClient(`${API_BASE}/${resource}/${id}`, { method: "DELETE" })));
    return { data: params.ids };
  },
};
