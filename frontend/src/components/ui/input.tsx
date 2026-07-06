import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground shadow-sm transition placeholder:text-foreground/40 focus-visible:ring-primary",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
