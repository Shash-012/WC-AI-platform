import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Build a /scout deep-link with a pre-filled question. */
export function askScoutLink(question: string) {
  return `/scout?q=${encodeURIComponent(question)}`;
}
