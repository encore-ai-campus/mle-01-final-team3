const contextKeys = ["demo", "role", "team"] as const;

export function withRouteContext(path: string, search: string): string {
  const current = new URLSearchParams(search);
  const context = new URLSearchParams();
  contextKeys.forEach((key) => {
    const value = current.get(key);
    if (value) context.set(key, value);
  });
  const query = context.toString();
  if (!query) return path;
  return `${path}${path.includes("?") ? "&" : "?"}${query}`;
}
