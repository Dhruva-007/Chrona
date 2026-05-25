interface Props {
  title: string;
  value: string;
  subtitle: string;
}

export function StatusCard({
  title,
  value,
  subtitle,
}: Props) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-wide text-slate-500">
        {title}
      </p>

      <p className="mt-5 text-4xl font-semibold tracking-tight text-slate-900">
        {value}
      </p>

      <p className="mt-4 text-sm leading-relaxed text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}