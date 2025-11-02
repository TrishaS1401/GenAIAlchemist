import { useState, useRef, useEffect } from "react";
import { Send, Bot, User as UserIcon, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Avatar, AvatarFallback } from "./ui/avatar";
import { FlightCard } from "./FlightCard";
import { HotelCard } from "./HotelCard";
import { BookingConfirmation } from "./BookingConfirmation";

export interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  data?: any; // For structured data like flight options, hotel details, etc.
  dataType?: 'flights' | 'hotels' | 'booking-confirmation';
}

// API Configuration - Uses VITE_API_URL from environment (set during build)
// Falls back to production backend URL if not set
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://genaialchemist-backend-315210470033.us-central1.run.app';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: "Hello! 👋 I'm your EaseMyTrip AI assistant. I can help you book flights, hotels, trains, buses, and plan your perfect trip. How can I assist you today?",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [userId] = useState<string>(() => {
    // Generate or retrieve a persistent user ID
    const stored = localStorage.getItem('user_id');
    if (stored) return stored;
    const newId = `user_${Date.now()}`;
    localStorage.setItem('user_id', newId);
    return newId;
  });
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    // Find the ScrollArea viewport element and scroll it, not the entire page
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-slot="scroll-area-viewport"]') as HTMLElement;
      if (viewport) {
        // Only auto-scroll if user is near the bottom (within 150px) or it's a new conversation
        const isNearBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight < 150;
        
        if (isNearBottom || messages.length <= 2) {
          // Use requestAnimationFrame for smoother scroll without page jumping
          requestAnimationFrame(() => {
            if (viewport) {
              viewport.scrollTop = viewport.scrollHeight;
            }
          });
        }
      }
    }
  };

  useEffect(() => {
    // Only scroll on new messages, not on every render
    if (messages.length > 1) {
      scrollToBottom();
    }
  }, [messages.length]);

  // Initialize session on component mount
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/getSession`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ user_id: userId })
        });

        if (response.ok) {
          const data = await response.json();
          setSessionId(data.session_id);
          console.log('Session initialized:', data.session_id);
        } else {
          console.error('Failed to initialize session:', response.statusText);
        }
      } catch (error) {
        console.error('Error initializing session:', error);
      }
    };

    if (!sessionId) {
      initializeSession();
    }
  }, [userId, sessionId]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !sessionId) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentInput,
          session_id: sessionId,
          user_id: userId
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: data.response || "I'm sorry, I didn't receive a response.",
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
      setIsLoading(false);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: `I'm sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the backend API is running on ${API_BASE_URL}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-gradient-to-b from-[#2196F3] to-[#1976D2] -mt-8 pt-8 pb-12">
      <div className="max-w-5xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-2xl overflow-hidden" style={{ height: '600px' }}>
          {/* Chat Header */}
          <div className="bg-[#2196F3] text-white p-4 flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
              <Bot className="w-6 h-6 text-[#2196F3]" />
            </div>
            <div>
              <h3 className="text-white">EaseMyTrip AI Assistant</h3>
              <p className="text-white/80 text-sm">Online • Ready to help</p>
            </div>
          </div>

          {/* Messages Area */}
          <ScrollArea className="h-[440px] p-4" ref={scrollAreaRef}>
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  <Avatar className="w-8 h-8 flex-shrink-0">
                    <AvatarFallback className={message.type === 'user' ? 'bg-gray-200' : 'bg-blue-100'}>
                      {message.type === 'user' ? (
                        <UserIcon className="w-5 h-5 text-gray-600" />
                      ) : (
                        <Bot className="w-5 h-5 text-[#2196F3]" />
                      )}
                    </AvatarFallback>
                  </Avatar>

                  <div className={`flex-1 ${message.type === 'user' ? 'flex justify-end' : ''}`}>
                    <div
                      className={`rounded-lg p-3 max-w-[80%] ${
                        message.type === 'user'
                          ? 'bg-[#2196F3] text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="whitespace-pre-wrap">{message.content}</p>
                      
                      {/* Render structured data */}
                      {message.dataType === 'flights' && message.data && (
                        <div className="mt-3 space-y-2">
                          {message.data.map((flight: any, index: number) => (
                            <FlightCard key={index} flight={flight} />
                          ))}
                        </div>
                      )}
                      
                      {message.dataType === 'hotels' && message.data && (
                        <div className="mt-3 space-y-2">
                          {message.data.map((hotel: any, index: number) => (
                            <HotelCard key={index} hotel={hotel} />
                          ))}
                        </div>
                      )}

                      {message.dataType === 'booking-confirmation' && message.data && (
                        <div className="mt-3">
                          <BookingConfirmation booking={message.data} />
                        </div>
                      )}
                    </div>
                    <p className={`text-xs text-gray-500 mt-1 ${message.type === 'user' ? 'text-right' : ''}`}>
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-3">
                  <Avatar className="w-8 h-8">
                    <AvatarFallback className="bg-blue-100">
                      <Bot className="w-5 h-5 text-[#2196F3]" />
                    </AvatarFallback>
                  </Avatar>
                  <div className="bg-gray-100 rounded-lg p-3">
                    <Loader2 className="w-5 h-5 animate-spin text-[#2196F3]" />
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="border-t p-4">
            <div className="flex gap-2">
              <Input
                placeholder="Type your travel request... (e.g., 'Book a flight from Delhi to Mumbai on Dec 25')"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="bg-[#FF6D00] hover:bg-[#F57C00] text-white"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-xs text-gray-500 mt-2">
              💡 Try: "I want to book a flight from Delhi to Mumbai" or "Find hotels in Goa"
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
