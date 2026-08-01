"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Plus, Wallet } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { PageHeader } from "@/components/layout/page-header";
import { IncomeForm, type IncomeFormValues } from "@/components/forms/IncomeForm";
import { IncomeTable } from "@/components/tables/IncomeTable";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useCreateIncome, useDeleteIncome, useUpdateIncome } from "@/hooks/useIncome";
import { can } from "@/lib/rbac";
import { ApiError } from "@/lib/api-client";
import type { Income } from "@/lib/types";

export default function IncomePage() {
  const { data: user } = useCurrentUser();
  const [formOpen, setFormOpen] = useState(false);
  const [editingIncome, setEditingIncome] = useState<Income | null>(null);
  const [deletingIncome, setDeletingIncome] = useState<Income | null>(null);

  const createIncome = useCreateIncome();
  const updateIncome = useUpdateIncome();
  const deleteIncome = useDeleteIncome();

  const canDelete = user ? can(user.role, "income:delete") : false;

  function openCreateDialog() {
    setEditingIncome(null);
    setFormOpen(true);
  }

  function openEditDialog(income: Income) {
    setEditingIncome(income);
    setFormOpen(true);
  }

  async function handleSubmit(values: IncomeFormValues) {
    try {
      if (editingIncome) {
        await updateIncome.mutateAsync({ id: editingIncome.id, values });
        toast.success("Income updated");
      } else {
        await createIncome.mutateAsync(values);
        toast.success("Income added");
      }
      setFormOpen(false);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  async function handleConfirmDelete() {
    if (!deletingIncome) return;
    try {
      await deleteIncome.mutateAsync(deletingIncome.id);
      toast.success("Income deleted");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setDeletingIncome(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Wallet}
        title="Income"
        description="Record and review every source of income."
        actions={
          <Button onClick={openCreateDialog}>
            <Plus className="size-4" />
            Add Income
          </Button>
        }
      />

      <IncomeTable canDelete={canDelete} onEdit={openEditDialog} onDelete={setDeletingIncome} />

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingIncome ? "Edit Income" : "Add Income"}</DialogTitle>
          </DialogHeader>
          <IncomeForm
            income={editingIncome ?? undefined}
            onSubmit={handleSubmit}
            onCancel={() => setFormOpen(false)}
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deletingIncome} onOpenChange={(open) => !open && setDeletingIncome(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this income entry?</AlertDialogTitle>
            <AlertDialogDescription>
              &ldquo;{deletingIncome?.source}&rdquo; will be removed from the ledger and dashboard
              totals. This cannot be undone from the UI.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmDelete}>Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
