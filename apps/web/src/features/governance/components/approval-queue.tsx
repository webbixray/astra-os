'use client';

import { useState } from 'react';
import { usePendingApprovals, useDecideApproval } from '../api/useApprovals';
import {
  STATUS_COLORS,
} from '../types';

interface ApprovalQueueProps {
  organizationId: string;
  role?: string;
}

export function ApprovalQueue({ organizationId, role }: ApprovalQueueProps) {
  const { data, isLoading, error } = usePendingApprovals(organizationId, role);
  const decideMutation = useDecideApproval();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
        <span className="ml-3 text-gray-500">Loading approval queue…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
        Failed to load approval queue. Please try again.
      </div>
    );
  }

  const requests = data?.items || [];

  const handleDecide = async (
    requestId: string,
    action: 'approve' | 'reject',
  ) => {
    try {
      await decideMutation.mutateAsync({ requestId, action });
    } catch (err) {
      console.error('Decision failed:', err);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">
          Approval Queue
        </h2>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-medium text-amber-800">
          {requests.length} pending
        </span>
      </div>

      {requests.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center">
          <p className="text-gray-500">No pending approvals. All clear! 🎉</p>
        </div>
      ) : (
        <div className="space-y-3">
          {requests.map((request) => (
            <div
              key={request.id}
              className="rounded-lg border border-gray-200 bg-white shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-center justify-between p-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-gray-900">
                      {request.action_type}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[request.status] || 'bg-gray-100 text-gray-600'}`}
                    >
                      {request.status}
                    </span>
                  </div>
                  <p className="mt-1 text-sm text-gray-600">
                    {request.action_summary}
                  </p>
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-400">
                    <span>Role: {request.assigned_role}</span>
                    <span>
                      Created: {new Date(request.created_at).toLocaleString()}
                    </span>
                    {request.timeout_at && (
                      <span>
                        Expires: {new Date(request.timeout_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() =>
                      setExpandedId(
                        expandedId === request.id ? null : request.id,
                      )
                    }
                    className="rounded-md border border-gray-200 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
                  >
                    Details
                  </button>
                  <button
                    onClick={() => handleDecide(request.id, 'reject')}
                    disabled={decideMutation.isPending}
                    className="rounded-md border border-red-200 bg-white px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => handleDecide(request.id, 'approve')}
                    disabled={decideMutation.isPending}
                    className="rounded-md bg-green-600 px-3 py-1.5 text-sm text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    Approve
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
