"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Plus, Receipt } from "lucide-react";

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
import { ExpenseForm, type ExpenseFormValues } from "@/components/forms/ExpenseForm";
import { ExpenseTable } from "@/components/tables/ExpenseTable";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useCreateExpense, useDeleteExpense, useUpdateExpense } from "@/hooks/useExpenses";
import { can } from "@/lib/rbac";
import { ApiError } from "@/lib/api-client";
import type { Expense } from "@/lib/types";

export default function ExpensesPage() {
  const { data: user } = useCurrentUser();
  const [formOpen, setFormOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<Expense | null>(null);
  const [deletingExpense, setDeletingExpense] = useState<Expense | null>(null);

  const createExpense = useCreateExpense();
  const updateExpense = useUpdateExpense();
  const deleteExpense = useDeleteExpense();

  const canDelete = user ? can(user.role, "expenses:delete") : false;

  function openCreateDialog() {
    setEditingExpense(null);
    setFormOpen(true);
  }

  function openEditDialog(expense: Expense) {
    setEditingExpense(expense);
    setFormOpen(true);
  }

  async function handleSubmit(values: ExpenseFormValues) {
    try {
      if (editingExpense) {
        await updateExpense.mutateAsync({ id: editingExpense.id, values });
        toast.success("Expense updated");
      } else {
        await createExpense.mutateAsync(values);
        toast.success("Expense added");
      }
      setFormOpen(false);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong");
    }
  }

  async function handleConfirmDelete() {
    if (!deletingExpense) return;
    try {
      await deleteExpense.mutateAsync(deletingExpense.id);
      toast.success("Expense deleted");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setDeletingExpense(null);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        icon={Receipt}
        title="Expenses"
        description="Track and manage every business expense."
        actions={
          <Button onClick={openCreateDialog}>
            <Plus className="size-4" />
            Add Expense
          </Button>
        }
      />

      <ExpenseTable canDelete={canDelete} onEdit={openEditDialog} onDelete={setDeletingExpense} />

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingExpense ? "Edit Expense" : "Add Expense"}</DialogTitle>
          </DialogHeader>
          <ExpenseForm
            expense={editingExpense ?? undefined}
            onSubmit={handleSubmit}
            onCancel={() => setFormOpen(false)}
          />
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deletingExpense} onOpenChange={(open) => !open && setDeletingExpense(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this expense?</AlertDialogTitle>
            <AlertDialogDescription>
              &ldquo;{deletingExpense?.title}&rdquo; will be removed from the ledger and dashboard
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
