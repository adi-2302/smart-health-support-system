import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, tokenStore, setUnauthorizedHandler } from "./api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(!!tokenStore.get());
  const [bootError, setBootError] = useState(null);
  const [attempt, setAttempt] = useState(0);

  const logout = useCallback(() => { tokenStore.clear(); setUser(null); setExam(null); }, []);

  useEffect(() => { setUnauthorizedHandler(logout); }, [logout]);

  useEffect(() => {
    if (!tokenStore.get()) { setLoading(false); return; }
    let cancelled = false;
    setLoading(true); setBootError(null);
    api.profile()
      .then((p) => { if (!cancelled) { setUser(p.user); setExam(p.exam); } })
      .catch((err) => {
        if (cancelled) return;
        // Only a 401 means the token is bad. A network error or server hiccup must not log the user out.
        if (err.status === 401) tokenStore.clear();
        else setBootError(err.message);
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [attempt]);

  const value = useMemo(() => ({
    user, exam, loading, bootError, retry: () => setAttempt((n) => n + 1), setExam, logout,
    async login(email, password) {
      const r = await api.login({ email, password });
      tokenStore.set(r.token);
      const p = await api.profile();
      setUser(p.user); setExam(p.exam);
    },
    async register(payload) {
      const r = await api.register(payload);
      tokenStore.set(r.token);
      setUser(r.user); setExam(r.exam);
    },
  }), [user, exam, loading, bootError, logout]);

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}
