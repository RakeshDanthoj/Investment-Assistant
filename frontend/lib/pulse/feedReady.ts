export const PULSE_FEED_READY_EVENT = "finnwise-pulse-feed-ready";

export function dispatchPulseFeedReady(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(PULSE_FEED_READY_EVENT));
}
