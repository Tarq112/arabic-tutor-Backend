import React, { useState, useEffect } from 'react';

const ArabicTutorApp = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lessonTopic, setLessonTopic] = useState('greetings');
  const [conversationMode, setConversationMode] = useState('beginner');

  const lessonTopics = {
    greetings: { title: 'التحيات (Greetings)', emoji: '👋' },
    shopping: { title: 'التسوق (Shopping)', emoji: '🛒' },
    family: { title: 'العائلة (Family)', emoji: '👨‍👩‍👧‍👦' },
    food: { title: 'الطعام (Food)', emoji: '🍽️' },
    directions: { title: 'الاتجاهات (Directions)', emoji: '🗺️' },
    conversation: { title: 'محادثة حرة (Free Conversation)', emoji: '💬' }
  };

  const systemPrompts = {
    beginner: `You are Mohammed's Arabic language tutor specializing in Saudi dialect. The student is a beginner.

Your role:
- Teach practical, everyday Saudi Arabic phrases
- Use both Arabic script and transliteration (in parentheses)
- Keep responses simple and encouraging
- Correct mistakes gently and explain why
- Provide cultural context when relevant
- Focus on conversational fluency over perfect grammar

Current topic: ${lessonTopics[lessonTopic].title}

Start each conversation naturally, introduce 2-3 key phrases, then practice with the student.`,
    
    intermediate: `You are Mohammed's Arabic language tutor specializing in Saudi dialect. The student is intermediate level.

Your role:
- Have natural conversations in Saudi Arabic
- Mix Arabic and English explanations as needed
- Introduce idiomatic expressions and colloquialisms
- Correct mistakes and explain grammar patterns
- Challenge the student with follow-up questions
- Share cultural insights about Saudi Arabia

Current topic: ${lessonTopics[lessonTopic].title}`,
    
    advanced: `You are Mohammed's Arabic language tutor specializing in Saudi dialect. The student is advanced.

Your role:
- Conduct conversations primarily in Arabic
- Use sophisticated vocabulary and expressions
- Discuss nuanced cultural and social topics
- Provide detailed grammar explanations when asked
- Help refine pronunciation and fluency
- Introduce regional variations within Saudi dialects

Current topic: ${lessonTopics[lessonTopic].title}`
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': 'YOUR_API_KEY_HERE', // User needs to replace this
          'anthropic-version': '2023-06-01'
        },
        body: JSON.stringify({
          model: 'claude-sonnet-4-5-20250929',
          max_tokens: 1024,
          system: systemPrompts[conversationMode],
          messages: [...messages, userMessage].map(msg => ({
            role: msg.role,
            content: msg.content
          }))
        })
      });

      const data = await response.json();
      const assistantMessage = {
        role: 'assistant',
        content: data.content[0].text
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'عذراً، حدث خطأ (Sorry, an error occurred). Please check your API key and try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const startNewLesson = (topic) => {
    setLessonTopic(topic);
    setMessages([]);
  };

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <div style={{
      maxWidth: '1200px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif',
      direction: 'ltr'
    }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '30px',
        borderRadius: '15px',
        color: 'white',
        marginBottom: '30px',
        textAlign: 'center'
      }}>
        <h1 style={{ margin: '0 0 10px 0', fontSize: '2.5em' }}>🇸🇦 تعلم العربية</h1>
        <p style={{ margin: 0, fontSize: '1.2em', opacity: 0.9 }}>
          Learn Saudi Arabic with AI - Built by Mohammed
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '20px' }}>
        {/* Sidebar */}
        <div>
          {/* Level Selection */}
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '10px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            marginBottom: '20px'
          }}>
            <h3 style={{ marginTop: 0 }}>📊 Level</h3>
            {['beginner', 'intermediate', 'advanced'].map(level => (
              <button
                key={level}
                onClick={() => setConversationMode(level)}
                style={{
                  width: '100%',
                  padding: '12px',
                  margin: '5px 0',
                  border: conversationMode === level ? '2px solid #667eea' : '1px solid #ddd',
                  background: conversationMode === level ? '#f0f4ff' : 'white',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '1em',
                  textTransform: 'capitalize',
                  fontWeight: conversationMode === level ? 'bold' : 'normal'
                }}
              >
                {level}
              </button>
            ))}
          </div>

          {/* Lesson Topics */}
          <div style={{
            background: 'white',
            padding: '20px',
            borderRadius: '10px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ marginTop: 0 }}>📚 Lessons</h3>
            {Object.entries(lessonTopics).map(([key, topic]) => (
              <button
                key={key}
                onClick={() => startNewLesson(key)}
                style={{
                  width: '100%',
                  padding: '12px',
                  margin: '5px 0',
                  border: lessonTopic === key ? '2px solid #667eea' : '1px solid #ddd',
                  background: lessonTopic === key ? '#f0f4ff' : 'white',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontSize: '0.95em',
                  textAlign: 'left',
                  fontWeight: lessonTopic === key ? 'bold' : 'normal'
                }}
              >
                {topic.emoji} {topic.title}
              </button>
            ))}
          </div>
        </div>

        {/* Main Chat Area */}
        <div style={{
          background: 'white',
          borderRadius: '10px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column',
          height: '600px'
        }}>
          {/* Chat Header */}
          <div style={{
            padding: '20px',
            borderBottom: '1px solid #eee',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.5em' }}>
                {lessonTopics[lessonTopic].emoji} {lessonTopics[lessonTopic].title}
              </h2>
              <p style={{ margin: '5px 0 0 0', color: '#666', fontSize: '0.9em' }}>
                Level: {conversationMode}
              </p>
            </div>
            <button
              onClick={clearConversation}
              style={{
                padding: '10px 20px',
                background: '#f44336',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '0.9em'
              }}
            >
              🔄 Clear Chat
            </button>
          </div>

          {/* Messages */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: '20px'
          }}>
            {messages.length === 0 && (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: '#999'
              }}>
                <h3>مرحباً! (Welcome!)</h3>
                <p>Start a conversation to practice Arabic. Type "hello" or "مرحبا" to begin!</p>
                <p style={{ fontSize: '0.9em', marginTop: '20px' }}>
                  💡 Tip: The AI will teach you Saudi dialect phrases and correct your mistakes gently.
                </p>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  marginBottom: '15px',
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start'
                }}
              >
                <div style={{
                  maxWidth: '70%',
                  padding: '15px',
                  borderRadius: '15px',
                  background: msg.role === 'user' ? '#667eea' : '#f0f0f0',
                  color: msg.role === 'user' ? 'white' : 'black',
                  lineHeight: '1.6',
                  fontSize: '1.05em'
                }}>
                  {msg.content}
                </div>
              </div>
            ))}
            
            {loading && (
              <div style={{
                display: 'flex',
                justifyContent: 'flex-start',
                marginBottom: '15px'
              }}>
                <div style={{
                  padding: '15px',
                  borderRadius: '15px',
                  background: '#f0f0f0',
                  color: '#999'
                }}>
                  Typing...
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <div style={{
            padding: '20px',
            borderTop: '1px solid #eee'
          }}>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type your message in Arabic or English..."
                style={{
                  flex: 1,
                  padding: '15px',
                  border: '1px solid #ddd',
                  borderRadius: '10px',
                  fontSize: '1em',
                  outline: 'none'
                }}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !input.trim()}
                style={{
                  padding: '15px 30px',
                  background: loading || !input.trim() ? '#ccc' : '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '10px',
                  cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
                  fontSize: '1em',
                  fontWeight: 'bold'
                }}
              >
                Send
              </button>
            </div>
            <p style={{
              margin: '10px 0 0 0',
              fontSize: '0.85em',
              color: '#999',
              textAlign: 'center'
            }}>
              Press Enter to send • The AI tutor will respond in a mix of Arabic and English
            </p>
          </div>
        </div>
      </div>

      {/* Instructions Box */}
      <div style={{
        marginTop: '30px',
        padding: '20px',
        background: '#fff3cd',
        borderRadius: '10px',
        border: '1px solid #ffc107'
      }}>
        <h3 style={{ marginTop: 0 }}>⚠️ Setup Instructions</h3>
        <ol style={{ lineHeight: '1.8' }}>
          <li>Get your Claude API key from <a href="https://console.anthropic.com" target="_blank" rel="noopener">console.anthropic.com</a></li>
          <li>Replace <code>YOUR_API_KEY_HERE</code> in the code with your actual API key</li>
          <li>Save this file as an HTML file or use it in your React project</li>
          <li>Start chatting with your AI Arabic tutor!</li>
        </ol>
        <p style={{ margin: '10px 0 0 0', fontSize: '0.9em' }}>
          <strong>Note:</strong> API calls will cost approximately $0.003 per conversation message with Claude Sonnet 4.5
        </p>
      </div>
    </div>
  );
};

export default ArabicTutorApp;
