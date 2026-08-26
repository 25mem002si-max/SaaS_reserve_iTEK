import clsx from "clsx";

export default function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("bg-white rounded-xl shadow p-4", className)}>
      {children}
    </div>
  );
}
