'use client'

import { useState } from 'react'
import Link from 'next/link'
import { ChevronRight, Zap, Code, Shield, ExternalLink, BookOpen, Target, ArrowUpRight, BarChart, LineChart, Activity, TrendingUp, Download, FileText, ChevronRight as ChevronRightIcon } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface DocSection {
  id: string
  title: string
  description: string
  icon: React.ReactNode
  href: string
  category: 'getting-started' | 'guides' | 'api' | 'advanced'
}

const ANALYTICS_SECTIONS: DocSection[] = [
  {
    id: 'overview',
    title: 'Analytics Overview',
    description: 'Understand your marketing performance at a glance',
    icon: <BarChart className="h-5 w-5" />,
    href: '/docs/analytics/overview',
    category: 'getting-started',
  },
  {
    id: 'dashboards',
    title: 'Custom Dashboards',
    description: 'Build personalized analytics dashboards',
    icon: <LineChart className="h-5 w-5" />,
    href: '/docs/analytics/dashboards',
    category: 'guides',
  },
  {
    id: 'reports',
    title: 'Automated Reports',
    description: 'Schedule and automate report delivery',
    icon: <FileText className="h-5 w-5" />,
    href: '/docs/analytics/reports',
    category: 'guides',
  },
  {
    id: 'roi-tracking',
    title: 'ROI Tracking',
    description: 'Measure and optimize your marketing ROI',
    icon: <TrendingUp className="h-5 w-5" />,
    href: '/docs/analytics/roi-tracking',
    category: 'guides',
  },
  {
    id: 'attribution',
    title: 'Attribution Modeling',
    description: 'Understand which channels drive conversions',
    icon: <Target className="h-5 w-5" />,
    href: '/docs/analytics/attribution',
    category: 'advanced',
  },
  {
    id: 'predictive',
    title: 'Predictive Analytics',
    description: 'Forecast trends with AI-powered predictions',
    icon: <Activity className="h-5 w-5" />,
    href: '/docs/analytics/predictive',
    category: 'advanced',
  },
  {
    id: 'api',
    title: 'Analytics API',
    description: 'Integrate analytics data into your applications',
    icon: <Code className="h-5 w-5" />,
    href: '/docs/analytics/api',
    category: 'api',
  },
  {
    id: 'webhooks',
    title: 'Webhook Integration',
    description: 'Real-time analytics data via webhooks',
    icon: <Zap className="h-5 w-5" />,
    href: '/docs/analytics/webhooks',
    category: 'api',
  },
  {
    id: 'export',
    title: 'Data Export',
    description: 'Export analytics data for external analysis',
    icon: <Download className="h-5 w-5" />,
    href: '/docs/analytics/export',
    category: 'api',
  },
]

const CATEGORIES = [
  { id: 'all', label: 'All' },
  { id: 'getting-started', label: 'Getting Started' },
  { id: 'guides', label: 'User Guides' },
  { id: 'api', label: 'API Reference' },
  { id: 'advanced', label: 'Advanced' },
]

export default function AnalyticsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState('all')

  const filteredSections = ANALYTICS_SECTIONS.filter((section) => {
    const matchesSearch = section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      section.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = activeCategory === 'all' || section.category === activeCategory
    return matchesSearch && matchesCategory
  })

  const groupedSections = filteredSections.reduce((acc, section) => {
    if (!acc[section.category]) {
      acc[section.category] = []
    }
    acc[section.category]!.push(section)
    return acc
  }, {} as Record<string, DocSection[]>)

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-72 bg-card border-r transition-all duration-300 lg:relative lg:translate-x-0">
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center justify-between border-b px-4">
            <Link href="/docs" className="flex items-center gap-2">
              <BookOpen className="h-6 w-6 text-primary" />
              <span className="font-semibold">Astra OS Docs</span>
            </Link>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <div className="mb-4">
              <Input
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />
            </div>

            <div className="space-y-2 mb-4">
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id)}
                  className={cn(
                    'w-full px-3 py-2 rounded-md text-sm font-medium transition-colors text-left',
                    activeCategory === cat.id
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            <div className="space-y-1">
              {Object.entries(groupedSections).filter(([, sections]) => sections.length > 0).map(([category, sections]) => (
                <div key={category} className="space-y-1">
                  <h3 className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {CATEGORIES.find(c => c.id === category)?.label}
                  </h3>
                  {sections.map((section) => (
                    <Link
                      key={section.id}
                      href={section.href}
                      className="flex items-center gap-3 px-3 py-2 rounded-md text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
                    >
                      <span className="flex h-5 w-5 items-center justify-center text-muted-foreground">
                        {section.icon}
                      </span>
                      <span className="flex-1 truncate">{section.title}</span>
                      <ChevronRightIcon className="h-4 w-4 text-muted-foreground" />
                    </Link>
                  ))}
                </div>
              ))}
              <div className="border-t p-4 mt-4">
                <a
                  href="https://github.com/webbixray/astra-os"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 hover:text-primary"
                >
                  <ExternalLink className="h-3 w-3" />
                  View on GitHub
                </a>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar toggle */}
      <button
        className="lg:hidden fixed bottom-4 right-4 z-50 rounded-full bg-primary p-3 text-primary-foreground shadow-lg"
      >
        <BookOpen className="h-5 w-5" />
      </button>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto transition-all duration-300 lg:ml-72">
        <div className="max-w-4xl mx-auto p-8">
          <div className="mb-8">
            <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
              <Link href="/dashboard" className="hover:text-foreground">Dashboard</Link>
              <ChevronRightIcon className="h-4 w-4" />
              <Link href="/docs" className="hover:text-foreground">Documentation</Link>
              <ChevronRightIcon className="h-4 w-4" />
              <span>Analytics & Reporting</span>
            </nav>
            <h1 className="text-3xl font-bold tracking-tight">Analytics & Reporting</h1>
            <p className="mt-2 text-muted-foreground text-lg">
              Track performance, measure ROI, and make data-driven decisions.
            </p>
          </div>

          <div className="space-y-8">
            {Object.entries(groupedSections).filter(([, sections]) => sections.length > 0).map(([category, sections]) => (
              <div key={category}>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold capitalize">{CATEGORIES.find(c => c.id === category)?.label}</h2>
                  <span className="text-sm text-muted-foreground">{sections.length} articles</span>
                </div>
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {sections.map((section) => (
                    <Link
                      key={section.id}
                      href={section.href}
                      className="group flex flex-col p-6 bg-card border rounded-xl hover:border-primary/50 hover:shadow-lg transition-all duration-200"
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
                          {section.icon}
                        </div>
                        <span className="text-xs font-medium text-primary uppercase tracking-wider">
                          {CATEGORIES.find(c => c.id === category)?.label}
                        </span>
                      </div>
                      <h3 className="font-semibold text-lg mb-2 group-hover:text-primary transition-colors">
                        {section.title}
                      </h3>
                      <p className="text-sm text-muted-foreground mb-4 flex-1">
                        {section.description}
                      </p>
                      <div className="flex items-center justify-between pt-4 border-t">
                        <span className="text-sm font-medium text-primary group-hover:text-primary/80 transition-colors">
                          Read more
                        </span>
                        <ChevronRightIcon className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}

            {/* Quick Links */}
            <div className="mt-12 rounded-xl border bg-muted/30 p-6">
              <h2 className="text-lg font-semibold mb-4">Quick Links</h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Link href="/docs/quickstart" className="flex items-center gap-3 p-4 rounded-lg border hover:bg-accent transition-colors">
                  <Zap className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">Quick Start</p>
                    <p className="text-sm text-muted-foreground">5-minute setup guide</p>
                  </div>
                </Link>
                <Link href="/docs/api-reference" className="flex items-center gap-3 p-4 rounded-lg border hover:bg-accent transition-colors">
                  <Code className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">API Reference</p>
                    <p className="text-sm text-muted-foreground">Complete endpoint docs</p>
                  </div>
                </Link>
                <Link href="/docs/best-practices" className="flex items-center gap-3 p-4 rounded-lg border hover:bg-accent transition-colors">
                  <Zap className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">Best Practices</p>
                    <p className="text-sm text-muted-foreground">Tips for success</p>
                  </div>
                </Link>
                <Link href="https://github.com/webbixray/astra-os" target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 p-4 rounded-lg border hover:bg-accent transition-colors">
                  <ExternalLink className="h-5 w-5 text-primary" />
                  <div>
                    <p className="font-medium">GitHub Repository</p>
                    <p className="text-sm text-muted-foreground">Source code & issues</p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}