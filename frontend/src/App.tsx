import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { AppProvider } from "./components/AppProvider";
import { LoadingState } from "./components/StatePanel";
import { AssistantPage } from "./pages/AssistantPage";
import { AstronomyPage } from "./pages/AstronomyPage";
import { EarthEventsPage } from "./pages/EarthEventsPage";
import { MediaPage } from "./pages/MediaPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SavedRecordsPage } from "./pages/SavedRecordsPage";
import { SettingsPage } from "./pages/SettingsPage";

const SpaceWeatherPage = lazy(() => import("./pages/SpaceWeatherPage").then((module) => ({ default: module.SpaceWeatherPage })));
const AsteroidsPage = lazy(() => import("./pages/AsteroidsPage").then((module) => ({ default: module.AsteroidsPage })));

export function App() {
  return (
    <AppProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="astronomy" element={<AstronomyPage />} />
          <Route path="asteroids" element={<Suspense fallback={<LoadingState label="Loading asteroid distance map…" />}><AsteroidsPage /></Suspense>} />
          <Route path="space-weather" element={<Suspense fallback={<LoadingState label="Loading space-weather monitor…" />}><SpaceWeatherPage /></Suspense>} />
          <Route path="earth-events" element={<EarthEventsPage />} />
          <Route path="media" element={<MediaPage />} />
          <Route path="assistant" element={<AssistantPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="saved" element={<SavedRecordsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </AppProvider>
  );
}
