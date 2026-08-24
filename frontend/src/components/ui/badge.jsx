import * as React from "react"
import { cva } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground shadow hover:bg-primary/90",
        secondary:
          "border-border/60 bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-rose-500/30 bg-rose-500/15 text-rose-700 dark:text-rose-300 dark:bg-rose-950/50 dark:border-rose-800",
        outline: "text-foreground border-border",
        success:
          "border-emerald-500/30 bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 dark:bg-emerald-950/50 dark:border-emerald-800 font-medium",
        warning:
          "border-amber-500/30 bg-amber-500/15 text-amber-800 dark:text-amber-300 dark:bg-amber-950/50 dark:border-amber-800 font-medium",
        info:
          "border-blue-500/30 bg-blue-500/15 text-blue-700 dark:text-blue-300 dark:bg-blue-950/50 dark:border-blue-800 font-medium",
        purple:
          "border-purple-500/30 bg-purple-500/15 text-purple-700 dark:text-purple-300 dark:bg-purple-950/50 dark:border-purple-800 font-medium",
        cyan:
          "border-cyan-500/30 bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 dark:bg-cyan-950/50 dark:border-cyan-800 font-medium",
        indigo:
          "border-indigo-500/30 bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 dark:bg-indigo-950/50 dark:border-indigo-800 font-medium",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({ className, variant, ...props }) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
