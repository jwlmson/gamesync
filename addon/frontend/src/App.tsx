import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import DashboardScreen from './screens/DashboardScreen';
import TeamManagementScreen from './screens/TeamManagementScreen';
import TeamDiscoveryScreen from './screens/TeamDiscoveryScreen';
import TeamConfigurationScreen from './screens/TeamConfigurationScreen';
import GameBrowserScreen from './screens/GameBrowserScreen';
import GameOverrideEditorScreen from './screens/GameOverrideEditorScreen';
import EffectTesterScreen from './screens/EffectTesterScreen';
import SoundLibraryScreen from './screens/SoundLibraryScreen';
import SettingsScreen from './screens/SettingsScreen';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardScreen />} />
          <Route path="/teams" element={<TeamManagementScreen />} />
          <Route path="/teams/discover" element={<TeamDiscoveryScreen />} />
          <Route path="/teams/:teamId/config" element={<TeamConfigurationScreen />} />
          <Route path="/games" element={<GameBrowserScreen />} />
          <Route path="/games/:gameId/override" element={<GameOverrideEditorScreen />} />
          <Route path="/effects" element={<EffectTesterScreen />} />
          <Route path="/sounds" element={<SoundLibraryScreen />} />
          <Route path="/settings" element={<SettingsScreen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
