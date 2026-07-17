'use client';

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

export interface Column<T> {
  id: string;
  header: string;
  accessorKey?: keyof T;
  accessorFn?: (row: T) => unknown;
  sortable?: boolean;
  filterable?: boolean;
  cell?: (row: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  pageSize?: number;
  searchable?: boolean;
  searchPlaceholder?: string;
  emptyMessage?: string;
  onRowClick?: (row: T) => void;
  className?: string;
}

type SortDirection = 'asc' | 'desc' | null;

export function DataTable<T extends { id?: string | number }>({
  columns,
  data,
  pageSize = 10,
  searchable = true,
  searchPlaceholder = 'Search...',
  emptyMessage = 'No data found',
  onRowClick,
  className,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [filters, _setFilters] = useState<Record<string, string>>({});

  const filteredData = useMemo(() => {
    let result = [...data];

    if (search) {
      const searchLower = search.toLowerCase();
      result = result.filter((row) =>
        columns.some((col) => {
          const value = col.accessorFn
            ? col.accessorFn(row)
            : col.accessorKey
              ? row[col.accessorKey]
              : null;
          return String(value || '').toLowerCase().includes(searchLower);
        }),
      );
    }

    Object.entries(filters).forEach(([columnId, filterValue]) => {
      if (filterValue) {
        result = result.filter((row) => {
          const col = columns.find((c) => c.id === columnId);
          if (!col) return true;
          const value = col.accessorFn
            ? col.accessorFn(row)
            : col.accessorKey
              ? row[col.accessorKey]
              : null;
          return String(value || '').toLowerCase().includes(filterValue.toLowerCase());
        });
      }
    });

    return result;
  }, [data, search, columns, filters]);

  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return filteredData;

    const col = columns.find((c) => c.id === sortColumn);
    if (!col) return filteredData;

    return [...filteredData].sort((a, b) => {
      const aVal = col.accessorFn ? col.accessorFn(a) : col.accessorKey ? a[col.accessorKey] : null;
      const bVal = col.accessorFn ? col.accessorFn(b) : col.accessorKey ? b[col.accessorKey] : null;

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [filteredData, sortColumn, sortDirection, columns]);

  const paginatedData = useMemo(() => {
    const start = currentPage * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const totalPages = Math.ceil(sortedData.length / pageSize);

  const handleSort = (columnId: string) => {
    if (sortColumn === columnId) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : prev === 'desc' ? null : 'asc'));
      if (sortDirection === 'desc') {
        setSortColumn(null);
      }
    } else {
      setSortColumn(columnId);
      setSortDirection('asc');
    }
  };

  const getCellValue = (row: T, column: Column<T>) => {
    if (column.cell) return column.cell(row);
    if (column.accessorFn) return column.accessorFn(row);
    if (column.accessorKey) return row[column.accessorKey];
    return null;
  };

  return (
    <div className={cn('space-y-4', className)}>
      {searchable && (
        <div className="flex items-center gap-2">
          <Input
            placeholder={searchPlaceholder}
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setCurrentPage(0);
            }}
            className="max-w-sm"
          />
        </div>
      )}

      <div className="overflow-hidden rounded-lg border">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.id}
                  className={cn(
                    'px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300',
                    column.sortable && 'cursor-pointer select-none hover:bg-gray-100 dark:hover:bg-gray-700',
                    column.className,
                  )}
                  onClick={() => column.sortable && handleSort(column.id)}
                >
                  <div className="flex items-center gap-2">
                    {column.header}
                    {column.sortable && sortColumn === column.id && (
                      <span className="text-blue-600 dark:text-blue-400">
                        {sortDirection === 'asc' ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-sm text-gray-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedData.map((row, rowIndex) => (
                <tr
                  key={row.id || rowIndex}
                  className={cn(
                    'hover:bg-gray-50 dark:hover:bg-gray-800/50',
                    onRowClick && 'cursor-pointer',
                  )}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column) => (
                    <td
                      key={column.id}
                      className={cn('px-4 py-3 text-sm', column.className)}
                    >
                      {getCellValue(row, column) as React.ReactNode}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {currentPage * pageSize + 1} to{' '}
            {Math.min((currentPage + 1) * pageSize, sortedData.length)} of {sortedData.length}{' '}
            results
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage === totalPages - 1}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
