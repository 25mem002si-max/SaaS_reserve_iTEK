import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
}

export default function Button({
  variant = "primary",
  className,
  ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        "rounded-lg px-4 py-2 text-sm font-medium transition",
        variant === "primary" && "bg-primary text-white hover:bg-primary-light",
        variant === "secondary" && "bg-gray-100 text-gray-800 hover:bg-gray-200",
        variant === "danger" && "bg-danger text-white hover:bg-red-700",
        className
      )}
      {...props}
    />
  );
}
