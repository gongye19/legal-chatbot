import React, { useState, useRef, useEffect } from 'react';
import './ChatBot.css';

const ChatBot = () => {
  const [messages, setMessages] = useState(() => {
    const savedMessages = localStorage.getItem('chatHistory');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResponse, setCurrentResponse] = useState('');
  const [dots, setDots] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, currentResponse, isLoading]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: "smooth",
        block: "end",
      });
    }
  };

  useEffect(() => {
    let interval;
    if (isLoading && !currentResponse) {
      interval = setInterval(() => {
        setDots(prev => {
          if (prev === '...') return '';
          return prev + '.';
        });
      }, 500);
    }
    return () => clearInterval(interval);
  }, [isLoading, currentResponse]);

  const simulateTyping = async (text) => {
    const words = text.split(' ');
    let currentText = '';
    
    for (const word of words) {
      currentText += word + ' ';
      setCurrentResponse(currentText.trim());
      await new Promise(resolve => setTimeout(resolve, Math.random() * 100 + 50));
    }
    setMessages(prev => [...prev, {
      text: text,
      sender: 'bot',
      isComplete: true
    }]);
    setCurrentResponse('');
  };

  const focusInput = () => {
    requestAnimationFrame(() => {
      inputRef.current?.focus();
    });
  };

  const handleClear = () => {
    setMessages([]);
    setCurrentResponse('');
    setInputMessage('');
    localStorage.removeItem('chatHistory');
    focusInput();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setCurrentResponse('');

    setTimeout(focusInput, 0);
    setTimeout(scrollToBottom, 100);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: inputMessage,
          history: messages.filter(msg => msg.isComplete !== false)
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      await simulateTyping(data.response);

    } catch (error) {
      console.error('Error:', error);
      const errorMessage = {
        text: `Error: ${error.message}`,
        sender: 'bot'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(focusInput, 0);
    }
  };

  useEffect(() => {
    focusInput();
  }, []);

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(messages));
  }, [messages]);

  return (
    <div className="chatbot-container" onClick={(e) => e.stopPropagation()}>
      <div className="chat-header">
        <h2>Legal Assistant</h2>
      </div>
      
      <div className="chat-messages">
        <div className="message bot">
          <div className="message-content">
            Hello! I'm your legal assistant. How can I help you today?
          </div>
        </div>
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            <div className="message-content">{message.text}</div>
          </div>
        ))}
        {currentResponse && (
          <div className="message bot">
            <div className="message-content">{currentResponse}</div>
          </div>
        )}
        {isLoading && !currentResponse && (
          <div className="message bot">
            <div className="message-content">Thinking{dots}</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-form">
        <button 
          type="button" 
          onClick={handleClear}
          className="clear-button"
          disabled={isLoading}
        >
          Clear
        </button>
        <textarea
          ref={inputRef}
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Type your legal question here..."
          className="chat-input"
          disabled={isLoading}
          rows="1"
        />
        <button 
          type="submit" 
          className="send-button"
          disabled={isLoading || !inputMessage.trim()}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatBot; 