import { useState } from "react";
import type { DataState } from "../types/domain";

export function useMutationState<T>() {
  const [state, setState] = useState<DataState<T> | null>(null);
  return { state, pending: state?.status === "loading", setState, reset: () => setState(null) };
}
