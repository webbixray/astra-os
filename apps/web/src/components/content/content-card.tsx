'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { StatusBadge } from '@/components/status-indicator';
import { EmptyContentState } from '@/components/empty-state';
import { cn } from '@/lib/utils';

interface Content {
  id: string;
  title: string;
  type: 'blog' | 'social' | 'email' | 'video' | 'podcast';
  status: 'draft' | 'review' | 'published' | 'archived';
  author: string;
  authorAvatar?: string;
  publishedAt?: string;
  updatedAt: string;
  tags: string[];
  excerpt?: string;
  readTime?: number;
  views?: number;
  engagement?: number;
}

interface ContentCardProps {
  content: Content;
  onEdit?: (content: Content) => void;
  onDelete?: (content: Content) => void;
  className?: string;
}

export function ContentCard({ content, onEdit, className }: ContentCardProps) {
  const typeIcons: Record<Content['type'], string> = {
    blog: '📝',
    social: '📱',
    email: '📧',
    video: '🎬',
    podcast: '🎙️',
  };

  return (
    <Card className={cn('transition-shadow hover:shadow-md', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-lg">{typeIcons[content.type]}</span>
              <CardTitle className="text-lg">{content.title}</CardTitle>
            </div>
            <CardDescription className="flex items-center gap-2">
              <span className="capitalize">{content.type}</span>
              <span>·</span>
              <span>{content.readTime} min read</span>
            </CardDescription>
          </div>
          <StatusBadge status={content.status as 'active' | 'inactive' | 'pending' | 'error' | 'success' | 'warning' | 'info'} />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {content.excerpt && (
          <p className="line-clamp-2 text-sm text-gray-600 dark:text-gray-400">
            {content.excerpt}
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          {content.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {content.tags.length > 3 && (
            <Badge variant="secondary" className="text-xs">
              +{content.tags.length - 3}
            </Badge>
          )}
        </div>

        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded-full bg-gray-200 dark:bg-gray-700" />
            <span>{content.author}</span>
          </div>
          <div className="flex items-center gap-4">
            {content.views !== undefined && (
              <span>{content.views.toLocaleString()} views</span>
            )}
            {content.engagement !== undefined && (
              <span>{content.engagement}% engagement</span>
            )}
          </div>
        </div>

        <div className="flex gap-2 pt-2">
          <Button asChild variant="outline" size="sm" className="flex-1">
            <Link href={`/content/${content.id}`}>View</Link>
          </Button>
          {onEdit && (
            <Button variant="ghost" size="sm" onClick={() => onEdit(content)}>
              Edit
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface ContentListProps {
  content: Content[];
  onCreateContent?: () => void;
  onEdit?: (content: Content) => void;
  onDelete?: (content: Content) => void;
  className?: string;
}

export function ContentList({ content, onCreateContent, onEdit, onDelete, className }: ContentListProps) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');

  const filteredContent = content.filter((item) => {
    const matchesSearch = item.title.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || item.status === statusFilter;
    const matchesType = typeFilter === 'all' || item.type === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  if (content.length === 0) {
    return <EmptyContentState onCreateContent={onCreateContent} />;
  }

  return (
    <div className={cn('space-y-6', className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold">Content</h2>
        {onCreateContent && (
          <Button onClick={onCreateContent}>
            <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Create Content
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Input
          placeholder="Search content..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="sm:w-[300px]"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
            <SelectItem value="review">In Review</SelectItem>
            <SelectItem value="published">Published</SelectItem>
            <SelectItem value="archived">Archived</SelectItem>
          </SelectContent>
        </Select>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-full sm:w-[150px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="blog">Blog</SelectItem>
            <SelectItem value="social">Social</SelectItem>
            <SelectItem value="email">Email</SelectItem>
            <SelectItem value="video">Video</SelectItem>
            <SelectItem value="podcast">Podcast</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filteredContent.map((item) => (
          <ContentCard
            key={item.id}
            content={item}
            onEdit={onEdit}
            onDelete={onDelete}
          />
        ))}
      </div>

      {filteredContent.length === 0 && (
        <div className="py-12 text-center text-gray-500">
          No content matches your filters.
        </div>
      )}
    </div>
  );
}

interface ContentCalendarProps {
  content: Content[];
  className?: string;
}

export function ContentCalendar({ content, className }: ContentCalendarProps) {
  const publishedContent = content
    .filter((item) => item.publishedAt)
    .sort((a, b) => new Date(a.publishedAt!).getTime() - new Date(b.publishedAt!).getTime());

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Content Calendar</CardTitle>
        <CardDescription>Upcoming and recent publications</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {publishedContent.map((item) => (
            <div key={item.id} className="flex items-start gap-4">
              <div className="flex-shrink-0 text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {new Date(item.publishedAt!).getDate()}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(item.publishedAt!).toLocaleDateString('en-US', { month: 'short' })}
                </div>
              </div>
              <div className="flex-1">
                <div className="font-medium">{item.title}</div>
                <div className="text-sm text-gray-500">
                  {item.type} · {item.author}
                </div>
              </div>
              <StatusBadge status={item.status as 'active' | 'inactive' | 'pending' | 'error' | 'success' | 'warning' | 'info'} />
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
