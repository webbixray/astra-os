'use client';

import { useState } from 'react';
import { useRAGSearch, useIngestBrandGuidelines } from '../api/useKnowledge';
import { RELEVANCE_COLORS, type SearchResult } from '../types';

interface RAGSearchProps {
  organizationId: string;
}

export function RAGSearch({ organizationId }: RAGSearchProps) {
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [showIngest, setShowIngest] = useState(false);

  const search = useRAGSearch(organizationId);

  const handleSearch = async () => {
    if (!query.trim()) return;
    const data = await search.mutateAsync({
      query: query.trim(),
      typeFilter: typeFilter || undefined,
      limit: 15,
    });
    setResults(data.results);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Knowledge Search (RAG)
        </h2>
        <button
          onClick={() => setShowIngest(!showIngest)}
          className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
        >
          {showIngest ? 'Close' : '+ Ingest Guidelines'}
        </button>
      </div>

      {/* Brand Guidelines Ingestion */}
      {showIngest && <BrandGuidelinesIngest organizationId={organizationId} />}

      {/* Search Bar */}
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search knowledge graph… (e.g., 'best performing audience for summer campaigns')"
          className="flex-1 rounded-md border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm"
        >
          <option value="">All Types</option>
          <option value="campaign">Campaigns</option>
          <option value="content">Content</option>
          <option value="brand">Brand</option>
          <option value="audience">Audiences</option>
          <option value="topic">Topics</option>
          <option value="channel">Channels</option>
        </select>
        <button
          onClick={handleSearch}
          disabled={search.isPending || !query.trim()}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800 disabled:opacity-50"
        >
          {search.isPending ? 'Searching…' : 'Search'}
        </button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500">
            {results.length} results found
          </p>
          {results.map((result) => (
            <SearchResultCard key={result.node_id} result={result} />
          ))}
        </div>
      )}

      {!search.isPending && results.length === 0 && query && (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
          <p className="text-sm text-gray-500">No results found for &ldquo;{query}&rdquo;</p>
        </div>
      )}
    </div>
  );
}

function SearchResultCard({ result }: { result: SearchResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="cursor-pointer rounded-lg border border-gray-200 bg-white p-4 transition hover:border-blue-200 hover:shadow-sm"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-900">
              {result.name}
            </span>
            <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
              {result.node_type}
            </span>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-600">
              {result.source}
            </span>
          </div>
          <p className="mt-1 text-sm text-gray-600 line-clamp-2">
            {result.description}
          </p>
        </div>
        <div className="ml-4 flex items-center gap-2">
          <span
            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
              RELEVANCE_COLORS[result.relevance] || ''
            }`}
          >
            {(result.score * 100).toFixed(0)}% — {result.relevance}
          </span>
        </div>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3 border-t border-gray-100 pt-3">
          <div>
            <h4 className="mb-1 text-xs font-medium uppercase text-gray-500">
              Full Description
            </h4>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">
              {result.description}
            </p>
          </div>
          {result.related_node_ids.length > 0 && (
            <div>
              <h4 className="mb-1 text-xs font-medium uppercase text-gray-500">
                Related Nodes
              </h4>
              <p className="text-sm text-gray-500">
                {result.related_node_ids.length} connected node(s)
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function BrandGuidelinesIngest({ organizationId }: { organizationId: string }) {
  const [name, setName] = useState('Brand Guidelines');
  const [text, setText] = useState('');
  const ingest = useIngestBrandGuidelines();

  const handleIngest = async () => {
    if (!text.trim()) return;
    await ingest.mutateAsync({
      organizationId,
      guidelinesText: text,
      name,
    });
    setText('');
  };

  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 space-y-3">
      <h3 className="text-sm font-medium text-gray-900">Ingest Brand Guidelines</h3>
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Guideline name"
        className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm"
      />
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste brand guidelines, voice & tone rules, dos and don'ts…"
        rows={6}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
      />
      <div className="flex items-center gap-3">
        <button
          onClick={handleIngest}
          disabled={ingest.isPending || !text.trim()}
          className="rounded-md bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {ingest.isPending ? 'Ingesting…' : 'Ingest'}
        </button>
        {ingest.isSuccess && (
          <span className="text-sm text-green-600">✓ Ingested successfully</span>
        )}
        {ingest.isError && (
          <span className="text-sm text-red-600">✗ Ingestion failed</span>
        )}
      </div>
    </div>
  );
}
