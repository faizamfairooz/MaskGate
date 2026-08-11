import React from 'react'
import { Link, useLocation } from 'react-router-dom'

function Layout({ children }) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/schema', label: 'Schema Browser' },
    { path: '/masking', label: 'Masking Policies' },
    { path: '/query', label: 'Query Editor' }
  ]

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>MaskGate</h1>
        </div>
        <ul className="nav-links">
          {navItems.map(item => (
            <li key={item.path}>
              <Link 
                to={item.path} 
                className={location.pathname === item.path ? 'active' : ''}
              >
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

export default Layout
