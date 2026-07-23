import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import StartPage from "./pages/StartPage";
import CaseSelectPage from "./pages/CaseSelectPage";
import GamePage from "./pages/GamePage";
import DeductionBoardPage from "./pages/DeductionBoardPage";
import RitualPage from "./pages/RitualPage";
import SaveLoadPage from "./pages/SaveLoadPage";
import EndingPage from "./pages/EndingPage";
import SettingsPage from "./pages/SettingsPage";
import TutorialPage from "./pages/TutorialPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<StartPage />} />
        <Route path="/tutorial" element={<TutorialPage />} />
        <Route path="/case-select" element={<CaseSelectPage />} />
        <Route path="/game" element={<GamePage />} />
        <Route path="/deduction" element={<DeductionBoardPage />} />
        <Route path="/ritual" element={<RitualPage />} />
        <Route path="/save-load" element={<SaveLoadPage />} />
        <Route path="/ending" element={<EndingPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
