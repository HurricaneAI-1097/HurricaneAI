import { ButtonHTMLAttributes, forwardRef } from "react";
import { clsx } from "clsx";

export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "destructive";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary: "bg-primary text-primary-foreground hover:bg-primary-700",
  secondary: "bg-muted text-zinc-900 hover:bg-zinc-200",
  outline: "border border-zinc-300 bg-transparent hover:bg-zinc-50",
  ghost: "bg-transparent hover:bg-zinc-100",
  destructive: "bg-destructive text-destructive-foreground hover:bg-red-700",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-12 px-6 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { className, variant = "primary", size = "md", isLoading = false, disabled, children, ...props },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={clsx(
          "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {isLoading && (
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-hidden="true"
          />
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";
