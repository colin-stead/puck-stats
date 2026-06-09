import { BrowserRouter, Routes, Route } from 'react-router';
import { HomePage } from './components/HomePage';
import { PlayerDetail } from './components/PlayerDetail';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/player/:playerId" element={<PlayerDetail />} />
      </Routes>
    </BrowserRouter>
  );
}