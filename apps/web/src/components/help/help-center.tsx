'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface HelpArticle {
  id: string;
  title: string;
  description: string;
  category: string;
  icon: string;
  readTime: number;
  url: string;
}

interface HelpCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  articles: HelpArticle[];
}

interface HelpCenterProps {
  categories: HelpCategory[];
  className?: string;
}

export function HelpCenter({ categories, className }: HelpCenterProps) {
  const [search, setSearch] = useState('');

  const filteredCategories = categories
    .map((category) => ({
      ...category,
      articles: category.articles.filter(
        (article) =>
          article.title.toLowerCase().includes(search.toLowerCase()) ||
          article.description.toLowerCase().includes(search.toLowerCase()),
      ),
    }))
    .filter((category) => category.articles.length > 0 || !search);

  return (
    <div className={cn('space-y-8', className)}>
      <div className="text-center">
        <h1 className="text-3xl font-bold">Help Center</h1>
        <p className="mt-2 text-gray-500">Find answers to your questions</p>
        <div className="mx-auto mt-6 max-w-xl">
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <Input
              placeholder="Search for help..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {filteredCategories.map((category) => (
          <Card key={category.id}>
            <CardHeader>
              <div className="flex items-center gap-3">
                <span className="text-2xl">{category.icon}</span>
                <div>
                  <CardTitle className="text-lg">{category.name}</CardTitle>
                  <CardDescription>{category.description}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {category.articles.slice(0, 5).map((article) => (
                  <Link
                    key={article.id}
                    href={article.url}
                    className="flex items-center justify-between rounded-lg p-2 hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <div>
                      <div className="font-medium">{article.title}</div>
                      <div className="text-xs text-gray-500">{article.readTime} min read</div>
                    </div>
                    <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: string;
}

interface FAQSectionProps {
  faqs: FAQItem[];
  className?: string;
}

export function FAQSection({ faqs, className }: FAQSectionProps) {
  const [openId, setOpenId] = useState<string | null>(null);

  const groupedFaqs = faqs.reduce(
    (acc, faq) => {
      if (!acc[faq.category]) acc[faq.category] = [];
      acc[faq.category]!.push(faq);
      return acc;
    },
    {} as Record<string, FAQItem[]>,
  );

  return (
    <div className={cn('space-y-8', className)}>
      <div className="text-center">
        <h2 className="text-2xl font-bold">Frequently Asked Questions</h2>
        <p className="mt-2 text-gray-500">Quick answers to common questions</p>
      </div>

      {Object.entries(groupedFaqs).map(([category, items]) => (
        <div key={category}>
          <h3 className="mb-4 text-lg font-semibold">{category}</h3>
          <div className="space-y-3">
            {items.map((faq) => (
              <div key={faq.id} className="rounded-lg border">
                <button
                  className="flex w-full items-center justify-between p-4 text-left"
                  onClick={() => setOpenId(openId === faq.id ? null : faq.id)}
                >
                  <span className="font-medium">{faq.question}</span>
                  <svg
                    className={cn(
                      'h-5 w-5 text-gray-500 transition-transform',
                      openId === faq.id && 'rotate-180',
                    )}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openId === faq.id && (
                  <div className="border-t px-4 pb-4 pt-3 text-gray-600 dark:text-gray-400">
                    {faq.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

interface ContactSupportProps {
  className?: string;
}

export function ContactSupport({ className }: ContactSupportProps) {
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Contact Support</CardTitle>
        <CardDescription>Can't find what you're looking for? Get in touch.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Subject</label>
          <Input
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="How can we help?"
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Message</label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Describe your issue..."
            className="w-full rounded-md border px-3 py-2"
            rows={4}
          />
        </div>
        <Button className="w-full">Send Message</Button>
      </CardContent>
    </Card>
  );
}

interface QuickStartGuideProps {
  steps: { title: string; description: string; url: string; completed?: boolean }[];
  className?: string;
}

export function QuickStartGuide({ steps, className }: QuickStartGuideProps) {
  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Quick Start Guide</CardTitle>
        <CardDescription>Get up and running in minutes</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => (
            <div key={index} className="flex items-start gap-4">
              <div
                className={cn(
                  'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full',
                  step.completed ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-600',
                )}
              >
                {step.completed ? (
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{step.title}</span>
                  {step.completed && (
                    <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">
                      Done
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-500">{step.description}</p>
                {!step.completed && (
                  <Link href={step.url} className="mt-1 inline-block text-sm text-blue-600 hover:underline">
                    Get started →
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
