interface BrandMarkProps {
  className?: string;
}

export default function BrandMark({
  className = "",
}: BrandMarkProps) {
  return (
    <svg
      className={`brand-mark ${className}`.trim()}
      viewBox="0 0 30 28"
      role="img"
      aria-label="MIND"
    >
      <path
        d="M4 23V12.5C4 9.25 6.4 7 9.5 7S15 9.25 15 12.5V23 12.5C15 9.25 17.4 7 20.5 7S26 9.25 26 12.5V23"
      />
    </svg>
  );
}
