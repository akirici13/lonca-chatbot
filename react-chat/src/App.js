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
        {/* Show a microphone icon if this is an audio message with no text/image */}
        {message.audio && !message.content && !message.image && (
          <span style={{ display: 'inline-block', verticalAlign: 'middle' }}>
            <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="22" x2="12" y2="16"/></svg>
          </span>
        )}
      </div>
    </div>
  );
}

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [image, setImage] = useState(null);
  const [audio, setAudio] = useState(null);
  const [pending, setPending] = useState(false);
  const [region, setRegion] = useState('Turkey');
  const fileInputRef = useRef();
  const audioInputRef = useRef();
  const sessionIdRef = useRef(null);

  // Helper to convert file to base64
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
    if (!input && !image && !audio) return;
    setPending(true);
    let base64Image = null;
    let base64Audio = null;
    if (image) {
      base64Image = await fileToBase64(image);
    }
    if (audio) {
      base64Audio = await fileToBase64(audio);
    }
    const session_id = sessionIdRef.current;
    try {
      const res = await sendMessageToBackend({
        message: input,
        image: base64Image,
        audio_data: base64Audio,
        region,
        session_id,
      });
      if (!sessionIdRef.current) {
        sessionIdRef.current = res.session_id;
      }
      const msgs = res.messages.map((msg) => {
        if (msg.image && !msg.image.startsWith('data:')) {
          return { ...msg, image: `data:image/*;base64,${msg.image}` };
        }
        return msg;
      });
      setMessages(msgs);
      setInput('');
      setImage(null);
      setAudio(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      if (audioInputRef.current) audioInputRef.current.value = '';
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
      setAudio(null);
      if (audioInputRef.current) audioInputRef.current.value = '';
    }
  };

  const handleAudioChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setAudio(e.target.files[0]);
      setImage(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
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
          <option value="Turkey">Turkey</option>
          <option value="Other">Other</option>
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
        <label className={`icon-btn attach-btn${image ? ' selected' : ''}`} title="Attach image">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageChange}
            ref={fileInputRef}
            className="file-input"
          />
          <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><path d="M21.44 11.05l-9.19 9.19a5 5 0 0 1-7.07-7.07l10.6-10.6a3 3 0 0 1 4.24 4.24l-10.6 10.6a1 1 0 0 1-1.42-1.42l9.19-9.19"/></svg>
        </label>
        <label className={`icon-btn attach-btn${audio ? ' selected' : ''}`} title="Attach audio" style={{marginLeft: 4}}>
          <input
            type="file"
            accept="audio/*"
            onChange={handleAudioChange}
            ref={audioInputRef}
            className="file-input"
          />
          <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="22" x2="12" y2="16"/></svg>
        </label>
        <button type="submit" className="icon-btn send-btn" aria-label="Send">
          <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </form>
    </div>
  );
}

export default App;
