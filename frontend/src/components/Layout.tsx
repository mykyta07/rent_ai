import { Outlet } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { Sparkles } from 'lucide-react'
import { Navbar } from './Navbar'
import { Footer } from './Footer'

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col bg-surface">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <Link
        to="/ai/chat"
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lg shadow-brand/30 transition-transform hover:scale-105"
        aria-label="Відкрити AI чат"
      >
        <Sparkles className="h-6 w-6" />
        <span className="absolute -right-0.5 -top-0.5 h-3 w-3 rounded-full bg-accent ring-2 ring-white" />
      </Link>
    </div>
  )
}
