import { api, uploadFile } from "./api";

export async function getProfile(): Promise<any> {
  return api("GET", "/user/profile");
}

export async function updateProfile(data: {
  default_system_prompt?: string;
  full_name?: string;
  email?: string;
}): Promise<any> {
  return api("PUT", "/user/profile", data);
}

export async function uploadAvatar(file: File): Promise<any> {
  return uploadFile("/user/avatar", file);
}
