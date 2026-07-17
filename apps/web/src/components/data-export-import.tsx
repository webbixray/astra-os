'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { LegacySelect as Select } from '@/components/ui/select';
import { api } from '@/lib/api';

type ExportFormat = 'csv' | 'json' | 'xlsx';

interface ExportOption {
  id: string;
  name: string;
  description: string;
}

const EXPORT_OPTIONS: ExportOption[] = [
  {
    id: 'campaigns',
    name: 'Campaigns',
    description: 'Export all campaigns with their settings and metrics',
  },
  {
    id: 'content',
    name: 'Content',
    description: 'Export all content items and templates',
  },
  {
    id: 'analytics',
    name: 'Analytics',
    description: 'Export analytics data and reports',
  },
  {
    id: 'contacts',
    name: 'Contacts',
    description: 'Export contact lists and segments',
  },
  {
    id: 'team',
    name: 'Team',
    description: 'Export team members and roles',
  },
];

export function DataExportImport() {
  const [exportType, setExportType] = useState('campaigns');
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv');
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    success: boolean;
    message: string;
    imported?: number;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExport = async () => {
    setExporting(true);
    try {
      const response = await fetch(
        `/api/v1/export/${exportType}?format=${exportFormat}`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) {
        throw new Error('Export failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `astra-${exportType}-${new Date().toISOString().split('T')[0]}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      alert('Failed to export data');
    } finally {
      setExporting(false);
    }
  };

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    setImportResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const result = await api.post<{
        success: boolean;
        message: string;
        imported: number;
      }>('/import', formData);

      setImportResult(result);
    } catch {
      setImportResult({
        success: false,
        message: 'Failed to import data. Please check the file format.',
      });
    } finally {
      setImporting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-medium">Export Data</h3>
        <p className="text-sm text-muted-foreground">
          Download your data in various formats
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <label className="text-sm font-medium">Data Type</label>
          <Select
            options={EXPORT_OPTIONS.map((opt) => ({
              value: opt.id,
              label: opt.name,
            }))}
            value={exportType}
            onChange={(e) => setExportType(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            {EXPORT_OPTIONS.find((opt) => opt.id === exportType)?.description}
          </p>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Format</label>
          <Select
            options={[
              { value: 'csv', label: 'CSV' },
              { value: 'json', label: 'JSON' },
              { value: 'xlsx', label: 'Excel (XLSX)' },
            ]}
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
          />
        </div>
      </div>

      <Button onClick={handleExport} disabled={exporting}>
        {exporting ? 'Exporting...' : 'Export Data'}
      </Button>

      <div className="border-t pt-8">
        <h3 className="text-lg font-medium">Import Data</h3>
        <p className="text-sm text-muted-foreground">
          Import data from CSV or JSON files
        </p>
      </div>

      <div className="rounded-lg border border-dashed p-8 text-center">
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.json,.xlsx"
          onChange={handleImport}
          className="hidden"
          id="import-file"
        />
        <label
          htmlFor="import-file"
          className="cursor-pointer"
        >
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <span className="text-2xl">+</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {importing
              ? 'Importing...'
              : 'Click to select a file or drag and drop'}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Supports CSV, JSON, and XLSX files
          </p>
        </label>
      </div>

      {importResult && (
        <div
          className={`rounded-lg border p-4 ${
            importResult.success
              ? 'border-green-500/50 bg-green-50 dark:bg-green-950'
              : 'border-red-500/50 bg-red-50 dark:bg-red-950'
          }`}
        >
          <p
            className={`font-medium ${
              importResult.success
                ? 'text-green-900 dark:text-green-100'
                : 'text-red-900 dark:text-red-100'
            }`}
          >
            {importResult.success ? 'Import Successful' : 'Import Failed'}
          </p>
          <p
            className={`mt-1 text-sm ${
              importResult.success
                ? 'text-green-700 dark:text-green-300'
                : 'text-red-700 dark:text-red-300'
            }`}
          >
            {importResult.message}
            {importResult.imported && ` (${importResult.imported} records imported)`}
          </p>
        </div>
      )}
    </div>
  );
}
