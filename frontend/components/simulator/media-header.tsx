"use client";

import Image from "next/image";
import { Play, X } from "lucide-react";
import { useState } from "react";

interface MediaHeaderProps {
  mediaType: "none" | "image" | "video";
  mediaUrl?: string | null;
}

/** Image/video thumbnail with a lightweight, keyboard-dismissable lightbox. */
export function MediaHeader({
  mediaType,
  mediaUrl,
}: MediaHeaderProps): React.JSX.Element | null {
  const [isOpen, setIsOpen] = useState(false);
  if (!mediaUrl || mediaType === "none") return null;

  return (
    <>
      <button
        type="button"
        className="bg-sim-wallpaper relative mb-2 block aspect-video w-full overflow-hidden rounded focus-visible:outline-2 focus-visible:outline-offset-2"
        onClick={() => setIsOpen(true)}
        aria-label={`Open ${mediaType} attachment`}
      >
        <Image
          src={mediaUrl}
          alt="Message attachment"
          fill
          unoptimized
          className="object-cover"
        />
        {mediaType === "video" ? (
          <span className="bg-sim-text/65 text-sim-incoming absolute inset-0 flex items-center justify-center">
            <Play aria-hidden="true" className="size-10" fill="currentColor" />
            <span className="absolute right-2 bottom-1 text-[0.6rem]">
              0:24
            </span>
          </span>
        ) : null}
      </button>
      {isOpen ? (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Message attachment"
          className="bg-sim-text/90 fixed inset-0 z-[70] flex items-center justify-center p-6"
        >
          <button
            type="button"
            className="text-sim-incoming absolute top-4 right-4 p-2"
            onClick={() => setIsOpen(false)}
            aria-label="Close attachment"
            autoFocus
          >
            <X aria-hidden="true" />
          </button>
          {mediaType === "video" ? (
            <video
              src={mediaUrl}
              controls
              autoPlay
              className="max-h-full max-w-full"
            />
          ) : (
            <Image
              src={mediaUrl}
              alt="Message attachment"
              width={900}
              height={600}
              unoptimized
              className="max-h-full w-auto object-contain"
            />
          )}
        </div>
      ) : null}
    </>
  );
}
