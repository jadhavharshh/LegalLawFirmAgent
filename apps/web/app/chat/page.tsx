"use client";

import { useState, useRef, useEffect } from "react";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Toggle } from "@/components/ui/toggle";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Send, Bot, User, MessageCircle, Mic, MicOff, Upload, LogOut } from "lucide-react";

// TypeScript declarations for Speech APIs
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

interface Message {
  id: string;
  content: string;
  sender: "user" | "bot";
  timestamp: Date;
}

const VoiceOrb = ({ isListening, isSpeaking, onClick, onStop, speechSupported }: {
  isListening: boolean;
  isSpeaking: boolean;
  onClick: () => void;
  onStop?: () => void;
  speechSupported: boolean;
}) => {
  return (
    <div className="flex flex-col items-center justify-center flex-1">
      <div
        className={`relative cursor-pointer transition-all duration-300 ${
          isListening ? 'scale-110' : isSpeaking ? 'scale-105' : 'hover:scale-105'
        }`}
        onClick={isSpeaking && onStop ? onStop : onClick}
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
          !speechSupported
            ? 'bg-gradient-to-br from-gray-400 to-gray-500 shadow-lg shadow-gray-500/50 cursor-not-allowed'
            : isListening
            ? 'bg-gradient-to-br from-red-500 to-red-600 shadow-lg shadow-red-500/50'
            : isSpeaking
            ? 'bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/50 animate-pulse'
            : 'bg-gradient-to-br from-primary to-primary/80 shadow-lg shadow-primary/50'
        }`}>
          {!speechSupported ? (
            <MicOff className="h-8 w-8 text-white" />
          ) : isListening ? (
            <MicOff className="h-8 w-8 text-white" />
          ) : (
            <Mic className="h-8 w-8 text-white" />
          )}
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-lg font-medium text-foreground">
          {!speechSupported
            ? 'Speech not supported'
            : isListening
            ? 'Listening...'
            : isSpeaking
            ? 'Speaking...'
            : 'Tap to speak'}
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          {!speechSupported
            ? 'Please use a supported browser like Chrome or Safari'
            : isListening
            ? 'Click again to stop'
            : isSpeaking
            ? 'Click to stop speaking'
            : 'Ask me anything about legal matters'}
        </p>
      </div>
    </div>
  );
};

function HomePage() {
  const { user, logout } = useAuth();
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
  const [speechEnabled, setSpeechEnabled] = useState(false); // Simple speech toggle
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  useEffect(() => {
    // Initialize speech recognition and synthesis
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          setIsListening(true);
        };

        recognition.onresult = (event) => {
          const transcript = event.results?.[0]?.[0]?.transcript || '';
          setIsListening(false);
          handleVoiceInput(transcript);
        };

        recognition.onerror = (event: any) => {
          console.error('Speech recognition error:', event.error);
          setIsListening(false);
        };

        recognition.onend = () => {
          setIsListening(false);
        };

        setRecognition(recognition);
        setSpeechSupported(true);
      } else {
        console.warn('Speech recognition not supported in this browser');
        setSpeechSupported(false);
      }

      // Initialize speech synthesis voices
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices();
        setAvailableVoices(voices);

        // Check for previously stored voice preference
        let bestVoice = null;
        try {
          const storedVoiceName = localStorage.getItem('preferredVoice');
          if (storedVoiceName) {
            bestVoice = voices.find(voice => voice.name === storedVoiceName);
          }
        } catch (error) {
          console.warn('Could not retrieve voice preference:', error);
        }

        // If no stored preference or stored voice not found, select the best available voice
        if (!bestVoice) {
          const preferredVoices = voices.filter(voice =>
            voice.lang.startsWith('en') && (
              voice.name.toLowerCase().includes('neural') ||
              voice.name.toLowerCase().includes('enhanced') ||
              voice.name.toLowerCase().includes('premium') ||
              voice.name.toLowerCase().includes('natural') ||
              voice.name.toLowerCase().includes('samantha') ||
              voice.name.toLowerCase().includes('alex') ||
              voice.name.toLowerCase().includes('karen') ||
              voice.name.toLowerCase().includes('daniel') ||
              voice.name.toLowerCase().includes('sara') ||
              voice.name.toLowerCase().includes('google')
            )
          );

          const englishVoices = voices.filter(voice => voice.lang.startsWith('en'));
          bestVoice = preferredVoices[0] || englishVoices[0] || voices[0];
        }

        if (bestVoice) {
          setSelectedVoice(bestVoice);
          console.log(`🎤 Selected voice: ${bestVoice.name} (${bestVoice.lang})`);

          // Store the preferred voice in localStorage for consistency
          try {
            localStorage.setItem('preferredVoice', bestVoice.name);
          } catch (error) {
            console.warn('Could not save voice preference:', error);
          }
        }
      };

      // Load voices immediately if available
      loadVoices();

      // Also load voices when they become available (some browsers need this)
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  const sendMessageToAPI = async (message: string) => {
    console.log('🚀 Sending message to API:', message);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          sender: 'user'
        }),
        signal: AbortSignal.timeout(150000), // 2.5 minutes timeout
      });

      console.log('📡 API Response status:', response.status);

      if (!response.ok) {
        throw new Error(`API responded with status: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ API Response data:', data);
      return data.response;
    } catch (error) {
      console.error('❌ Error sending message:', error);
      return "I apologize, but I'm having trouble connecting to the server right now. Please try again later.";
    }
  };

  const speakText = (text: string) => {
    console.log('🎤 speakText called with:', text.substring(0, 50) + '...');
    console.log('🎤 Speech synthesis available:', 'speechSynthesis' in window);
    console.log('🎤 Selected voice:', selectedVoice?.name);

    if ('speechSynthesis' in window && text.trim()) {
      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      // Clean and prepare the text for better speech
      const cleanedText = text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold markdown
        .replace(/\*(.*?)\*/g, '$1') // Remove italic markdown
        .replace(/`(.*?)`/g, '$1') // Remove code markdown
        .replace(/#{1,6}\s+/g, '') // Remove markdown headers
        .replace(/\n{2,}/g, '. ') // Replace multiple newlines with period
        .replace(/\n/g, ' ') // Replace single newlines with space
        .replace(/\s{2,}/g, ' ') // Replace multiple spaces with single space
        .trim();

      if (!cleanedText) return;

      const utterance = new SpeechSynthesisUtterance(cleanedText);

      // Use the pre-selected voice or fallback
      if (selectedVoice) {
        utterance.voice = selectedVoice;
      }

      // Enhanced voice settings for professional, warm tone
      utterance.rate = 0.82; // Optimal rate for comprehension
      utterance.pitch = selectedVoice?.name.toLowerCase().includes('male') ? 0.8 : 0.95; // Adjust pitch based on voice
      utterance.volume = 0.85; // Comfortable volume level

      utterance.onstart = () => {
        setIsSpeaking(true);
        console.log(`🎤 Speaking with voice: ${selectedVoice?.name || 'System Default'}`);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        console.log('🎤 Speech completed');
      };

      utterance.onerror = (event) => {
        setIsSpeaking(false);
        console.error('🎤 Speech synthesis error:', event.error);

        // Try again with default voice if there's an error
        if (selectedVoice && event.error === 'voice-unavailable') {
          setTimeout(() => {
            const fallbackUtterance = new SpeechSynthesisUtterance(cleanedText);
            fallbackUtterance.rate = 0.82;
            fallbackUtterance.pitch = 0.9;
            fallbackUtterance.volume = 0.85;
            fallbackUtterance.onstart = () => setIsSpeaking(true);
            fallbackUtterance.onend = () => setIsSpeaking(false);
            fallbackUtterance.onerror = () => setIsSpeaking(false);
            window.speechSynthesis.speak(fallbackUtterance);
          }, 100);
        }
      };

      utterance.onpause = () => {
        console.log('🎤 Speech paused');
      };

      utterance.onresume = () => {
        console.log('🎤 Speech resumed');
      };

      // Handle boundary events for natural pacing
      utterance.onboundary = (event) => {
        if (event.name === 'sentence') {
          // Log progress for debugging
          console.log(`🎤 Sentence boundary at character ${event.charIndex}`);
        }
      };

      // Start speaking
      console.log('🎤 About to call speechSynthesis.speak()');
      window.speechSynthesis.speak(utterance);
      console.log('🎤 speechSynthesis.speak() called');
    } else {
      console.warn('🎤 Speech synthesis not available or empty text provided');
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    console.log('🎤 Starting handleSendMessage. isVoiceMode:', isVoiceMode);

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const messageText = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      const response = await sendMessageToAPI(messageText);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response,
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);

      // ALWAYS speak if speech is enabled - no matter what mode
      console.log('🎤 Speech enabled state:', speechEnabled, 'isVoiceMode:', isVoiceMode);
      if (speechEnabled) {
        console.log('🎤 SPEECH IS ENABLED - SPEAKING RESPONSE:', response.substring(0, 100) + '...');
        speakText(response);
      } else {
        console.log('🎤 Speech is disabled, not speaking');
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleVoiceMode = () => {
    console.log('🎤 Toggling voice mode. Current state:', isVoiceMode, '-> New state:', !isVoiceMode);
    setIsVoiceMode(!isVoiceMode);
    if (isListening) {
      setIsListening(false);
    }
  };

  const stopSpeaking = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      console.log('🎤 Speech stopped by user');
    }
  };

  // Add a test function to debug speech
  const testSpeech = () => {
    console.log('🎤 Testing speech synthesis...');

    // Try a simple direct test first
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance("Testing direct speech");
      utterance.volume = 1.0;
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      utterance.onstart = () => console.log('🎤 Direct test started');
      utterance.onend = () => console.log('🎤 Direct test ended');
      utterance.onerror = (e) => console.error('🎤 Direct test error:', e.error);

      window.speechSynthesis.speak(utterance);
    }

    // Also test our enhanced function
    setTimeout(() => {
      speakText("This is a test of the speech synthesis system. Can you hear me?");
    }, 2000);
  };

  const startListening = () => {
    if (!recognition || !speechSupported) {
      console.warn('Speech recognition not supported');
      return;
    }

    // Stop any ongoing speech first
    if (isSpeaking) {
      stopSpeaking();
    }

    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      try {
        recognition.start();
      } catch (error) {
        console.error('Error starting speech recognition:', error);
      }
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

    try {
      const response = await sendMessageToAPI(voiceText);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: response,
        sender: "bot",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);

      // ALWAYS speak if speech is enabled - no matter what mode
      console.log('🎤 Speech enabled state (voice input):', speechEnabled, 'isVoiceMode:', isVoiceMode);
      if (speechEnabled) {
        console.log('🎤 SPEECH IS ENABLED - SPEAKING RESPONSE (voice input):', response.substring(0, 100) + '...');
        speakText(response);
      } else {
        console.log('🎤 Speech is disabled, not speaking (voice input)');
      }
    } catch (error) {
      console.error('Error processing voice input:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setSelectedFiles(Array.from(files));
    }
  };

  const handleUploadDocuments = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);

    try {
      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append('files', file);
      });

      const response = await fetch('http://localhost:8000/upload-documents', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        console.log('Documents uploaded successfully:', selectedFiles.map(f => f.name));
        setSelectedFiles([]);
        setShowUploadDialog(false);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        console.error('Failed to upload documents');
      }
    } catch (error) {
      console.error('Error uploading documents:', error);
    } finally {
      setIsUploading(false);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
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
              <Button
                onClick={() => setShowUploadDialog(true)}
                variant="outline"
                size="sm"
                className="text-xs"
              >
                <Upload className="h-4 w-4 mr-1" />
                Upload Documents
              </Button>
              <div className="flex items-center bg-secondary/50 rounded-lg p-1">
                <Toggle
                  pressed={!isVoiceMode}
                  onPressedChange={() => isVoiceMode && toggleVoiceMode()}
                  className="data-[state=on]:bg-background data-[state=on]:text-foreground h-8 px-3"
                >
                  <MessageCircle className="h-4 w-4 mr-1" />
                  <span className="text-xs">Chat</span>
                </Toggle>
                <Toggle
                  pressed={isVoiceMode}
                  onPressedChange={() => !isVoiceMode && toggleVoiceMode()}
                  className="data-[state=on]:bg-background data-[state=on]:text-foreground h-8 px-3"
                >
                  <Mic className="h-4 w-4 mr-1" />
                  <span className="text-xs">Voice</span>
                </Toggle>
              </div>
              <Badge variant="secondary">
                Online
              </Badge>
              {/* Simple Speech Toggle */}
              <Button
                onClick={() => {
                  setSpeechEnabled(!speechEnabled);
                  console.log('🎤 Speech toggle clicked. New state:', !speechEnabled);
                }}
                variant={speechEnabled ? "default" : "outline"}
                size="sm"
                className="text-xs"
              >
                🔊 {speechEnabled ? 'ON' : 'OFF'}
              </Button>
              {/* User Info */}
              <div className="flex items-center gap-2 border-l pl-3 ml-3">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs bg-primary text-primary-foreground">
                    {user?.full_name?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium">{user?.full_name || user?.email}</span>
                <Button
                  onClick={logout}
                  variant="ghost"
                  size="sm"
                  className="text-xs"
                  title="Logout"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
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
                onStop={stopSpeaking}
                speechSupported={speechSupported}
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
                    onKeyDown={handleKeyDown}
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

      {/* Document Upload Dialog */}
      <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Upload Case Documents</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileSelect}
                className="hidden"
                id="file-upload"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant="outline"
                className="w-full"
              >
                <Upload className="h-4 w-4 mr-2" />
                Select Documents
              </Button>
            </div>

            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Selected files:</p>
                <div className="space-y-1">
                  {selectedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-secondary/50 p-2 rounded">
                      <span className="text-sm truncate">{file.name}</span>
                      <Button
                        onClick={() => removeFile(index)}
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0"
                      >
                        ×
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleUploadDocuments}
                disabled={selectedFiles.length === 0 || isUploading}
                className="flex-1"
              >
                {isUploading ? "Uploading..." : "Upload Documents"}
              </Button>
              <Button
                onClick={() => setShowUploadDialog(false)}
                variant="outline"
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function Home() {
  return (
    <ProtectedRoute>
      <HomePage />
    </ProtectedRoute>
  );
}
