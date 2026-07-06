import { InputHTMLAttributes, forwardRef } from "react";
import { clsx } from "clsx";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, ...props }, ref) => {
    const inputId = id ?? props.name;

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-zinc-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={clsx(
            "h-10 w-full rounded-md border border-zinc-300 bg-white px-3 text-sm text-zinc-900",
            "placeholder:text-zinc-400",
            "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
            "disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-destructive focus:ring-destructive",
            className
          )}
          {...props}
        />
        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
    );
  }
);

Input.displayName = "Input";
