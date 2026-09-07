import { useState } from "react";
import { machineArtCandidates } from "@/lib/machineArt";

type Props = {
  machineType?: string | null;
  alt: string;
  className?: string;
};

export function MachineArt({ machineType, alt, className = "" }: Props) {
  const { png, svg } = machineArtCandidates(machineType);
  const [src, setSrc] = useState(png);

  return (
    <img
      src={src}
      alt={alt}
      className={`machine-art ${className}`}
      onError={() => {
        if (src !== svg) setSrc(svg);
      }}
    />
  );
}
