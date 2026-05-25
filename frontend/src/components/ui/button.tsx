import * as React from "react";

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
}

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-2xl px-5 py-3 font-medium transition-all duration-200";

  const variants = {
    primary:
      "bg-sky-600 text-white shadow-sm hover:bg-sky-700 hover:shadow-md",
    secondary:
      "bg-white border border-slate-200 text-slate-900 hover:bg-slate-50",
    ghost:
      "text-slate-700 hover:bg-slate-100",
  };

  return (
    <button
      className={`${base} ${variants[variant]} ${className}`}
      {...props}
    />
  );
}