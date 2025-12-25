'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Shield } from 'lucide-react'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    // Auto-redirect to dashboard after 2 seconds
    const timer = setTimeout(() => {
      router.push('/dashboard')
    }, 2000)
    return () => clearTimeout(timer)
  }, [router])

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center">
      <div className="text-center space-y-6">
        <div className="flex items-center justify-center gap-3">
          <Shield className="h-12 w-12 text-green-500" />
          <h1 className="text-4xl font-bold">AgentSudo</h1>
        </div>
        <p className="text-xl text-gray-400">
          The permission layer for AI agents
        </p>
        <div className="pt-8 space-y-4">
          <a
            href="/dashboard"
            className="inline-block px-6 py-3 bg-white text-black font-medium rounded-lg hover:bg-gray-200 transition"
          >
            Go to Dashboard
          </a>
          <p className="text-sm text-gray-500">
            Redirecting automatically...
          </p>
        </div>
        <div className="pt-12 text-sm text-gray-600">
          <p>Self-hosted instance</p>
          <a 
            href="https://github.com/xywa23/agentsudo" 
            className="text-green-500 hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </div>
  )
}
