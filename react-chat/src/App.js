import React, { useState, useRef } from 'react';
import './App.css';

// Add this import for backend API helper
import { sendMessageToBackend } from './api';

function Message({ message }) {
  return (
    <div className={`message ${message.role}`}>
      <div className="bubble">
        {message.content}
        {message.image && (
          <img src={message.image} alt="attachment" className="chat-image" />
        )}
      </div>
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [image, setImage] = useState(null);
  const [pending, setPending] = useState(false);
  const [region, setRegion] = useState('Europe');
  const fileInputRef = useRef();
  const sessionIdRef = useRef(null);

  // Helper to convert image file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new window.FileReader();
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input && !image) return;
    setPending(true);
    let base64Image = null;
    if (image) {
      base64Image = await fileToBase64(image);
    }
    const session_id = sessionIdRef.current;
    try {
      const res = await sendMessageToBackend({
        message: input,
        image: base64Image,
        region,
        session_id,
      });
      if (!sessionIdRef.current) {
        sessionIdRef.current = res.session_id;
      }
      // For user/assistant images, show as data URLs if present
      const msgs = res.messages.map((msg) => {
        if (msg.image && !msg.image.startsWith('data:')) {
          return { ...msg, image: `data:image/*;base64,${msg.image}` };
        }
        return msg;
      });
      setMessages(msgs);
      setInput('');
      setImage(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setPending(res.pending);
      if (res.pending) {
        setTimeout(pollForResponse, 1000);
      }
    } catch (err) {
      setPending(false);
      alert('Error sending message.');
    }
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setImage(e.target.files[0]);
    }
  };

  const pollForResponse = async () => {
    const session_id = sessionIdRef.current;
    try {
      const res = await sendMessageToBackend({
        message: '', // No new message, just poll
        image: null,
        region,
        session_id,
      });
      const msgs = res.messages.map((msg) => {
        if (msg.image && !msg.image.startsWith('data:')) {
          return { ...msg, image: `data:image/*;base64,${msg.image}` };
        }
        return msg;
      });
      setMessages(msgs);
      setPending(res.pending);
      if (res.pending) {
        setTimeout(pollForResponse, 1000);
      }
    } catch (err) {
      setPending(false);
      alert('Error polling for response.');
    }
  };

  return (
    <div className="chat-container">
      <div style={{padding: '16px', borderBottom: '1px solid #eee', background: '#fff'}}>
        <label style={{marginRight: 8}}>Region:</label>
        <select value={region} onChange={e => setRegion(e.target.value)}>
          <option value="Europe">Europe</option>
          <option value="Turkey">Turkey</option>
          <option value="Other">Other</option>
          <option value="Own">Own</option>
        </select>
      </div>
      <div className="messages">
        {messages.map((msg, idx) => (
          <Message key={idx} message={msg} />
        ))}
      </div>
      <form className="input-area" onSubmit={handleSend}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          className="text-input"
        />
        <label className={`icon-btn attach-btn${image ? ' selected' : ''}`}>
          <input
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            ref={fileInputRef}
            className="file-input"
          />
          <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M21.44 11.05l-9.19 9.19a5 5 0 0 1-7.07-7.07l10.6-10.6a3 3 0 0 1 4.24 4.24l-10.6 10.6a1 1 0 0 1-1.42-1.42l9.19-9.19"/></svg>
        </label>
        <button type="submit" className="icon-btn send-btn" aria-label="Send">
          <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </form>
    </div>
  );
}

export default App;
