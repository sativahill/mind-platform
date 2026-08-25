interface BrainIconProps {
  className?: string;
}

export default function BrainIcon({
  className = "",
}: BrainIconProps) {
  return (
    <svg
      className={`brain-line-icon ${className}`.trim()}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path d="M12 5.6C10.9 3.7 8.2 3.2 6.7 5.1 4.4 5.2 3.2 7.5 4.3 9.3 2.8 10.5 2.9 12.9 4.5 14 3.9 16.2 5.5 18 7.6 18.1 8.3 20.2 10.7 20.6 12 18.5" />
      <path d="M12 5.6C13.1 3.7 15.8 3.2 17.3 5.1 19.6 5.2 20.8 7.5 19.7 9.3 21.2 10.5 21.1 12.9 19.5 14 20.1 16.2 18.5 18 16.4 18.1 15.7 20.2 13.3 20.6 12 18.5" />
      <path d="M12 5.6V18.5M7.1 8.2c1.8.1 2.8 1.1 2.9 2.6M16.9 8.2c-1.8.1-2.8 1.1-2.9 2.6M6.3 13c1.7-.4 3.1.2 3.8 1.6M17.7 13c-1.7-.4-3.1.2-3.8 1.6" />
    </svg>
  );
}
