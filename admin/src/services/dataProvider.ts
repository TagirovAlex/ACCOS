import { getToken } from "./api";

const API_BASE = "/api/v1/admin";

async function httpClient(url: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, {
    ...options,
    headers: { ...headers, "Content-Type": "application/json", ...(options.headers as Record<string, string>) },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`);
  return data;
}

function mapSettings(settings: any[]) {
  return (settings || []).map((s: any) => ({ id: s.key, ...s }));
}

function extractId(json: any, resource: string): string {
  const lookup = { groups: "group", users: "user" } as any;
  const key = lookup[resource];
  return json[key]?.id || json.id;
}

export const dataProvider: any = {
  getList: async (resource: string, params: any = {}) => {
    const { page = 1, perPage = 100 } = params.pagination || {};
    const skip = (page - 1) * perPage;
    const url = `${API_BASE}/${resource}?skip=${skip}&limit=${perPage}`;
    const json: any = await httpClient(url);
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
    const json = await httpClient(`${API_BASE}/${resource}`, {
      method: "POST", body: JSON.stringify(params.data),
    });
    const id = extractId(json, resource) || params.data.id;
    return { data: { ...json, ...params.data, id } };
  },
  update: async (resource: string, params: any) => {
    const url = resource === "settings"
      ? `${API_BASE}/settings/${params.id}`
      : `${API_BASE}/${resource}/${params.id}`;
    await httpClient(url, {
      method: "PUT", body: JSON.stringify(params.data),
    });
    return { data: { ...params.data, id: params.id } };
  },
  delete: async (resource: string, params: any) => {
    const url = resource === "settings"
      ? `${API_BASE}/settings/${params.id}`
      : `${API_BASE}/${resource}/${params.id}`;
    const data = await httpClient(url, { method: "DELETE" });
    if (data && data.success === false) throw new Error(data.error || "Delete failed");
    return { data: { id: params.id } };
  },
  getMany: async (resource: string, params: any) => {
    const { data } = await dataProvider.getList(resource);
    return { data: data.filter((item: any) => params.ids?.includes(item.id)) };
  },
  getManyReference: async (resource: string) => dataProvider.getList(resource),
  updateMany: async (resource: string, params: any) => {
    await Promise.all(
      (params.ids || []).map((id: string) => {
        const url = resource === "settings"
          ? `${API_BASE}/settings/${id}`
          : `${API_BASE}/${resource}/${id}`;
        return httpClient(url, { method: "PUT", body: JSON.stringify(params.data) });
      })
    );
    return { data: params.ids };
  },
  deleteMany: async (resource: string, params: any) => {
    await Promise.all(
      (params.ids || []).map(async (id: string) => {
        const url = resource === "settings"
          ? `${API_BASE}/settings/${id}`
          : `${API_BASE}/${resource}/${id}`;
        const data = await httpClient(url, { method: "DELETE" });
        if (data && data.success === false) throw new Error(data.error || "Delete failed");
      })
    );
    return { data: params.ids };
  },
};
