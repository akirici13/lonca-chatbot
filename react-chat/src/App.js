import React, { useState, useRef } from 'react';
import './App.css';

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
  const fileInputRef = useRef();

  // Dummy assistant response for demo
  const getAssistantResponse = async (userMessage, imageData) => {
    // Replace this with your backend call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          role: 'assistant',
          content: userMessage + (imageData ? ' [image attached]' : ''),
        });
      }, 1000);
    });
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input && !image) return;
    let imageUrl = null;
    if (image) {
      imageUrl = URL.createObjectURL(image);
    }
    const userMsg = { role: 'user', content: input, image: imageUrl };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput('');
    setImage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    // Simulate assistant response
    const assistantMsg = await getAssistantResponse(input, imageUrl);
    setMessages((msgs) => [...msgs, assistantMsg]);
  };

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setImage(e.target.files[0]);
    }
  };

  return (
    <div className="chat-container">
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
