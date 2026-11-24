import { useCallback, useEffect, useState } from "react";
import type { DataState } from "../types/domain";

export function useDataState<T>(load: () => Promise<DataState<T>>): [DataState<T>, () => void] {
  const [state, setState] = useState<DataState<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  const retry = useCallback(() => setAttempt((value) => value + 1), []);

  useEffect(() => {
    let active = true;
    setState({ status: "loading" });
    void load().then((nextState) => { if (active) setState(nextState); });
    return () => { active = false; };
  }, [attempt, load]);

  return [state, retry];
}
