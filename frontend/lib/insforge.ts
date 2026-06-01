import { createClient } from "@insforge/sdk";

const baseUrl = process.env.NEXT_PUBLIC_INSFORGE_URL;
const anonKey = process.env.NEXT_PUBLIC_INSFORGE_ANON_KEY;

export const isInsForgeConfigured = Boolean(baseUrl && anonKey);

export const insforge = isInsForgeConfigured
  ? createClient({
      baseUrl: baseUrl!,
      anonKey: anonKey!,
    })
  : null;

export const INVESTIGATIONS_TABLE = "investigations";
