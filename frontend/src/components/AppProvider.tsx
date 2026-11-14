import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { setApiBearerToken } from "../api/client";

interface Preferences {
  reducedMotion: boolean;
  setReducedMotion: (value: boolean) => void;
  developmentIdentity: string;
  setDevelopmentIdentity: (value: string) => void;
  setBearerToken: (value: string) => void;
}

const PreferencesContext = createContext<Preferences | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [reducedMotion, setReducedMotion] = useState(() => {
    try {
      return window.localStorage.getItem("cosmos-reduced-motion") === "true";
    } catch {
      return false;
    }
  });
  const [developmentIdentity, setDevelopmentIdentityState] = useState(() => {
    try {
      return window.sessionStorage.getItem("cosmos-dev-user") || "local-developer";
    } catch {
      return "local-developer";
    }
  });
  const [bearerToken, setBearerTokenState] = useState("");
  useEffect(() => {
    try {
      window.localStorage.setItem("cosmos-reduced-motion", String(reducedMotion));
    } catch {
      // The preference remains active for this session when storage is unavailable.
    }
  }, [reducedMotion]);
  useEffect(() => {
    try {
      window.sessionStorage.setItem("cosmos-dev-user", developmentIdentity);
    } catch {
      // The development identity remains active for this session if storage is unavailable.
    }
  }, [developmentIdentity]);
  useEffect(() => setApiBearerToken(bearerToken), [bearerToken]);
  const setDevelopmentIdentity = (value: string) => {
    if (/^[A-Za-z0-9._@-]{1,128}$/.test(value)) {
      setDevelopmentIdentityState(value);
      try {
        window.sessionStorage.setItem("cosmos-dev-user", value);
      } catch {
        // The development identity remains active for this session if storage is unavailable.
      }
    }
  };
  const setBearerToken = (value: string) => {
    const token = value.trim();
    setBearerTokenState(token);
    setApiBearerToken(token);
  };
  const value = useMemo(
    () => ({ reducedMotion, setReducedMotion, developmentIdentity, setDevelopmentIdentity, setBearerToken }),
    [reducedMotion, developmentIdentity],
  );

  return (
    <PreferencesContext.Provider value={value}>
      <div className={reducedMotion ? "app-root reduce-motion" : "app-root"}>{children}</div>
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const value = useContext(PreferencesContext);
  if (!value) throw new Error("usePreferences must be used inside AppProvider.");
  return value;
}
