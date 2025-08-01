import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Database from './pages/Database'
import Scrapers from './pages/Scrapers'
import Scheduling from './pages/Scheduling'
import Monitoring from './pages/Monitoring'
import Settings from './pages/Settings'
import Progress from './pages/Progress'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/database" element={<Database />} />
        <Route path="/scrapers" element={<Scrapers />} />
        <Route path="/scheduling" element={<Scheduling />} />
        <Route path="/monitoring" element={<Monitoring />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App