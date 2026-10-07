import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, tokenStore, setUnauthorizedHandler } from "./api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [exam, setExam] = useState(null);
  const [loading, setLoading] = useState(!!tokenStore.get());

  const logout = useCallback(() => { tokenStore.clear(); setUser(null); setExam(null); }, []);

  useEffect(() => { setUnauthorizedHandler(logout); }, [logout]);

  useEffect(() => {
    if (!tokenStore.get()) return;
    api.profile()
      .then((p) => { setUser(p.user); setExam(p.exam); })
      .catch(() => tokenStore.clear())
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(() => ({
    user, exam, loading, setExam, logout,
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
  }), [user, exam, loading, logout]);

  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}
