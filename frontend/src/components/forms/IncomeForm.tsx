"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { Income } from "@/lib/types";

// `amount` stays a string end-to-end (form -> JSON -> Pydantic Decimal), same
// rationale as ExpenseForm: avoids float round-tripping on financial values
// and the z.coerce/RHF generic inference mismatch.
export const incomeFormSchema = z.object({
  source: z.string().min(1, "Source is required").max(255),
  amount: z
    .string()
    .min(1, "Amount is required")
    .refine((v) => !Number.isNaN(Number(v)), "Amount must be a number")
    .refine((v) => Number(v) > 0, "Amount must be greater than 0"),
  date: z.string().min(1, "Date is required"),
  description: z.string().optional(),
});

export type IncomeFormValues = z.infer<typeof incomeFormSchema>;

interface IncomeFormProps {
  income?: Income;
  onSubmit: (values: IncomeFormValues) => Promise<void>;
  onCancel?: () => void;
  submitLabel?: string;
}

export function IncomeForm({ income, onSubmit, onCancel, submitLabel }: IncomeFormProps) {
  const form = useForm<IncomeFormValues>({
    resolver: zodResolver(incomeFormSchema),
    defaultValues: {
      source: income?.source ?? "",
      amount: income?.amount ?? "",
      date: income?.date ?? "",
      description: income?.description ?? "",
    },
  });

  async function handleSubmit(values: IncomeFormValues) {
    await onSubmit(values);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4" noValidate>
        <FormField
          control={form.control}
          name="source"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Source</FormLabel>
              <FormControl>
                <Input placeholder="Client Invoice #1042" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="amount"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Amount</FormLabel>
              <FormControl>
                <Input type="number" step="0.01" min="0" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="date"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Date</FormLabel>
              <FormControl>
                <Input type="date" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea rows={3} {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-2">
          {onCancel ? (
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          ) : null}
          <Button type="submit" disabled={form.formState.isSubmitting}>
            {form.formState.isSubmitting
              ? "Saving…"
              : (submitLabel ?? (income ? "Save changes" : "Add income"))}
          </Button>
        </div>
      </form>
    </Form>
  );
}
