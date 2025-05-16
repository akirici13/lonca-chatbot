// Send a message to the FastAPI backend
export async function sendMessageToBackend({ message, image, region, session_id }) {
  const res = await fetch('http://localhost:8000/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, image, region, session_id }),
  });
  if (!res.ok) {
    throw new Error('Failed to send message');
  }
  return await res.json();
} 