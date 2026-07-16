import { Outlet, NavLink } from 'react-router-dom'
import { Cpu, LayoutDashboard, Smartphone } from 'lucide-react'

export default function Layout() {
  return (
    <div className="min-h-screen bg-darkBg">
      <header className="border-b border-borderBg bg-cardBg/50 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <NavLink to="/" className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600/20 text-blue-500 rounded-lg">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-wider text-white">IoT Platform</h1>
            <p className="text-xs text-gray-400">Device Monitoring Dashboard</p>
          </div>
        </NavLink>
        <nav className="flex items-center space-x-4">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white'
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboard</span>
          </NavLink>
          <NavLink
            to="/devices"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600/20 text-blue-400' : 'text-gray-400 hover:text-white'
              }`
            }
          >
            <Smartphone className="w-4 h-4" />
            <span>Devices</span>
          </NavLink>
        </nav>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
