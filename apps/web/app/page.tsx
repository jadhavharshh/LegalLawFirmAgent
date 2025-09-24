"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Toggle } from "@/components/ui/toggle";
import { Send, Bot, User, MessageCircle, Mic, MicOff } from "lucide-react";

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
}

const VoiceOrb = ({ isListening, isSpeaking, onClick }: {
  isListening: boolean;
  isSpeaking: boolean;
  onClick: () => void;
}) => {
  return (
    <div className="flex flex-col items-center justify-center flex-1">
      <div
        className={`relative cursor-pointer transition-all duration-300 ${
          isListening ? 'scale-110' : isSpeaking ? 'scale-105' : 'hover:scale-105'
        }`}
        onClick={onClick}
      >
        {/* Outer pulse rings */}
        {isListening && (
          <>
            <div className="absolute inset-0 rounded-full bg-primary/30 animate-ping"></div>
            <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" style={{ animationDelay: '0.5s' }}></div>
          </>
        )}

        {/* Speaking waves */}
        {isSpeaking && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="absolute w-32 h-32 rounded-full border-2 border-primary/40 animate-pulse"></div>
            <div className="absolute w-40 h-40 rounded-full border-2 border-primary/20 animate-pulse" style={{ animationDelay: '0.3s' }}></div>
            <div className="absolute w-48 h-48 rounded-full border-2 border-primary/10 animate-pulse" style={{ animationDelay: '0.6s' }}></div>
          </div>
        )}

        {/* Main orb */}
        <div className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 ${
          isListening
            ? 'bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/50'
            : isSpeaking
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/50 animate-pulse'
            : 'bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/50'
        }`}>
          {isListening ? (
            <MicOff className="h-8 w-8 text-white" />
          ) : (
            <Mic className="h-8 w-8 text-white" />
          )}
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-lg font-medium text-foreground">
          {isListening
            ? 'Listening...'
            : isSpeaking
            ? 'Speaking...'
            : 'Tap to speak'}
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          {isListening
            ? 'Click again to stop'
            : isSpeaking
            ? 'Processing your request'
            : 'Ask me anything about legal matters'}
        </p>
      </div>
    </div>
  );
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content: "Hello! I'm your legal assistant. How can I help you today?",
      sender: "bot",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "I understand your question. Let me analyze this legal matter for you...",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleVoiceMode = () => {
    setIsVoiceMode(!isVoiceMode);
    if (isListening) {
      setIsListening(false);
    }
  };

  const startListening = () => {
    if (!isListening) {
      setIsListening(true);
      // Simulate listening for demo purposes
      setTimeout(() => {
        setIsListening(false);
        // Simulate processing the voice input
        handleVoiceInput("What are the requirements for a valid contract?");
      }, 3000);
    } else {
      setIsListening(false);
    }
  };

  const handleVoiceInput = async (voiceText: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: voiceText,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsSpeaking(true);

    setTimeout(() => {
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: "A valid contract requires offer, acceptance, consideration, and mutual consent. Let me explain each element in detail...",
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);

      // Simulate speaking animation
      setTimeout(() => {
        setIsSpeaking(false);
      }, 2000);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <Card className="flex-1 flex flex-col m-4 border-0 shadow-lg">
        <CardHeader className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
          <CardTitle className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <span>Legal Assistant</span>
            </div>
            <div className="flex items-center gap-3 ml-auto">
              <div className="flex items-center bg-secondary/50 rounded-lg p-1">
                <Toggle
                  pressed={!isVoiceMode}
                  onPressedChange={() => !isVoiceMode && toggleVoiceMode()}
                  className="data-[state=on]:bg-background data-[state=on]:text-foreground h-8 px-3"
                >
                  <MessageCircle className="h-4 w-4 mr-1" />
                  <span className="text-xs">Chat</span>
                </Toggle>
                <Toggle
                  pressed={isVoiceMode}
                  onPressedChange={() => isVoiceMode && toggleVoiceMode()}
                  className="data-[state=on]:bg-background data-[state=on]:text-foreground h-8 px-3"
                >
                  <Mic className="h-4 w-4 mr-1" />
                  <span className="text-xs">Voice</span>
                </Toggle>
              </div>
              <Badge variant="secondary">
                Online
              </Badge>
            </div>
          </CardTitle>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col p-0">
          {isVoiceMode ? (
            <div className="flex-1 flex flex-col">
              <VoiceOrb
                isListening={isListening}
                isSpeaking={isSpeaking}
                onClick={startListening}
              />

              {/* Recent conversation in voice mode */}
              {messages.length > 1 && (
                <div className="border-t bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm p-4 max-h-32 overflow-y-auto">
                  <div className="text-xs text-muted-foreground mb-2">Recent:</div>
                  <div className="text-sm space-y-1">
                    {messages.slice(-2).map((message) => (
                      <div key={message.id} className="flex gap-2">
                        <span className={`font-medium ${
                          message.sender === "user" ? "text-primary" : "text-muted-foreground"
                        }`}>
                          {message.sender === "user" ? "You:" : "Assistant:"}
                        </span>
                        <span className="truncate">{message.content}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <>
              <ScrollArea ref={scrollAreaRef} className="flex-1 p-4">
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex items-start gap-3 ${
                        message.sender === "user" ? "flex-row-reverse" : ""
                      }`}
                    >
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className={`text-xs ${
                          message.sender === "user"
                            ? "bg-primary text-primary-foreground"
                            : "bg-secondary"
                        }`}>
                          {message.sender === "user" ? (
                            <User className="h-4 w-4" />
                          ) : (
                            <Bot className="h-4 w-4" />
                          )}
                        </AvatarFallback>
                      </Avatar>

                      <div className={`flex flex-col ${
                        message.sender === "user" ? "items-end" : "items-start"
                      }`}>
                        <div
                          className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm ${
                            message.sender === "user"
                              ? "bg-primary text-primary-foreground ml-4"
                              : "bg-muted mr-4"
                          }`}
                        >
                          {message.content}
                        </div>
                        <span className="text-xs text-muted-foreground mt-1 px-1">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex items-start gap-3">
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-secondary">
                          <Bot className="h-4 w-4" />
                        </AvatarFallback>
                      </Avatar>
                      <div className="bg-muted max-w-[80%] px-4 py-3 rounded-2xl mr-4">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
                          <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              <div className="border-t bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm p-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Ask me anything about legal matters..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                    className="flex-1"
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || isLoading}
                    size="icon"
                    className="shrink-0"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
