import clsx from "clsx";

export default function Badge({
  children,
  color = "primary",
}: {
  children: React.ReactNode;
  color?: "primary" | "success" | "danger" | "accent";
}) {
  return (
    <span
      className={clsx(
        "inline-block rounded-full px-2 py-0.5 text-xs font-medium",
        color === "primary" && "bg-primary/10 text-primary",
        color === "success" && "bg-success/10 text-success",
        color === "danger" && "bg-danger/10 text-danger",
        color === "accent" && "bg-accent/10 text-accent"
      )}
    >
      {children}
    </span>
  );
}
