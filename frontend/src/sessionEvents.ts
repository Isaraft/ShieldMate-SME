// Cross-tab invalidation carries no identity, token or customer data and uses no Storage.
const eventName = 'shieldmate-session-changed';
let channel: BroadcastChannel | undefined;
function sessionChannel() {
  if (!channel && typeof window.BroadcastChannel === 'function') {
    channel = new window.BroadcastChannel('shieldmate-session');
    channel.addEventListener('message', () =>
      window.dispatchEvent(new Event(eventName)),
    );
  }
  return channel;
}
export function notifySessionChange() {
  window.dispatchEvent(new Event(eventName));
  sessionChannel()?.postMessage('changed');
}
export function onSessionChange(callback: () => void) {
  sessionChannel();
  window.addEventListener(eventName, callback);
  return () => window.removeEventListener(eventName, callback);
}
