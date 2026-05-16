import { Routes, Route } from 'react-router-dom';
import HomePage from './components/HomePage/HomePage';
import ToolPage from './components/ToolPage/ToolPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/tools/:toolId" element={<ToolPage />} />
    </Routes>
  );
}

export default App;
