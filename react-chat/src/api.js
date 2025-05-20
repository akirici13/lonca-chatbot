// Send a message to the FastAPI backend
const getApiUrl = () => {
  // Use the current hostname, but always port 8000
  const host = window.location.hostname;
  return `http://${host}:8000/message`;
};

export async function sendMessageToBackend({ message, image, audio_data, region, session_id }) {
  const res = await fetch(getApiUrl(), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, image, audio_data, region, session_id }),
  });
  if (!res.ok) {
    throw new Error('Failed to send message');
  }
  return await res.json();
} 