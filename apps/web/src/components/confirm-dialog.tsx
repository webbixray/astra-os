'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface ConfirmDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'default' | 'destructive';
  onConfirm: () => void | Promise<void>;
  loading?: boolean;
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  loading = false,
}: ConfirmDialogProps) {
  const handleConfirm = async () => {
    await onConfirm();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            {cancelLabel}
          </Button>
          <Button
            variant={variant === 'destructive' ? 'destructive' : 'default'}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? 'Processing...' : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface UseConfirmDialogOptions {
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'default' | 'destructive';
}

export function useConfirmDialog(options: UseConfirmDialogOptions) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resolveConfirm, setResolveConfirm] = useState<((value: boolean) => void) | null>(null);

  const confirm = useCallback(() => {
    return new Promise<boolean>((resolve) => {
      setResolveConfirm(() => resolve);
      setOpen(true);
    });
  }, []);

  const handleConfirm = useCallback(async () => {
    setLoading(true);
    try {
      resolveConfirm?.(true);
    } finally {
      setLoading(false);
      setOpen(false);
      setResolveConfirm(null);
    }
  }, [resolveConfirm]);

  const handleCancel = useCallback(() => {
    resolveConfirm?.(false);
    setOpen(false);
    setResolveConfirm(null);
  }, [resolveConfirm]);

  const ConfirmDialogComponent = useCallback(
    () => (
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title={options.title}
        description={options.description}
        confirmLabel={options.confirmLabel}
        cancelLabel={options.cancelLabel}
        variant={options.variant}
        onConfirm={handleConfirm}
        loading={loading}
      />
    ),
    [open, options, handleConfirm, loading],
  );

  return {
    confirm,
    ConfirmDialog: ConfirmDialogComponent,
    isOpen: open,
  };
}
