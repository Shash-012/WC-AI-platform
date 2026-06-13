import { Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Home } from "@/pages/Home";
import { Scout } from "@/pages/Scout";
import { Groups } from "@/pages/Groups";
import { Fixtures } from "@/pages/Fixtures";
import { Teams } from "@/pages/Teams";
import { TeamDetail } from "@/pages/TeamDetail";
import { Predictor } from "@/pages/Predictor";
import { Sentiment } from "@/pages/Sentiment";
import { NotFound } from "@/pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/scout" element={<Scout />} />
        <Route path="/groups" element={<Groups />} />
        <Route path="/fixtures" element={<Fixtures />} />
        <Route path="/teams" element={<Teams />} />
        <Route path="/teams/:id" element={<TeamDetail />} />
        <Route path="/predictor" element={<Predictor />} />
        <Route path="/sentiment" element={<Sentiment />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
