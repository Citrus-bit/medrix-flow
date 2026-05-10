"use client";

import Image from "next/image";

import { cn } from "@/lib/utils";

export function AnaxaLogoMark({
  className,
  size = 28,
}: {
  className?: string;
  size?: number;
}) {
  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 overflow-hidden rounded-md bg-[#08071b]",
        className,
      )}
      style={{ width: size, height: size }}
    >
      <Image
        src="/images/anaxa-mark.jpg"
        alt="Anaxa logo"
        fill
        sizes={`${size}px`}
        className="object-cover"
      />
    </span>
  );
}
