import { Accessibility, Database, ExternalLink, LockKeyhole, ShieldCheck, UserRound } from "lucide-react";
import { useState, type FormEvent } from "react";
import { usePreferences } from "../components/AppProvider";
import { PageHeader } from "../components/PageHeader";
import { useApiQuery } from "../hooks/useApiQuery";
import type { HealthResponse } from "../types";

const sources = ["APOD Basic", "Near-Earth Object Web Service", "DONKI", "EONET v3", "NASA Image and Video Library"];

interface AuthSession {
  authenticated: boolean;
  development_identity_enabled: boolean;
  oidc_configured: boolean;
  user: { subject: string; is_development_identity: boolean } | null;
}

export function SettingsPage() {
  const { reducedMotion, setReducedMotion, developmentIdentity, setDevelopmentIdentity, setBearerToken } = usePreferences();
  const [identityDraft, setIdentityDraft] = useState(developmentIdentity);
  const [tokenDraft, setTokenDraft] = useState("");
  const [identityNotice, setIdentityNotice] = useState("");
  const health = useApiQuery<HealthResponse>("/health/ready");
  const auth = useApiQuery<AuthSession>("/api/v1/auth/session");
  const apiStatus = health.error ? "Unavailable" : health.pending ? "Checking" : health.data?.status === "ok" ? "Ready" : "Unknown";

  function applyIdentity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!/^[A-Za-z0-9._@-]{1,128}$/.test(identityDraft)) {
      setIdentityNotice("Use 1–128 letters, digits, dots, underscores, @ signs, or hyphens.");
      return;
    }
    setDevelopmentIdentity(identityDraft);
    setIdentityNotice(`Local identity set to ${identityDraft} for this tab.`);
    auth.refresh();
  }

  function applyToken(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBearerToken(tokenDraft);
    setTokenDraft("");
    setIdentityNotice(tokenDraft ? "OIDC access token is active in memory for this tab." : "OIDC access token cleared.");
    auth.refresh();
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="WORKSPACE / SETTINGS" title="Settings & disclosure" description="Adjust accessibility preferences and review how Cosmos handles its data sources." />
      <section className="panel settings-panel" aria-labelledby="accessibility-settings-title">
        <div className="settings-heading"><span className="settings-icon"><Accessibility size={19} aria-hidden="true" /></span><div><h2 id="accessibility-settings-title">Accessibility</h2><p>Choose how the interface uses motion on this device.</p></div></div>
        <label className="toggle-row" htmlFor="reduced-motion-toggle"><span><strong>Reduce motion</strong><small>Stop nonessential interface transitions and animations.</small></span><input id="reduced-motion-toggle" type="checkbox" checked={reducedMotion} onChange={(event) => setReducedMotion(event.target.checked)} /></label>
      </section>
      <section className="panel settings-panel" aria-labelledby="account-settings-title">
        <div className="settings-heading"><span className="settings-icon"><UserRound size={19} aria-hidden="true" /></span><div><h2 id="account-settings-title">Account and local testing</h2><p>Private saves and reports are scoped to the validated identity attached to each request.</p></div></div>
        {auth.pending && <p className="helper-copy">Checking the current sign-in mode…</p>}
        {auth.error && <p className="field-error" role="alert">{auth.error.message}</p>}
        {auth.data && <div className="privacy-status-row"><span>Session</span><span className={`status-value ${auth.data.authenticated ? "" : "status-value-error"}`}><i aria-hidden="true" />{auth.data.authenticated ? `Signed in as ${auth.data.user?.subject}` : "Not signed in"}</span></div>}
        <form className="settings-auth-form" onSubmit={applyIdentity}>
          <label className="field-label" htmlFor="dev-identity">Local development identity<input id="dev-identity" value={identityDraft} maxLength={128} pattern="[A-Za-z0-9._@-]{1,128}" onChange={(event) => setIdentityDraft(event.target.value)} autoComplete="off" /></label>
          <button className="button button-secondary" type="submit">Use this identity</button>
          <p className="helper-copy">The identity is sent only as a local test header. It works only when the backend explicitly enables development sign-in and is rejected by production configuration.</p>
        </form>
        <form className="settings-auth-form" onSubmit={applyToken}>
          <label className="field-label" htmlFor="oidc-token">OIDC access token for this tab<input id="oidc-token" type="password" value={tokenDraft} maxLength={8192} onChange={(event) => setTokenDraft(event.target.value)} autoComplete="off" spellCheck={false} /></label>
          <button className="button button-secondary" type="submit">Apply token</button>
          <p className="helper-copy">If the backend has OIDC configured, paste a short-lived access token here. It stays in browser memory and is never written to local storage. Submit an empty field to clear it.</p>
        </form>
        {identityNotice && <p className="helper-copy" role="status">{identityNotice}</p>}
      </section>
      <section className="panel settings-panel" aria-labelledby="source-settings-title">
        <div className="settings-heading"><span className="settings-icon settings-icon-cyan"><Database size={19} aria-hidden="true" /></span><div><h2 id="source-settings-title">Data sources</h2><p>Records keep their source identity, provenance link, and retrieval timestamp.</p></div></div>
        <div className="settings-source-list">{sources.map((source) => <div className="settings-source-row" key={source}><span><ShieldCheck size={15} aria-hidden="true" />{source}</span><span className="source-status"><i aria-hidden="true" /> Supported</span></div>)}</div>
        <a className="text-link settings-disclosure-link" href="https://api.nasa.gov/" target="_blank" rel="noreferrer">NASA API documentation <ExternalLink size={13} aria-hidden="true" /></a>
      </section>
      <section className="panel settings-panel" aria-labelledby="privacy-settings-title">
        <div className="settings-heading"><span className="settings-icon settings-icon-amber"><LockKeyhole size={19} aria-hidden="true" /></span><div><h2 id="privacy-settings-title">Service status and privacy</h2><p>Configuration values and API credentials are never sent to the browser.</p></div></div>
        <div className="privacy-status-row"><span>Application readiness</span><span className={`status-value ${health.error ? "status-value-error" : ""}`}><i aria-hidden="true" />{apiStatus}</span></div>
        <p className="helper-copy">This independent research project is not affiliated with NASA. NASA media may include third-party material; follow the rights and credit attached to each item.</p>
        <a className="text-link" href="https://www.nasa.gov/nasa-brand-center/images-and-media/" target="_blank" rel="noreferrer">NASA media usage guidelines <ExternalLink size={13} aria-hidden="true" /></a>
      </section>
    </div>
  );
}
